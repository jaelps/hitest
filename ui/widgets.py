from typing import Any, Callable, Dict, Optional

import customtkinter as ctk

import ui.styles as styles


class MetricCard(ctk.CTkFrame):
    """A card showing a single metric with a label and large value."""

    def __init__(
        self,
        parent,
        label: str,
        value: str,
        value_color: str = styles.TEXTO,
        **kwargs,
    ):
        super().__init__(
            parent,
            fg_color=styles.PAINEL,
            corner_radius=styles.RADIUS_PANEL,
            border_width=1,
            border_color=styles.BORDER,
            **kwargs,
        )

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((0, 1), weight=1)

        self.lbl_widget = ctk.CTkLabel(
            self,
            text=label.upper(),
            font=styles.FONT_METRIC_LBL,
            text_color=styles.TEXTO_MUTED,
        )
        self.lbl_widget.grid(row=0, column=0, padx=15, pady=(12, 2), sticky="w")

        self.val_widget = ctk.CTkLabel(
            self,
            text=value,
            font=styles.FONT_METRIC_VAL,
            text_color=value_color,
        )
        self.val_widget.grid(row=1, column=0, padx=15, pady=(2, 12), sticky="w")

    def update_value(self, new_value: str):
        """Updates the metric value."""
        self.val_widget.configure(text=new_value)


class DeviceRow(ctk.CTkFrame):
    """A machine module card with status, identity, telemetry and command action."""

    def __init__(
        self,
        parent,
        device_id: str,
        ip: str,
        on_send_click: Callable[[str, str], None],
        show_button: bool = True,
        **kwargs,
    ):
        super().__init__(
            parent,
            fg_color=styles.PAINEL,
            corner_radius=styles.RADIUS_CARD,
            height=78,
            **kwargs,
        )

        self.device_id = device_id
        self.ip = ip
        self.on_send_click = on_send_click
        self.show_button = show_button

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure((0, 1, 2), weight=0)

        self.status_lbl = ctk.CTkLabel(
            self,
            text="🔴 DESCONECTADO",
            font=styles.CARD_TITLE_FONT,
            text_color=styles.OFFLINE,
            anchor="w",
        )
        self.status_lbl.grid(row=0, column=0, padx=(12, 6), pady=(10, 4), sticky="w")

        self.id_lbl = ctk.CTkLabel(
            self,
            text=f"ID: {device_id}",
            font=styles.CARD_TEXT_FONT,
            text_color=styles.TEXTO,
            anchor="w",
        )
        self.id_lbl.grid(row=1, column=0, padx=(12, 6), pady=(0, 2), sticky="w")

        self.ip_lbl = ctk.CTkLabel(
            self,
            text=f"IP: {ip}",
            font=styles.CARD_TEXT_FONT,
            text_color=styles.TEXTO_MUTED,
            anchor="w",
        )
        self.ip_lbl.grid(row=2, column=0, padx=(12, 6), pady=(0, 6), sticky="w")

        if show_button:
            self.btn_send = ctk.CTkButton(
                self,
                text="Enviar",
                font=styles.FONT_BUTTON,
                fg_color=styles.BOTAO,
                hover_color=styles.HOVER,
                text_color=styles.TEXTO,
                corner_radius=styles.RADIUS_BUTTON,
                width=78,
                height=28,
                command=self._handle_click,
            )
            self.btn_send.grid(row=0, column=1, padx=(6, 12), pady=(8, 4), sticky="e")

        self.details_lbl = ctk.CTkLabel(
            self,
            text="Firmware: -- | Tempo ativo: -- | Últ. Comunicação: -- | Últ. Comando: --",
            font=styles.CARD_TEXT_FONT,
            text_color=styles.TEXTO_MUTED,
            anchor="w",
            justify="left",
            wraplength=620,
        )
        self.details_lbl.grid(row=3, column=0, columnspan=2, padx=(12, 12), pady=(2, 12), sticky="w")

    def update_status(self, is_online: bool, details: Optional[Dict[str, Any]] = None):
        """Updates the status badge and detail line."""
        if is_online:
            self.status_lbl.configure(text="🟢 CONECTADO", text_color=styles.ONLINE)
        else:
            self.status_lbl.configure(text="🔴 DESCONECTADO", text_color=styles.OFFLINE)

        if details:
            firmware_version = details.get("firmware_version") or "--"
            uptime = details.get("uptime") or "--"
            last_comm = details.get("last_communication") or "--"
            last_command = details.get("last_command") or "--"
            self.details_lbl.configure(
                text=f"Firmware: {firmware_version} | Tempo ativo: {uptime} | Últ. Comunicação: {last_comm} | Últ. Comando: {last_command}"
            )

    def set_button_busy(self, busy: bool):
        """Temporarily disables the action button while request runs."""
        if self.show_button:
            if busy:
                self.btn_send.configure(state="disabled", text="Enviando...")
            else:
                self.btn_send.configure(state="normal", text="Enviar")

    def _handle_click(self):
        """Triggers the send callback."""
        self.on_send_click(self.device_id, self.ip)


