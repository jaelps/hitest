import json
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_CONFIG: Dict[str, List[Dict[str, str]]] = {
    "machine_modules": [],
    "air_sensors": [],
    "online_dosers": [],
}


def normalize_config(config: Any) -> Dict[str, List[Dict[str, str]]]:
    """Normalizes the device configuration into the categorized structure used by the UI."""
    if not isinstance(config, dict):
        return {key: [] for key in DEFAULT_CONFIG}

    if any(key in config for key in DEFAULT_CONFIG):
        normalized: Dict[str, List[Dict[str, str]]] = {key: [] for key in DEFAULT_CONFIG}
        for category in DEFAULT_CONFIG:
            entries = config.get(category, [])
            if isinstance(entries, list):
                normalized[category] = [normalize_entry(entry, category) for entry in entries if isinstance(entry, dict)]
        return normalized

    legacy_devices = []
    for device_id, ip in config.items():
        if isinstance(device_id, str) and isinstance(ip, str):
            legacy_devices.append({"id": device_id, "ip": ip})

    return {
        "machine_modules": legacy_devices,
        "air_sensors": [],
        "online_dosers": [],
    }


def normalize_entry(entry: Dict[str, Any], category: str) -> Dict[str, str]:
    """Ensures a single device entry includes the expected minimum fields while preserving additional metadata."""
    device_id = str(entry.get("id", ""))
    ip_address = str(entry.get("ip", ""))
    normalized = {"id": device_id, "ip": ip_address}

    for key, value in entry.items():
        if key not in {"id", "ip"}:
            normalized[str(key)] = str(value)

    return normalized


def flatten_devices(config: Dict[str, List[Dict[str, str]]]) -> Dict[str, str]:
    """Builds a flat id -> ip mapping for the monitor service."""
    flattened: Dict[str, str] = {}
    for category in DEFAULT_CONFIG:
        for entry in config.get(category, []):
            device_id = entry.get("id")
            ip_address = entry.get("ip")
            if device_id and ip_address:
                flattened[str(device_id)] = str(ip_address)
    return flattened


def load_config(path: Any) -> Dict[str, List[Dict[str, str]]]:
    """Loads and normalizes the device configuration from disk."""
    config_path = Path(path)
    if not config_path.exists():
        save_config(config_path, DEFAULT_CONFIG)
        return DEFAULT_CONFIG

    with open(config_path, "r", encoding="utf-8") as handle:
        loaded = json.load(handle)
    return normalize_config(loaded)


def save_config(path: Any, config: Dict[str, List[Dict[str, str]]]) -> None:
    """Persists the device configuration to disk."""
    config_path = Path(path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    normalized = normalize_config(config)
    with open(config_path, "w", encoding="utf-8") as handle:
        json.dump(normalized, handle, indent=2)
