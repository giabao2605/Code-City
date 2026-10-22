"""Windows integration spike: trusted static Qt WebEngine, no HTTP server."""
import logging
import sys
from pathlib import Path
from .resources import frontend_dist

from PySide6.QtCore import QUrl
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox

from .bridge import DiagnosticBridge
from .security import Assets, HOME, LockedPage, OfflineInterceptor, register_scheme

LOG = logging.getLogger(__name__)
DIST = frontend_dist()


class SpikeWindow(QMainWindow):
    def __init__(self, dist=DIST):
        super().__init__()
        dist = Path(dist).resolve()
        if not (dist / "index.html").is_file():
            raise FileNotFoundError(f"Missing built frontend/index.html in {dist}. Run npm run build.")
        self.setWindowTitle("Code City | G0 WebEngine Packaging Spike")
        self.resize(850, 610)

        # QObject ownership order matters: delete view/page BEFORE the profile.
        self.view = QWebEngineView(self)
        # Unnamed profile is off-the-record. Keep handlers alive for entire page lifetime.
        self.profile = QWebEngineProfile(self)
        assert self.profile.isOffTheRecord(), "Production spike must not persist browsing data"
        self.interceptor = OfflineInterceptor(self)
        self.assets = Assets(dist, self)
        self.profile.setUrlRequestInterceptor(self.interceptor)
        self.profile.installUrlSchemeHandler(b"codecity-spike", self.assets)
        self.profile.downloadRequested.connect(self.reject_download)

        self.page = LockedPage(self.profile, self.view)
        self.page.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, False)
        self.page.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, False)
        self.page.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, False)
        self.page.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, False)
        self.view.setPage(self.page)
        self.setCentralWidget(self.view)

        self.bridge = DiagnosticBridge(self)
        self.channel = QWebChannel(self.page)
        self.channel.registerObject("spike", self.bridge)
        self.page.setWebChannel(self.channel)
        self.loaded = None
        self._last_denied_navigation = 0
        self.rejected_downloads = 0
        self.view.loadFinished.connect(self.on_loaded)
        self.view.loadStarted.connect(lambda: LOG.info("WebEngine navigation started"))
        self.view.setUrl(QUrl(HOME))

    def on_loaded(self, ok):
        if not ok and self.page.denied_navigation > self._last_denied_navigation:
            # Chromium may emit loadFinished(False) for a deliberately denied URL.
            # This is not a failure to load our original, trusted frontend.
            self._last_denied_navigation = self.page.denied_navigation
            LOG.info("Expected blocked navigation, preserved trusted frontend")
            return
        self.loaded = bool(ok)
        LOG.info("Trusted frontend loadFinished=%s", ok)
        if not ok:
            LOG.error("Qt WebEngine could not load trusted static frontend")
            # Non-modal to avoid freezing a headless CI test on load failures.
            self.error_dialog = QMessageBox(QMessageBox.Icon.Critical,
                                            "Code City spike load failed",
                                            "Trusted frontend load failed. Inspect the terminal log.",
                                            QMessageBox.StandardButton.Ok, self)
            self.error_dialog.open()

    def reject_download(self, item):
        self.rejected_downloads += 1
        LOG.warning("Denied WebEngine download")
        item.cancel()

    def closeEvent(self, event):
        self.view.stop()
        LOG.info("Qt spike window closing")
        super().closeEvent(event)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    try:
        if not (DIST / "index.html").is_file():
            raise FileNotFoundError("frontend/dist/index.html missing; run npm ci && npm run build in frontend")
        register_scheme()
        app = QApplication(sys.argv)
        window = SpikeWindow()
        window.show()
        return app.exec()
    except Exception:
        LOG.exception("Cannot launch CC-002 spike")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
