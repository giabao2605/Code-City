"""Self-contained REAL packaged Windows Qt WebEngine smoke, without source checkout.

All checks run through the frozen Python/QWebChannel/Chromium runtime, not mocks.
The --smoke-test flag adds no frontend privileges and never needs a dev server.
"""
import json
import logging
import socket
import sys
import threading
import time
from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWidgets import QApplication
from .app import SpikeWindow
from .security import HOME, register_scheme

LOG = logging.getLogger("cc003.smoke")


def wait(predicate, seconds=25, description="condition"):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        QApplication.processEvents()
        if predicate():
            return
        time.sleep(0.025)
    raise AssertionError(f"Timeout: {description}")


def javascript(window, source, seconds=12):
    result = []
    window.page.runJavaScript(source, lambda value: result.append(value))
    wait(lambda: bool(result), seconds, "JS callback: " + source[:90])
    return result[0]


def until_js(window, source, expected, seconds=20):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        value = javascript(window, source)
        if expected(value):
            return value
        time.sleep(0.09)
    raise AssertionError("Expected JS state never reached: " + source)


def check(value, label):
    if not value:
        raise AssertionError(label)
    LOG.info("PASS %s", label)


def network_negative(window):
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen(5)
    listener.settimeout(0.1)
    port = listener.getsockname()[1]
    stop = threading.Event()
    accepted = []

    def receive():
        while not stop.is_set():
            try:
                client, _ = listener.accept()
                accepted.append(True)
                client.close()
            except socket.timeout:
                continue
            except OSError:
                return

    thread = threading.Thread(target=receive, daemon=True)
    thread.start()
    try:
        urls = [f"http://127.0.0.1:{port}/blocked",
                f"https://127.0.0.1:{port}/blocked",
                "file:///C:/Windows/win.ini"]
        for i, url in enumerate(urls):
            key = "__ccNegativeFetch" + str(i)
            javascript(window, "window." + key + "='pending';fetch(" +
                       json.dumps(url) + ").then(()=>window." + key +
                       "='ALLOWED',()=>window." + key + "='blocked')")
            until_js(window, "window." + key, lambda v: v != "pending")
            check(javascript(window, "window." + key) == "blocked", "denied fetch " + str(i))
        for i, scheme in enumerate(("ws", "wss")):
            key = "__ccNegativeSocket" + str(i)
            javascript(window, "window." + key + "='pending';try{const w=new WebSocket(" +
                       json.dumps(f"{scheme}://127.0.0.1:{port}/") +
                       ");w.onopen=()=>window." + key +
                       "='ALLOWED';w.onerror=()=>window." + key +
                       "='blocked';}catch(e){window." + key + "='blocked';}")
            until_js(window, "window." + key, lambda v: v != "pending")
            check(javascript(window, "window." + key) == "blocked", "denied socket " + scheme)
        time.sleep(0.2)
        check(not accepted, "zero intercepted loopback TCP connections")
    finally:
        stop.set()
        listener.close()
        thread.join(timeout=2)


def run_checks(window):
    wait(lambda: window.loaded is not None, 35, "trusted frontend loadFinished")
    check(window.loaded is True, "packaged WebEngine loaded application origin")
    until_js(window, "document.querySelector('[data-testid=frontend]')?.textContent",
             lambda v: v == "mounted")
    check(True, "packaged React mounted")
    until_js(window, "document.querySelector('[data-testid=bridge]')?.textContent",
             lambda v: v == "connected to Qt WebChannel")
    check(True, "packaged WebChannel connected")
    until_js(window, "document.querySelector('[data-testid=events]')?.textContent",
             lambda v: "app.ready" in (v or ""))
    check(True, "unsolicited Python app.ready observed")
    for n in range(1, 4):
        javascript(window, "document.querySelector('[data-testid=ping]').click()")
        until_js(window, "document.querySelector('[data-testid=successes]')?.textContent",
                 lambda v: v == str(n))
        request_id = javascript(window, "document.querySelector('[data-testid=request-id]')?.textContent")
        pong = javascript(window, "document.querySelector('[data-testid=pong]')?.textContent")
        check(bool(request_id) and request_id in (pong or ""), f"Ping/Pong {n} requestId match")
    check(javascript(window, "document.querySelector('[data-testid=failures]')?.textContent") == "0",
          "zero response failures")

    raw = json.dumps({"schemaVersion": 1, "requestId": "invalid1",
                      "command": "os.execute", "payload": {"message": "ignored"}})
    javascript(window, "window.__ccInvalidReply=null;window.__ccBridge.request(" +
               json.dumps(raw) + ",r=>window.__ccInvalidReply=r)")
    denial = until_js(window, "window.__ccInvalidReply", lambda v: isinstance(v, str))
    check(json.loads(denial)["payload"]["code"] == "UNKNOWN_COMMAND",
          "packaged IPC rejects unauthorized command")
    network_negative(window)
    javascript(window, "window.location.href='https://example.invalid/escape';'attempted'")
    wait(lambda: window.page.url().toString() == HOME, 3, "blocked external navigation")
    check(javascript(window, "window.open('https://example.invalid','_blank')===null") is True,
          "packaged popup denied")
    before = window.rejected_downloads
    window.page.triggerAction(QWebEnginePage.WebAction.SavePage)
    wait(lambda: window.rejected_downloads > before, 9, "packaged download cancellation")
    check(True, "packaged download denied")

    previous = window.bridge.sequence
    window.loaded = None
    window.view.reload()
    wait(lambda: window.loaded is True, 35, "reload")
    until_js(window, "document.querySelector('[data-testid=bridge]')?.textContent",
             lambda v: v == "connected to Qt WebChannel")
    wait(lambda: window.bridge.sequence > previous, 12, "new Python event")
    javascript(window, "document.querySelector('[data-testid=ping]').click()")
    until_js(window, "document.querySelector('[data-testid=successes]')?.textContent",
             lambda v: v == "1")
    check(True, "reload/reconnect/re-Ping")


def smoke():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    window = None
    try:
        register_scheme()
        app = QApplication([])
        window = SpikeWindow()
        window.show()
        run_checks(window)
        LOG.info("CC003_PACKAGED_SMOKE=PASS")
        return 0
    except Exception:
        LOG.exception("CC003_PACKAGED_SMOKE=FAIL")
        return 1
    finally:
        if window is not None:
            window.close()
            window.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            QApplication.processEvents()
