from pathlib import Path
from typing import Dict, List

import customtkinter as ctk

from services.config import DEFAULT_CONFIG, flatten_devices, load_config, save_config
from services.logger import logger
from services.monitor import DeviceMonitor
from ui.main_window import HitestMainWindow


class HitestApp:
    """Main application controller for HITEST."""

    def __init__(self):
        logger.info("Inicializando o sistema HITEST")

        self.config_dir = Path("config")
        self.config_file = self.config_dir / "dispositivos.json"

        self.config = load_config(self.config_file)
        self.devices = flatten_devices(self.config)

        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.window = HitestMainWindow(
            config=self.config,
            on_refresh_click=self.refresh_configuration,
            on_command_result=self._handle_command_result,
            on_settings_save=self._handle_settings_save,
            on_monitoring_interval_changed=self._handle_monitoring_interval_change,
            on_theme_changed=self._handle_theme_change,
        )
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.monitor = DeviceMonitor(
            devices=self.devices,
            on_status_change=self.window.on_device_status_change,
            on_cycle_complete=self.window.on_monitor_cycle_complete,
        )
        self.monitor.start()

    def _handle_command_result(self, device_id: str, success: bool):
        """Propagates command execution feedback to the monitor state."""
        self.monitor.record_command_result(device_id, success)

    def _handle_settings_save(self, config: Dict[str, List[Dict[str, str]]]):
        """Persists updated configuration and refreshes the UI and monitor."""
        self.config = config
        save_config(self.config_file, config)
        self.devices = flatten_devices(config)
        self.monitor.update_devices(self.devices)
        self.window.apply_config(config)
        self.monitor.force_check()
        logger.info("Configuracao atualizada via configuracoes")

    def _handle_monitoring_interval_change(self, interval: int):
        """Updates the heartbeat monitoring interval while preserving the UI responsiveness."""
        self.monitor.check_interval = float(interval)
        logger.info(f"Intervalo de monitoramento atualizado para {interval}s")

    def _handle_theme_change(self, theme: str):
        """Applies the selected appearance mode."""
        ctk.set_appearance_mode(theme)

    def refresh_configuration(self):
        """Reloads config from disk and updates monitor and UI dynamically."""
        logger.info("Recarregando configuracao de dispositivos...")
        self.config = load_config(self.config_file)
        self.devices = flatten_devices(self.config)
        self.monitor.update_devices(self.devices)
        self.window.apply_config(self.config)
        self.monitor.force_check()
        logger.info("Configuracao de dispositivos recarregada e atualizada com sucesso.")

    def run(self):
        """Starts the Tkinter main loop."""
        try:
            self.window.mainloop()
        except KeyboardInterrupt:
            self.on_closing()

    def on_closing(self):
        """Fires on window closing. Stops all threads and exits safely."""
        logger.info("Encerrando a aplicacao...")
        self.monitor.stop()
        self.window.destroy()
        logger.info("Aplicacao encerrada completamente.")


if __name__ == "__main__":
    app = HitestApp()
    app.run()
