import os
import json
import customtkinter as ctk
from pathlib import Path
from typing import Dict
from services.logger import logger
from services.monitor import DeviceMonitor
from ui.main_window import HitestMainWindow

class HitestApp:
    """
    Main application controller class for HITEST.
    Orchestrates configuration, background processes, and UI updates.
    """
    def __init__(self):
        logger.info("Inicializando o sistema HITEST")
        
        # Define paths
        self.config_dir = Path("config")
        self.config_file = self.config_dir / "dispositivos.json"
        
        # Load configuration
        self.devices = self.load_config()
        
        # Set customtkinter default appearance
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        # Initialize UI Main Window
        self.window = HitestMainWindow(
            devices=self.devices,
            on_refresh_click=self.refresh_configuration
        )
        
        # Intercept window closure to stop threads gracefully
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Initialize and start monitoring service
        self.monitor = DeviceMonitor(
            devices=self.devices,
            on_status_change=self.window.on_device_status_change,
            on_cycle_complete=self.window.on_monitor_cycle_complete
        )
        self.monitor.start()

    def load_config(self) -> Dict[str, str]:
        """Loads devices mapping from configuration file or creates a default one."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        default_devices = {
            "432": "192.168.50.101",
            "543": "192.168.50.102",
            "654": "192.168.50.103",
            "765": "192.168.50.104",
            "876": "192.168.50.105",
            "987": "192.168.50.106",
            "321": "192.168.50.100",
            "310": "192.168.50.107"
        }
        
        if not self.config_file.exists():
            try:
                with open(self.config_file, "w", encoding="utf-8") as f:
                    json.dump(default_devices, f, indent=4)
                logger.info(f"Arquivo de configuracao padrao criado em {self.config_file}")
                return default_devices
            except Exception as e:
                logger.error(f"Erro ao criar arquivo de configuracao padrao: {str(e)}")
                return default_devices
        
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                devices = json.load(f)
                # Quick validation that we loaded a dictionary
                if isinstance(devices, dict):
                    logger.info(f"Configuracao de dispositivos carregada de {self.config_file}")
                    return devices
                else:
                    raise ValueError("Formato de JSON invalido, esperado dicionario.")
        except Exception as e:
            logger.error(f"Erro ao ler arquivo de configuracao: {str(e)}. Usando valores padrao.")
            return default_devices

    def refresh_configuration(self):
        """Reloads config from disk and updates monitor and UI dynamically."""
        logger.info("Recarregando configuracao de dispositivos...")
        devices = self.load_config()
        self.devices = devices
        
        # Update monitor
        self.monitor.update_devices(devices)
        
        # Rebuild UI table list
        self.window.rebuild_device_rows(devices)
        
        # Force immediate check for the new devices
        self.monitor.force_check()
        
        logger.info("Configuracao de dispositivos recarregada e atualizada com sucesso.")

    def run(self):
        """Starts the Tkinter main loop."""
        try:
            self.window.mainloop()
        except KeyboardInterrupt:
            self.on_closing()

    def on_closing(self):
        """Fires on window closing. Stop all threads and exit safely."""
        logger.info("Encerrando a aplicacao...")
        self.monitor.stop()
        self.window.destroy()
        logger.info("Aplicacao encerrada completamente.")

if __name__ == "__main__":
    app = HitestApp()
    app.run()
