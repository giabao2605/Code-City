import unittest
from PySide6.QtCore import QUrl
from spike.security import allowed_navigation, allowed_request, asset_path, HOME


class SecurityPolicyTests(unittest.TestCase):
    def test_trusted_resources(self):
        for s in (HOME, "codecity-spike://app/assets/index-Ab12.js",
                  "codecity-spike://app/assets/index-A_b2.css",
                  "qrc:///qtwebchannel/qwebchannel.js"):
            self.assertTrue(allowed_request(QUrl(s)), s)

    def test_reject_untrusted_resources(self):
        for s in ("http://127.0.0.1:1111/", "https://example.com/",
                  "ws://127.0.0.1/socket", "wss://example.com/socket",
                  "file:///C:/private.txt", "data:text/plain,hello",
                  "codecity-spike://evil/index.html",
                  "codecity-spike://app/private.txt",
                  "codecity-spike://app/assets/../secret.js",
                  "codecity-spike://app/assets/payload.svg",
                  "qrc:///other/resource.js"):
            self.assertFalse(allowed_request(QUrl(s)), s)

    def test_navigation_only_root(self):
        self.assertTrue(allowed_navigation(QUrl(HOME), True))
        for s in ("https://example.com/", "file:///etc/passwd",
                  "codecity-spike://app/assets/index-A.js", "about:blank"):
            self.assertFalse(allowed_navigation(QUrl(s), True), s)
        self.assertFalse(allowed_navigation(QUrl(HOME), False))

    def test_asset_path_containment(self):
        for s in ("codecity-spike://app/assets/%2e%2e/secret.js",
                  "codecity-spike://app/index.html?x=1",
                  "codecity-spike://app/assets/%5csecret.js"):
            self.assertIsNone(asset_path(QUrl(s)))


if __name__ == "__main__":
    unittest.main()
