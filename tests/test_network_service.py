import unittest
from unittest.mock import patch

from services.network import NetworkService


class NetworkServiceTests(unittest.TestCase):
    def test_check_heartbeat_parses_json_payload(self):
        fake_response = b'{"status":"ok","uptime":123,"version":"1.2.3","device":"432"}'

        with patch("services.network.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value.__enter__.return_value.read.return_value = fake_response
            mock_urlopen.return_value.__enter__.return_value.status = 200

            result = NetworkService.check_heartbeat("192.168.0.10", timeout=2.0)

        self.assertTrue(result["success"])
        self.assertEqual(result["device_id"], "432")
        self.assertEqual(result["firmware_version"], "1.2.3")
        self.assertEqual(result["uptime"], 123)

    def test_send_command_reports_failure_on_http_error(self):
        with patch("services.network.request.urlopen", side_effect=Exception("boom")):
            success, detail = NetworkService.send_command("432", "192.168.0.10", timeout=2.0)

        self.assertFalse(success)
        self.assertIn("boom", detail)


if __name__ == "__main__":
    unittest.main()