class AirSensorCard(ctk.CTkFrame):
    """A compact sensor card designed to follow the same industrial styling."""

    def __init__(self, parent, device_id: str, ip: str, **kwargs):
        super().__init__(parent, fg_color=styles.PAINEL, corner_radius=styles.RADIUS_CARD, **kwargs)
        self.device_id = device_id
        self.ip = ip

        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure((0, 1), weight=1)

        self.status_lbl = ctk.CTkLabel(self, text="🔴 DESCONECTADO", font=styles.CARD_TITLE_FONT, text_color=styles.OFFLINE, anchor="w")
        self.status_lbl.grid(row=0, column=0, padx=(12, 6), pady=(10, 4), sticky="w")

        self.id_lbl = ctk.CTkLabel(self, text=f"ID: {device_id}", font=styles.CARD_TEXT_FONT, text_color=styles.TEXTO, anchor="w")
        self.id_lbl.grid(row=1, column=0, padx=(12, 6), pady=(0, 2), sticky="w")

        self.ip_lbl = ctk.CTkLabel(self, text=f"IP: {ip}", font=styles.CARD_TEXT_FONT, text_color=styles.TEXTO_MUTED, anchor="w")
        self.ip_lbl.grid(row=2, column=0, padx=(12, 6), pady=(0, 6), sticky="w")

        self.details_lbl = ctk.CTkLabel(self, text="Temp.: -- | Umid.: -- | Press.: -- | Qual. ar: -- | RSSI: -- | Firmware: -- | Últ. Atualização: --", font=styles.CARD_TEXT_FONT, text_color=styles.TEXTO_MUTED, justify="left", anchor="w", wraplength=620)
        self.details_lbl.grid(row=3, column=0, columnspan=2, padx=(12, 12), pady=(2, 12), sticky="w")

    def update_status(self, is_online: bool, details: Optional[Dict[str, Any]] = None):
        if is_online:
            self.status_lbl.configure(text="🟢 CONECTADO", text_color=styles.ONLINE)
        else:
            self.status_lbl.configure(text="🔴 DESCONECTADO", text_color=styles.OFFLINE)

        if details:
            self.details_lbl.configure(
                text=(
                    f"Temp.: {details.get('temperature', '--')} | Umid.: {details.get('humidity', '--')} | "
                    f"Press.: {details.get('pressure', '--')} | Qual. ar: {details.get('air_quality', '--')} | "
                    f"RSSI: {details.get('rssi', '--')} | Firmware: {details.get('firmware_version', '--')} | "
                    f"Últ. Atualização: {details.get('last_update', '--')}"
                )
            )


class DoserCard(ctk.CTkFrame):
    """A dosing system card that keeps the same industrial look and feel."""

    def __init__(self, parent, device_id: str, ip: str, on_send_click: Callable[[str, str], None], **kwargs):
        super().__init__(parent, fg_color=styles.PAINEL, corner_radius=styles.RADIUS_CARD, **kwargs)
        self.device_id = device_id
        self.ip = ip
        self.on_send_click = on_send_click

        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure((0, 1), weight=1)

        self.status_lbl = ctk.CTkLabel(self, text="🔴 DESCONECTADO", font=styles.CARD_TITLE_FONT, text_color=styles.OFFLINE, anchor="w")
        self.status_lbl.grid(row=0, column=0, padx=(12, 6), pady=(10, 4), sticky="w")

        self.id_lbl = ctk.CTkLabel(self, text=f"ID: {device_id}", font=styles.CARD_TEXT_FONT, text_color=styles.TEXTO, anchor="w")
        self.id_lbl.grid(row=1, column=0, padx=(12, 6), pady=(0, 2), sticky="w")

        self.ip_lbl = ctk.CTkLabel(self, text=f"IP: {ip}", font=styles.CARD_TEXT_FONT, text_color=styles.TEXTO_MUTED, anchor="w")
        self.ip_lbl.grid(row=2, column=0, padx=(12, 6), pady=(0, 6), sticky="w")

        self.btn_send = ctk.CTkButton(
            self,
            text="Enviar",
            font=styles.FONT_BUTTON,
            fg_color=styles.BOTAO,
            hover_color=styles.HOVER,
            text_color=styles.TEXTO,
            corner_radius=styles.RADIUS_BUTTON,
            width=78,
            height=28,
            command=self._handle_click,
        )
        self.btn_send.grid(row=0, column=1, padx=(6, 12), pady=(8, 4), sticky="e")

        self.details_lbl = ctk.CTkLabel(self, text="Receita: -- | Produção: -- | Reservatório: -- | Vazão: -- | Status: -- | Firmware: -- | Últ. Comunicação: --", font=styles.CARD_TEXT_FONT, text_color=styles.TEXTO_MUTED, justify="left", anchor="w", wraplength=620)
        self.details_lbl.grid(row=3, column=0, columnspan=2, padx=(12, 12), pady=(2, 12), sticky="w")

    def update_status(self, is_online: bool, details: Optional[Dict[str, Any]] = None):
        if is_online:
            self.status_lbl.configure(text="🟢 CONECTADO", text_color=styles.ONLINE)
        else:
            self.status_lbl.configure(text="🔴 DESCONECTADO", text_color=styles.OFFLINE)

        if details:
            self.details_lbl.configure(
                text=(
                    f"Receita: {details.get('recipe', '--')} | Produção: {details.get('production_counter', '--')} | "
                    f"Reservatório: {details.get('tank_level', '--')} | Vazão: {details.get('flow_rate', '--')} | "
                    f"Status: {details.get('operating_status', '--')} | Firmware: {details.get('firmware_version', '--')} | "
                    f"Últ. Comunicação: {details.get('last_communication', '--')}"
                )
            )

    def _handle_click(self):
        self.on_send_click(self.device_id, self.ip)
