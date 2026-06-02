import customtkinter as ctk
from typing import Callable, Optional
import ui.styles as styles

class MetricCard(ctk.CTkFrame):
    """A card showing a single metric with a label and large value."""
    def __init__(
        self,
        parent,
        label: str,
        value: str,
        value_color: str = styles.TEXTO,
        **kwargs
    ):
        super().__init__(
            parent,
            fg_color=styles.PAINEL,
            corner_radius=styles.RADIUS_PANEL,
            border_width=1,
            border_color=styles.BORDER,
            **kwargs
        )
        
        # Configure layout (grid)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((0, 1), weight=1)
        
        # Label
        self.lbl_widget = ctk.CTkLabel(
            self,
            text=label.upper(),
            font=styles.FONT_METRIC_LBL,
            text_color=styles.TEXTO_MUTED
        )
        self.lbl_widget.grid(row=0, column=0, padx=15, pady=(12, 2), sticky="w")
        
        # Value
        self.val_widget = ctk.CTkLabel(
            self,
            text=value,
            font=styles.FONT_METRIC_VAL,
            text_color=value_color
        )
        self.val_widget.grid(row=1, column=0, padx=15, pady=(2, 12), sticky="w")

    def update_value(self, new_value: str):
        """Thread-safe update of the metric value."""
        self.val_widget.configure(text=new_value)


class DeviceRow(ctk.CTkFrame):
    """
    A single row in the device table.
    Displays: Status, ID, IP, Action Button.
    """
    def __init__(
        self,
        parent,
        device_id: str,
        ip: str,
        on_send_click: Callable[[str, str], None],
        **kwargs
    ):
        super().__init__(
            parent,
            fg_color=styles.PAINEL,
            corner_radius=styles.RADIUS_CARD,
            height=50,
            **kwargs
        )
        
        self.device_id = device_id
        self.ip = ip
        self.on_send_click = on_send_click
        
        # Configure columns
        # Column 0: Status (20%)
        # Column 1: ID (20%)
        # Column 2: IP (40%)
        # Column 3: Action Button (20%)
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=2)
        self.grid_columnconfigure(2, weight=4)
        self.grid_columnconfigure(3, weight=2)
        self.grid_rowconfigure(0, weight=1)
        
        # Status Label (Initial state is offline)
        self.status_lbl = ctk.CTkLabel(
            self,
            text="🔴 OFFLINE",
            font=styles.FONT_ROW,
            text_color=styles.OFFLINE,
            anchor="w"
        )
        self.status_lbl.grid(row=0, column=0, padx=(15, 5), pady=10, sticky="w")
        
        # Device ID
        self.id_lbl = ctk.CTkLabel(
            self,
            text=device_id,
            font=styles.FONT_ROW,
            text_color=styles.TEXTO,
            anchor="w"
        )
        self.id_lbl.grid(row=0, column=1, padx=5, pady=10, sticky="w")
        
        # IP Address
        self.ip_lbl = ctk.CTkLabel(
            self,
            text=ip,
            font=styles.FONT_ROW,
            text_color=styles.TEXTO_MUTED,
            anchor="w"
        )
        self.ip_lbl.grid(row=0, column=2, padx=5, pady=10, sticky="w")
        
        # Action button
        self.btn_send = ctk.CTkButton(
            self,
            text="ENVIAR",
            font=styles.FONT_BUTTON,
            fg_color=styles.BOTAO,
            hover_color=styles.HOVER,
            text_color=styles.TEXTO,
            corner_radius=styles.RADIUS_BUTTON,
            width=90,
            height=28,
            command=self._handle_click
        )
        self.btn_send.grid(row=0, column=3, padx=(5, 15), pady=10, sticky="e")

    def update_status(self, is_online: bool):
        """Updates the status label and color dynamically."""
        if is_online:
            self.status_lbl.configure(text="🟢 ONLINE", text_color=styles.ONLINE)
        else:
            self.status_lbl.configure(text="🔴 OFFLINE", text_color=styles.OFFLINE)

    def set_button_busy(self, busy: bool):
        """Temporarily disables the action button while request runs."""
        if busy:
            self.btn_send.configure(state="disabled", text="ENVIANDO...")
        else:
            self.btn_send.configure(state="normal", text="ENVIAR")

    def _handle_click(self):
        """Triggers the send callback."""
        self.on_send_click(self.device_id, self.ip)
