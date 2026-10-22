import json
import unittest

from spike.protocol import MAX_REQUEST_BYTES, handle_request


def call(**changes):
    msg = {"schemaVersion": 1, "requestId": "ping_01",
           "command": "diagnostics.ping", "payload": {"message": "hello"}}
    msg.update(changes)
    return json.loads(handle_request(json.dumps(msg)))


class ProtocolTests(unittest.TestCase):
    def test_ping(self):
        r = call()
        self.assertEqual(r["event"], "diagnostics.pong")
        self.assertEqual(r["requestId"], "ping_01")
        self.assertEqual(r["payload"]["message"], "hello")

    def test_invalid_schema(self):
        for version in (0, 2, "1", True, None):
            with self.subTest(version=version):
                self.assertEqual(call(schemaVersion=version)["payload"]["code"], "INVALID_SCHEMA")

    def test_unknown_command(self):
        self.assertEqual(call(command="os.execute")["payload"]["code"], "UNKNOWN_COMMAND")

    def test_bad_payload(self):
        for p in (None, [], "text", {}, {"message": 12}, {"message": "x"*129},
                  {"message": "é"*65}, {"message": "ok", "path": "C:/secret"}):
            with self.subTest(p=p):
                self.assertEqual(call(payload=p)["payload"]["code"], "INVALID_PAYLOAD")

    def test_bad_ids(self):
        for i in (None, 1, "", "bad space", "é", "x"*65):
            with self.subTest(i=i):
                self.assertEqual(call(requestId=i)["payload"]["code"], "INVALID_REQUEST_ID")

    def test_envelope_and_json(self):
        self.assertEqual(json.loads(handle_request("{"))["payload"]["code"], "INVALID_JSON")
        self.assertEqual(json.loads(handle_request("[]"))["payload"]["code"], "INVALID_ENVELOPE")
        self.assertEqual(json.loads(handle_request('{"schemaVersion":1}'))["payload"]["code"],
                         "INVALID_REQUEST_ID")
        self.assertEqual(call(extra="unexpected")["payload"]["code"], "INVALID_ENVELOPE")

    def test_request_size_bytes(self):
        large = '{"x":"' + "é" * MAX_REQUEST_BYTES + '"}'
        self.assertEqual(json.loads(handle_request(large))["payload"]["code"], "REQUEST_TOO_LARGE")
        self.assertEqual(json.loads(handle_request(None))["payload"]["code"], "REQUEST_TOO_LARGE")

    def test_many_requests_stay_isolated(self):
        for n in range(100):
            r = call(requestId=f"p{n}")
            self.assertEqual(r["requestId"], f"p{n}")


if __name__ == "__main__":
    unittest.main()
