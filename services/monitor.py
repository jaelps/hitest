import time
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Dict, Callable, Optional, Tuple
from services.logger import logger
from services.network import NetworkService

class DeviceMonitor:
    """
    Monitors a list of ESP8266 devices in the background.
    Uses ThreadPoolExecutor for concurrent ping requests.
    """
    def __init__(
        self,
        devices: Dict[str, str],
        on_status_change: Callable[[str, bool], None],
        on_cycle_complete: Callable[[int, int, str], None],
        check_interval: float = 10.0,
        max_workers: int = 20
    ):
        """
        Args:
            devices: Dict of {device_id: ip_address}
            on_status_change: Callback when a device's status changes (device_id, is_online)
            on_cycle_complete: Callback when a full verification cycle ends (online_cnt, offline_cnt, time_str)
            check_interval: Interval between checks in seconds.
            max_workers: Maximum parallel workers.
        """
        self.devices = devices
        self.on_status_change = on_status_change
        self.on_cycle_complete = on_cycle_complete
        self.check_interval = check_interval
        self.max_workers = max_workers
        
        # State tracker: {device_id: is_online}
        # Initial state is None to force an initial update callback
        self.status_state: Dict[str, Optional[bool]] = {dev_id: None for dev_id in devices}
        
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def update_devices(self, devices: Dict[str, str]):
        """Dynamically updates the device list to monitor."""
        with self._lock:
            self.devices = devices
            # Retain status of existing devices, initialize new ones to None
            new_state = {}
            for dev_id in devices:
                new_state[dev_id] = self.status_state.get(dev_id, None)
            self.status_state = new_state

    def start(self):
        """Starts the background monitoring thread."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, name="DeviceMonitorThread")
        self.thread.daemon = True
        self.thread.start()
        logger.info("Sistema de monitoramento iniciado")

    def stop(self):
        """Stops the monitoring thread."""
        self.running = False
        if self.thread:
            # We don't join blockingly inside UI, but we log the exit
            logger.info("Parando o monitoramento...")

    def _check_single_device(self, dev_id: str, ip: str) -> Tuple[str, bool]:
        """Pings a single device and returns its status."""
        is_online = NetworkService.ping_device(ip)
        return dev_id, is_online

    def force_check(self):
        """Triggers an immediate verification cycle out-of-band in a thread."""
        threading.Thread(target=self._run_verification_cycle, daemon=True).start()

    def _run_verification_cycle(self):
        """Executes one round of verification across all devices in parallel."""
        with self._lock:
            current_devices = list(self.devices.items())
            
        if not current_devices:
            # No devices, complete cycle immediately
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.on_cycle_complete(0, 0, timestamp)
            return

        online_count = 0
        offline_count = 0

        # Run checks in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [
                executor.submit(self._check_single_device, dev_id, ip)
                for dev_id, ip in current_devices
            ]
            
            for future in futures:
                try:
                    dev_id, is_online = future.result()
                    
                    # Update counts
                    if is_online:
                        online_count += 1
                    else:
                        offline_count += 1

                    old_status = self.status_state.get(dev_id)
                    
                    # Update status and check if changed
                    if old_status != is_online:
                        self.status_state[dev_id] = is_online
                        ip = self.devices.get(dev_id, "")
                        
                        # Log the state change
                        if is_online:
                            logger.info(f"Dispositivo {ip} online")
                        else:
                            logger.info(f"Dispositivo {ip} offline")
                            
                        # Call UI callback
                        self.on_status_change(dev_id, is_online)
                        
                except Exception as e:
                    # Count as offline if there was an error checking
                    offline_count += 1
                    logger.error(f"Erro ao verificar dispositivo: {str(e)}")

        timestamp = datetime.now().strftime("%H:%M:%S")
        self.on_cycle_complete(online_count, offline_count, timestamp)

    def _monitor_loop(self):
        """Background loop executing checks every 10 seconds."""
        # Initial check immediately
        self._run_verification_cycle()
        
        while self.running:
            # Sleep in tiny increments to respond quickly to shutdown requests
            for _ in range(int(self.check_interval * 10)):
                if not self.running:
                    break
                time.sleep(0.1)
                
            if self.running:
                self._run_verification_cycle()
