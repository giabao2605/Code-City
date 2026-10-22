"""Only diagnostic ping and a host-initiated event cross this Qt bridge."""
from PySide6.QtCore import QObject, QTimer, Signal, Slot
from .protocol import encode, handle_request


class DiagnosticBridge(QObject):
    pushed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.sequence = 0

    @Slot(str, result=str)
    def request(self, raw):
        return handle_request(raw)

    @Slot()
    def clientReady(self):
        # Signal is independent of any request callback; send after JS subscribes.
        QTimer.singleShot(0, self.push_ready)

    def push_ready(self):
        self.sequence += 1
        self.pushed.emit(encode({
            "schemaVersion": 1,
            "event": "app.ready",
            "payload": {"sequence": self.sequence, "origin": "python"},
        }))
