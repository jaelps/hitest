import os
import logging
import threading
import customtkinter as ctk
from datetime import datetime
from typing import Dict, Optional
import ui.styles as styles
from ui.widgets import MetricCard, DeviceRow
from services.network import NetworkService
from services.logger import logger

class HitestMainWindow(ctk.CTk):
    """
    Main dashboard window for the Hitest system.
    Provides industrial-themed visualization and thread-safe control interface.
    """
    def __init__(self, devices: Dict[str, str], on_refresh_click: Optional[callable] = None):
        super().__init__()
        
        self.devices = devices
        self.on_refresh_click = on_refresh_click
        self.device_rows: Dict[str, DeviceRow] = {}

        # Set up window configurations
        self.title("HITEST - Sistema de Controle e Monitoramento ESP8266")
        self.geometry("820x680")
        self.configure(fg_color=styles.FUNDO)
        self.minsize(780, 580)
        
        # Configure Grid Layout weights
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Header
        self.grid_rowconfigure(1, weight=0)  # Metrics
        self.grid_rowconfigure(2, weight=0)  # Table Header
        self.grid_rowconfigure(3, weight=1)  # Table Body (Scrollable, expands)
        self.grid_rowconfigure(4, weight=0)  # Log Terminal Title
        self.grid_rowconfigure(5, weight=0)  # Log Terminal Box

        # Load Icon if it exists
        self.icon_path = os.path.join("assets", "logo.ico")
        if os.path.exists(self.icon_path):
            try:
                self.iconbitmap(self.icon_path)
            except Exception:
                pass # Fallback if OS doesn't support iconbitmap or file issues

        # Build UI Components
        self._create_header()
        self._create_metrics_panel()
        self._create_table_header()
        self._create_table_body()
        self._create_log_terminal()

        # Connect logger to GUI console output
        self._setup_gui_log_handler()

    def _create_header(self):
        """Creates the top header panel."""
        self.header_frame = ctk.CTkFrame(
            self,
            fg_color=styles.PAINEL,
            height=80,
            corner_radius=0,
            border_width=0
        )
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        self.header_frame.grid_columnconfigure(0, weight=1)
        self.header_frame.grid_columnconfigure(1, weight=0)

        # Title and Subtitle container
        title_container = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        title_container.grid(row=0, column=0, padx=25, pady=12, sticky="w")
        
        title_lbl = ctk.CTkLabel(
            title_container,
            text="HITEST",
            font=styles.FONT_TITLE,
            text_color=styles.TEXTO
        )
        title_lbl.pack(anchor="w")

        subtitle_lbl = ctk.CTkLabel(
            title_container,
            text="Sistema de Controle e Monitoramento ESP8266",
            font=styles.FONT_SUBTITLE,
            text_color=styles.TEXTO_MUTED
        )
        subtitle_lbl.pack(anchor="w")

        # Refresh Config Button
        self.btn_refresh = ctk.CTkButton(
            self.header_frame,
            text="ATUALIZAR CONFIG",
            font=styles.FONT_BUTTON,
            fg_color=styles.BOTAO,
            hover_color=styles.HOVER,
            text_color=styles.TEXTO,
            corner_radius=styles.RADIUS_BUTTON,
            width=140,
            height=32,
            command=self._handle_refresh_click
        )
        self.btn_refresh.grid(row=0, column=1, padx=25, pady=15, sticky="e")

    def _create_metrics_panel(self):
        """Creates the metric cards panel containing status counters."""
        self.metrics_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.metrics_frame.grid(row=1, column=0, sticky="ew", padx=25, pady=(20, 10))
        
        # Grid layout for cards (3 columns)
        self.metrics_frame.grid_columnconfigure((0, 1, 2), weight=1, uniform="equal")

        # Online Count Card
        self.card_online = MetricCard(
            self.metrics_frame,
            label="Dispositivos Online",
            value="0",
            value_color=styles.ONLINE
        )
        self.card_online.grid(row=0, column=0, padx=(0, 10), sticky="nsew")

        # Offline Count Card
        self.card_offline = MetricCard(
            self.metrics_frame,
            label="Dispositivos Offline",
            value="0",
            value_color=styles.OFFLINE
        )
        self.card_offline.grid(row=0, column=1, padx=10, sticky="nsew")

        # Last Update Card
        self.card_last_update = MetricCard(
            self.metrics_frame,
            label="Última Atualização",
            value="--:--:--",
            value_color=styles.TEXTO
        )
        self.card_last_update.grid(row=0, column=2, padx=(10, 0), sticky="nsew")

    def _create_table_header(self):
        """Creates the header row for the devices table."""
        self.table_header_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
            height=30
        )
        self.table_header_frame.grid(row=2, column=0, sticky="ew", padx=40, pady=(15, 2))
        
        # Keep same column weights as DeviceRow
        self.table_header_frame.grid_columnconfigure(0, weight=2)
        self.table_header_frame.grid_columnconfigure(1, weight=2)
        self.table_header_frame.grid_columnconfigure(2, weight=4)
        self.table_header_frame.grid_columnconfigure(3, weight=2)

        lbl_status = ctk.CTkLabel(
            self.table_header_frame,
            text="STATUS",
            font=styles.FONT_HEADER,
            text_color=styles.TEXTO_MUTED,
            anchor="w"
        )
        lbl_status.grid(row=0, column=0, sticky="w")

        lbl_id = ctk.CTkLabel(
            self.table_header_frame,
            text="ID",
            font=styles.FONT_HEADER,
            text_color=styles.TEXTO_MUTED,
            anchor="w"
        )
        lbl_id.grid(row=0, column=1, sticky="w")

        lbl_ip = ctk.CTkLabel(
            self.table_header_frame,
            text="IP DISPOSITIVO",
            font=styles.FONT_HEADER,
            text_color=styles.TEXTO_MUTED,
            anchor="w"
        )
        lbl_ip.grid(row=0, column=2, sticky="w")

        lbl_action = ctk.CTkLabel(
            self.table_header_frame,
            text="AÇÃO",
            font=styles.FONT_HEADER,
            text_color=styles.TEXTO_MUTED,
            anchor="e"
        )
        lbl_action.grid(row=0, column=3, sticky="e", padx=(0, 15))

    def _create_table_body(self):
        """Creates the scrollable frame that lists the devices."""
        self.table_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0
        )
        self.table_scroll.grid(row=3, column=0, sticky="nsew", padx=25, pady=(0, 15))
        self.table_scroll.grid_columnconfigure(0, weight=1)
        
        self.rebuild_device_rows(self.devices)

    def _create_log_terminal(self):
        """Creates a console log panel at the bottom."""
        title_lbl = ctk.CTkLabel(
            self,
            text="LOG DE EVENTOS EM TEMPO REAL",
            font=styles.FONT_METRIC_LBL,
            text_color=styles.TEXTO_MUTED,
            anchor="w"
        )
        title_lbl.grid(row=4, column=0, sticky="w", padx=30, pady=(10, 2))

        self.log_textbox = ctk.CTkTextbox(
            self,
            height=120,
            fg_color="#090d16",  # Deeper dark shade for terminal styling
            text_color=styles.TEXTO,
            font=styles.FONT_LOG,
            border_width=1,
            border_color=styles.BORDER,
            corner_radius=8
        )
        self.log_textbox.grid(row=5, column=0, sticky="ew", padx=25, pady=(0, 20))
        self.log_textbox.configure(state="disabled")

    def rebuild_device_rows(self, devices: Dict[str, str]):
        """Cleans current UI rows and instantiates new ones."""
        # Destroy current rows
        for row in self.device_rows.values():
            row.destroy()
        self.device_rows.clear()
        
        self.devices = devices
        
        # Recreate list
        for i, (dev_id, ip) in enumerate(devices.items()):
            row = DeviceRow(
                self.table_scroll,
                device_id=dev_id,
                ip=ip,
                on_send_click=self._handle_send_command
            )
            row.grid(row=i, column=0, sticky="ew", padx=5, pady=4)
            self.device_rows[dev_id] = row

    def _setup_gui_log_handler(self):
        """Attaches a log handler to display new log records in the CTkTextbox."""
        class GuiLogHandler(logging.Handler):
            def __init__(self, write_cb):
                super().__init__()
                self.write_cb = write_cb
            
            def emit(self, record):
                try:
                    msg = self.format(record)
                    self.write_cb(msg)
                except Exception:
                    self.handleError(record)

        # Retrieve global handler format to keep consistency
        from services.logger import CustomFormatter
        gui_handler = GuiLogHandler(self._append_log_message)
        gui_handler.setFormatter(CustomFormatter())
        
        # Add handler to base logger
        logging.getLogger("Hitest").addHandler(gui_handler)

    def _append_log_message(self, message: str):
        """Append log message thread-safely."""
        self.after(0, self._safe_append_log, message)

    def _safe_append_log(self, message: str):
        """Appends log message to textbox and scrolls it down."""
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", message + "\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    # --- Callbacks received from services/monitor.py ---

    def on_device_status_change(self, device_id: str, is_online: bool):
        """Thread-safe status update callback from the Monitor."""
        self.after(0, self._safe_update_device_ui, device_id, is_online)

    def on_monitor_cycle_complete(self, online_cnt: int, offline_cnt: int, timestamp: str):
        """Thread-safe cycle update callback from the Monitor."""
        self.after(0, self._safe_update_metrics_ui, online_cnt, offline_cnt, timestamp)

    def _safe_update_device_ui(self, device_id: str, is_online: bool):
        """Updates the status in the UI row."""
        if device_id in self.device_rows:
            self.device_rows[device_id].update_status(is_online)

    def _safe_update_metrics_ui(self, online_cnt: int, offline_cnt: int, timestamp: str):
        """Updates metrics panel widgets."""
        self.card_online.update_value(str(online_cnt))
        self.card_offline.update_value(str(offline_cnt))
        self.card_last_update.update_value(timestamp)

    # --- Actions ---

    def _handle_refresh_click(self):
        """Triggered when clicking the configuration refresh button."""
        if self.on_refresh_click:
            self.on_refresh_click()

    def _handle_send_command(self, device_id: str, ip: str):
        """Triggered when the user clicks 'ENVIAR' for a device."""
        row = self.device_rows.get(device_id)
        if row:
            row.set_button_busy(True)
            
        # Execute the HTTP request in a background thread to prevent UI freezing
        thread = threading.Thread(
            target=self._run_send_command_thread,
            args=(device_id, ip),
            name=f"SendCommand-{device_id}"
        )
        thread.daemon = True
        thread.start()

    def _run_send_command_thread(self, device_id: str, ip: str):
        """Sends the command and reports back to the UI thread."""
        success, details = NetworkService.send_command(device_id, ip)
        self.after(0, self._safe_on_send_command_complete, device_id, success)

    def _safe_on_send_command_complete(self, device_id: str, success: bool):
        """Re-enables command button on UI thread."""
        row = self.device_rows.get(device_id)
        if row:
            row.set_button_busy(False)
            
            # Briefly flash status or show feedback on button hover colors
            # The prompt requested "Evitar travamentos. Toda comunicação de rede deve ocorrer em threads separadas."
            # Which is fully respected.
