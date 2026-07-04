import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Callable, Dict, Optional, Tuple

from services.logger import logger
from services.network import NetworkService


class DeviceMonitor:
    """Background monitor that evaluates device health via HTTP heartbeat."""

    def __init__(
        self,
        devices: Dict[str, str],
        on_status_change: Callable[[str, bool, Dict[str, Any]], None],
        on_cycle_complete: Callable[[int, int, str], None],
        check_interval: float = 15.0,
        max_workers: int = 20,
    ):
        self.devices = devices
        self.on_status_change = on_status_change
        self.on_cycle_complete = on_cycle_complete
        self.check_interval = check_interval
        self.max_workers = max_workers

        self.status_state: Dict[str, Optional[bool]] = {dev_id: None for dev_id in devices}
        self.device_details: Dict[str, Dict[str, Any]] = {
            dev_id: {
                "firmware_version": "--",
                "uptime": "--",
                "device_id": dev_id,
                "last_communication": None,
                "last_command": None,
            }
            for dev_id in devices
        }

        self.running = False
        self.thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def update_devices(self, devices: Dict[str, str]):
        """Dynamically updates the device list to monitor."""
        with self._lock:
            self.devices = devices
            new_state = {}
            new_details = {}
            for dev_id in devices:
                new_state[dev_id] = self.status_state.get(dev_id, None)
                previous = self.device_details.get(dev_id, {})
                new_details[dev_id] = {
                    "firmware_version": previous.get("firmware_version", "--"),
                    "uptime": previous.get("uptime", "--"),
                    "device_id": previous.get("device_id", dev_id),
                    "last_communication": previous.get("last_communication"),
                    "last_command": previous.get("last_command"),
                }
            self.status_state = new_state
            self.device_details = new_details

    def start(self):
        """Starts the background monitoring thread."""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, name="DeviceMonitorThread")
        self.thread.daemon = True
        self.thread.start()
        logger.info("Sistema de monitoramento HTTP iniciado")

    def stop(self):
        """Stops the monitoring thread gracefully."""
        self.running = False
        if self.thread:
            logger.info("Parando o monitoramento HTTP...")

    def _build_details(self, dev_id: str, ip: str, is_online: bool, heartbeat: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Builds the metadata payload used by the UI and logging."""
        details = self.device_details.get(dev_id, {}).copy()
        details["ip_address"] = ip
        details["online"] = is_online
        if heartbeat and heartbeat.get("success"):
            details["firmware_version"] = heartbeat.get("firmware_version", "--")
            details["uptime"] = heartbeat.get("uptime", "--")
            details["device_id"] = heartbeat.get("device_id") or dev_id
            details["last_communication"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        return details

    def _check_single_device(self, dev_id: str, ip: str) -> Tuple[str, bool, Dict[str, Any]]:
        """Performs one lightweight heartbeat request for a single device."""
        heartbeat = NetworkService.check_heartbeat(ip)
        is_online = bool(heartbeat.get("success"))
        details = self._build_details(dev_id, ip, is_online, heartbeat)
        if is_online:
            self.device_details[dev_id] = details
        return dev_id, is_online, details

    def record_command_result(self, device_id: str, success: bool):
        """Updates device state after an operator command is executed."""
        with self._lock:
            ip = self.devices.get(device_id, "")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            details = self.device_details.get(device_id, {}).copy()
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            details["last_command"] = timestamp
            details["ip_address"] = ip
            details["online"] = success
            if success:
                details["last_communication"] = timestamp
                self.status_state[device_id] = True
                logger.info(f"Comando aceito e dispositivo {device_id} marcado como conectado")
            else:
                self.status_state[device_id] = False
                logger.warning(f"Comando falhou para {device_id}; dispositivo marcado como desconectado")

            self.device_details[device_id] = details
            self.on_status_change(device_id, success, details)

    def force_check(self):
        """Triggers an immediate verification cycle out-of-band in a thread."""
        threading.Thread(target=self._run_verification_cycle, daemon=True).start()

    def _run_verification_cycle(self):
        """Executes one round of verification across all devices in parallel."""
        with self._lock:
            current_devices = list(self.devices.items())

        if not current_devices:
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            self.on_cycle_complete(0, 0, timestamp)
            return

        online_count = 0
        offline_count = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [
                executor.submit(self._check_single_device, dev_id, ip)
                for dev_id, ip in current_devices
            ]

            for future in futures:
                try:
                    dev_id, is_online, details = future.result()
                    if is_online:
                        online_count += 1
                    else:
                        offline_count += 1

                    old_status = self.status_state.get(dev_id)
                    self.status_state[dev_id] = is_online
                    self.device_details[dev_id] = details

                    if old_status != is_online or details.get("last_communication") is None:
                        if is_online:
                            logger.info(f"Dispositivo {details.get('ip_address', dev_id)} conectado")
                        else:
                            logger.warning(f"Dispositivo {details.get('ip_address', dev_id)} desconectado")

                    self.on_status_change(dev_id, is_online, details)
                except Exception as exc:
                    offline_count += 1
                    logger.error(f"Erro ao verificar dispositivo: {exc}")

        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.on_cycle_complete(online_count, offline_count, timestamp)

    def _monitor_loop(self):
        """Background loop executing checks every 15 seconds by default."""
        self._run_verification_cycle()

        while self.running:
            for _ in range(int(self.check_interval * 10)):
                if not self.running:
                    break
                time.sleep(0.1)

            if self.running:
                self._run_verification_cycle()
