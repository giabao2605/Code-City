"""Fail-closed resource and navigation policy for the CC-002 production spike."""
import logging
import re
from pathlib import Path

from PySide6.QtCore import QBuffer, QByteArray, QFile, QIODevice, QUrl
from PySide6.QtWebEngineCore import (
    QWebEnginePage, QWebEngineUrlRequestInterceptor, QWebEngineUrlRequestJob,
    QWebEngineUrlScheme, QWebEngineUrlSchemeHandler,
)

LOG = logging.getLogger(__name__)
SCHEME = b"codecity-spike"
HOME = "codecity-spike://app/index.html"
ASSET_PATH = re.compile(r"^/assets/[A-Za-z0-9_.-]+\.(?:js|css)$")
MIME = {".html": b"text/html; charset=utf-8", ".js": b"text/javascript; charset=utf-8",
        ".css": b"text/css; charset=utf-8"}


def register_scheme():
    """Must be called BEFORE QApplication is constructed."""
    scheme = QWebEngineUrlScheme(QByteArray(SCHEME))
    scheme.setSyntax(QWebEngineUrlScheme.Syntax.HostAndPort)
    scheme.setFlags(QWebEngineUrlScheme.Flag.SecureScheme |
                    QWebEngineUrlScheme.Flag.LocalScheme)
    QWebEngineUrlScheme.registerScheme(scheme)


def asset_path(url):
    """Return ONLY trusted Vite assets; never arbitrary filesystem paths."""
    if (url.scheme() != SCHEME.decode() or url.host() != "app" or
            url.port(-1) != -1 or url.userInfo() or
            url.hasQuery() or url.hasFragment()):
        return None
    path = url.path()
    return path if path in ("/index.html", "/qwebchannel.js") or ASSET_PATH.fullmatch(path) else None


def allowed_request(url):
    return bool(asset_path(url))


def allowed_navigation(url, is_main_frame):
    return is_main_frame and url.toString() == HOME


class Assets(QWebEngineUrlSchemeHandler):
    def __init__(self, dist, parent=None):
        super().__init__(parent)
        self.dist = Path(dist).resolve()

    def requestStarted(self, job):
        part = asset_path(job.requestUrl())
        if job.requestMethod() != QByteArray(b"GET") or part is None:
            job.fail(QWebEngineUrlRequestJob.Error.RequestDenied)
            return
        if part == "/qwebchannel.js":
            # Read Qt's OWN bundled resource and serve it at this application's origin.
            # Direct cross-scheme qrc script loads are not reliable from custom schemes.
            resource = QFile(":/qtwebchannel/qwebchannel.js")
            if not resource.open(QIODevice.OpenModeFlag.ReadOnly):
                LOG.error("Qt qwebchannel.js resource unavailable")
                job.fail(QWebEngineUrlRequestJob.Error.UrlNotFound)
                return
            data = bytes(resource.readAll())
            resource.close()
            mime = MIME[".js"]
        else:
            candidate = (self.dist / part.lstrip("/")).resolve()
            if not candidate.is_relative_to(self.dist) or not candidate.is_file():
                job.fail(QWebEngineUrlRequestJob.Error.UrlNotFound)
                return
            try:
                # Assets are application-owned build outputs, NEVER user-scanned source.
                data = candidate.read_bytes()
            except OSError:
                LOG.exception("Cannot read trusted asset")
                job.fail(QWebEngineUrlRequestJob.Error.RequestFailed)
                return
            mime = MIME[candidate.suffix]
        device = QBuffer(job)
        device.setData(QByteArray(data))
        device.open(QIODevice.OpenModeFlag.ReadOnly)
        job.reply(QByteArray(mime), device)


class OfflineInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.denied = 0

    def interceptRequest(self, info):
        if not allowed_request(info.requestUrl()):
            self.denied += 1
            # Never log URL query, payload, file content or local paths.
            LOG.warning("Denied WebEngine resource scheme: %s", info.requestUrl().scheme())
            info.block(True)


class LockedPage(QWebEnginePage):
    def __init__(self, profile, parent=None):
        super().__init__(profile, parent)
        self.denied_navigation = 0
        self.denied_popup = 0

    def acceptNavigationRequest(self, url, nav_type, is_main_frame):
        if allowed_navigation(url, is_main_frame):
            return True
        self.denied_navigation += 1
        LOG.warning("Denied WebEngine navigation scheme: %s", url.scheme())
        return False

    def createWindow(self, window_type):
        self.denied_popup += 1
        LOG.warning("Denied WebEngine popup")
        return None
