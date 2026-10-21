"""Real Qt WebEngine integration. Run after Vite build on Windows; no mocks."""
import json
import os
import time
import unittest

from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication
from spike.app import SpikeWindow
from spike.security import HOME, register_scheme


def spin(predicate, timeout=20):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        QApplication.processEvents()
        if predicate():
            return True
        time.sleep(0.025)
    return bool(predicate())


class WebEngineIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        register_scheme()
        cls.app = QApplication.instance() or QApplication([])
        cls.window = SpikeWindow()
        cls.window.show()
        if not spin(lambda: cls.window.loaded is not None, 30):
            raise AssertionError("Qt WebEngine never reported loadFinished")
        if not cls.window.loaded:
            raise AssertionError("Real Qt WebEngine failed to load built Vite assets")

    @classmethod
    def tearDownClass(cls):
        cls.window.close()
        spin(lambda: not cls.window.isVisible(), 4)
        cls.window.deleteLater()
        # processEvents() alone does not guarantee DeferredDelete events are sent.
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QApplication.processEvents()

    def js(self, source, timeout=10):
        result = {"done": False, "value": None}
        self.window.page.runJavaScript(source, lambda value: result.update(done=True, value=value))
        self.assertTrue(spin(lambda: result["done"], timeout), "JavaScript callback timeout")
        return result["value"]

    def wait_js(self, expression, check=lambda v: bool(v), timeout=20):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            value = self.js(expression)
            if check(value):
                return value
            time.sleep(0.1)
        self.fail(f"JavaScript condition timed out: {expression}")

    def test_01_react_mount_bridge_event_and_ping(self):
        self.wait_js("document.querySelector('[data-testid=frontend]')?.textContent",
                     lambda s: s == "mounted")
        self.wait_js("document.querySelector('[data-testid=bridge]')?.textContent",
                     lambda s: s == "connected to Qt WebChannel")
        self.wait_js("document.querySelector('[data-testid=events]')?.textContent",
                     lambda s: "app.ready" in (s or ""))
        self.js("document.querySelector('[data-testid=ping]').click()")
        self.wait_js("document.querySelector('[data-testid=successes]')?.textContent",
                     lambda s: s == "1")
        self.assertIn("hello from React", self.js(
            "document.querySelector('[data-testid=pong]')?.textContent"))
        self.assertEqual(self.js("document.querySelector('[data-testid=failures]')?.textContent"), "0")

    def test_02_ipc_rejects_invalid_requests_in_real_webchannel(self):
        cases = [
            ({"schemaVersion": 2}, "INVALID_SCHEMA"),
            ({"command": "os.execute"}, "UNKNOWN_COMMAND"),
            ({"payload": {"message": 23}}, "INVALID_PAYLOAD"),
            ({"requestId": ""}, "INVALID_REQUEST_ID"),
            ({"payload": {"message": "é" * 4000}}, "REQUEST_TOO_LARGE"),
        ]
        base = {"schemaVersion": 1, "requestId": "negative1",
                "command": "diagnostics.ping", "payload": {"message": "valid"}}
        for index, (fields, expected) in enumerate(cases):
            payload = dict(base, **fields)
            raw = json.dumps(payload)
            self.js("window.__ccNegative = null; window.__ccBridge.request("
                    + json.dumps(raw) + ", r => window.__ccNegative = r)")
            result = self.wait_js("window.__ccNegative", lambda s: isinstance(s, str))
            parsed = json.loads(result)
            self.assertEqual(parsed["payload"]["code"], expected, f"case {index}")

    def test_03_csp_blocks_http_https_websockets_and_file_fetch(self):
        # Controlled loopback: no outbound internet requests are needed.
        probes = [
            "http://127.0.0.1:49401/no-network",
            "https://127.0.0.1:49401/no-network",
            "file:///C:/Windows/win.ini",
        ]
        for index, url in enumerate(probes):
            key = f"__ccFetch{index}"
            self.js(f"window.{key}='pending'; fetch({json.dumps(url)})"
                    f".then(()=>window.{key}='ALLOWED',()=>window.{key}='blocked')")
            self.wait_js(f"window.{key}", lambda s: s != "pending")
            self.assertEqual(self.js(f"window.{key}"), "blocked")
        for index, scheme in enumerate(("ws", "wss")):
            key = f"__ccSocket{index}"
            self.js(f"window.{key}='pending';"
                    f"try {{ const socket=new WebSocket('{scheme}://127.0.0.1:49401/ws');"
                    f"socket.onopen=()=>window.{key}='ALLOWED';"
                    f"socket.onerror=()=>window.{key}='blocked';"
                    f"}} catch(e) {{ window.{key}='blocked'; }}")
            self.wait_js(f"window.{key}", lambda s: s != "pending")
            self.assertEqual(self.js(f"window.{key}"), "blocked")

    def test_04_navigation_popup_and_local_file_are_denied(self):
        self.js("window.location.href='https://example.invalid/outside'; 'attempted'")
        self.assertTrue(spin(lambda: self.window.page.url().toString() == HOME, 3))
        self.assertEqual(self.window.page.url().toString(), HOME)
        self.js("window.location.href='file:///C:/Windows/win.ini'; 'attempted'")
        self.assertEqual(self.window.page.url().toString(), HOME)
        result = self.js("window.open('https://example.invalid/popup','_blank') === null")
        self.assertTrue(result)

    def test_05_reload_and_reconnect(self):
        previous_seq = self.window.bridge.sequence
        self.window.loaded = None
        self.window.view.reload()
        self.assertTrue(spin(lambda: self.window.loaded is True, 30))
        self.wait_js("document.querySelector('[data-testid=bridge]')?.textContent",
                     lambda s: s == "connected to Qt WebChannel")
        self.assertTrue(spin(lambda: self.window.bridge.sequence > previous_seq, 10))
        self.js("document.querySelector('[data-testid=ping]').click()")
        self.wait_js("document.querySelector('[data-testid=successes]')?.textContent",
                     lambda s: s == "1")


if __name__ == "__main__":
    unittest.main()
