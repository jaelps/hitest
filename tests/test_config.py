import json
import tempfile
import unittest
from pathlib import Path

from services.config import normalize_config, load_config, save_config


class ConfigTests(unittest.TestCase):
    def test_normalize_config_converts_old_mapping(self):
        legacy = {"432": "192.168.50.101"}
        normalized = normalize_config(legacy)

        self.assertEqual(normalized["machine_modules"], [{"id": "432", "ip": "192.168.50.101"}])
        self.assertEqual(normalized["air_sensors"], [])
        self.assertEqual(normalized["online_dosers"], [])

    def test_load_and_save_config_round_trip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "devices.json"
            payload = {
                "machine_modules": [{"id": "432", "ip": "192.168.50.101"}],
                "air_sensors": [{"id": "AIR01", "ip": "192.168.50.201"}],
                "online_dosers": [{"id": "DOS01", "ip": "192.168.50.150"}],
            }
            save_config(config_path, payload)
            loaded = load_config(config_path)

        self.assertEqual(loaded, payload)


if __name__ == "__main__":
    unittest.main()
