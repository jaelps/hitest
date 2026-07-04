import getpass
import logging
import os
import threading
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import customtkinter as ctk
from tkinter import filedialog

import ui.styles as styles
from services.logger import logger
from services.network import NetworkService
from ui.widgets import AirSensorCard, DeviceRow, DoserCard, MetricCard


class SettingsDialog(ctk.CTkToplevel):
    """Overlay settings dialog for importing, exporting, editing and tuning the dashboard."""

    def __init__(self, parent, config: Dict[str, List[Dict[str, str]]], on_save: Callable[[Dict[str, List[Dict[str, str]]]], None], on_interval_change: Optional[Callable[[int], None]], on_theme_change: Optional[Callable[[str], None]]):
        super().__init__(parent)
        self.title("Configurações HITEST")
        self.geometry("720x540")
        self.configure(fg_color=styles.FUNDO)
        self.transient(parent)
        self.grab_set()

        self.parent = parent
        self.config = config
        self.on_save = on_save
        self.on_interval_change = on_interval_change
        self.on_theme_change = on_theme_change

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)

        self.header = ctk.CTkFrame(self, fg_color=styles.PAINEL, corner_radius=styles.RADIUS_PANEL)
        self.header.grid(row=0, column=0, sticky="ew", padx=18, pady=16)
        self.header.grid_columnconfigure(0, weight=1)
        self.header.grid_columnconfigure(1, weight=0)
        ctk.CTkLabel(self.header, text="CONFIGURAÇÕES", font=styles.FONT_TITLE, text_color=styles.TEXTO).grid(row=0, column=0, sticky="w", padx=16, pady=14)
        ctk.CTkLabel(self.header, text="Gerencie dispositivos, intervalos e aparência", font=styles.FONT_SUBTITLE, text_color=styles.TEXTO_MUTED).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 14))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)

        left = ctk.CTkFrame(body, fg_color=styles.PAINEL, corner_radius=styles.RADIUS_PANEL)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=8)
        left.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(left, text="Arquivo", font=styles.FONT_HEADER, text_color=styles.TEXTO).grid(row=0, column=0, sticky="w", padx=12, pady=(12, 6))
        ctk.CTkButton(left, text="Importar JSON", fg_color=styles.BOTAO, hover_color=styles.HOVER, command=self._import_json, width=140).grid(row=1, column=0, padx=12, pady=4, sticky="w")
        ctk.CTkButton(left, text="Exportar JSON", fg_color=styles.BOTAO, hover_color=styles.HOVER, command=self._export_json, width=140).grid(row=2, column=0, padx=12, pady=4, sticky="w")
        ctk.CTkLabel(left, text="Monitoramento", font=styles.FONT_HEADER, text_color=styles.TEXTO).grid(row=3, column=0, sticky="w", padx=12, pady=(14, 6))
        self.interval_var = ctk.StringVar(value="15")
        ctk.CTkOptionMenu(left, values=["5", "10", "15", "30", "60"], variable=self.interval_var, command=self._on_interval_change, fg_color=styles.BOTAO, button_color=styles.BOTAO).grid(row=4, column=0, padx=12, pady=4, sticky="w")
        self.theme_var = ctk.StringVar(value="Escuro")
        ctk.CTkOptionMenu(left, values=["Escuro", "Claro", "Sistema"], variable=self.theme_var, command=self._on_theme_change, fg_color=styles.BOTAO, button_color=styles.BOTAO).grid(row=5, column=0, padx=12, pady=4, sticky="w")
        ctk.CTkLabel(left, text="Sobre", font=styles.FONT_HEADER, text_color=styles.TEXTO).grid(row=6, column=0, sticky="w", padx=12, pady=(14, 6))
        ctk.CTkLabel(left, text="HITEST v2.1\nMonitoramento industrial via heartbeat HTTP", font=styles.FONT_LOG, text_color=styles.TEXTO_MUTED, justify="left", anchor="w").grid(row=7, column=0, sticky="w", padx=12, pady=(0, 12))

        right = ctk.CTkFrame(body, fg_color=styles.PAINEL, corner_radius=styles.RADIUS_PANEL)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=8)
        right.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(right, text="Dispositivos", font=styles.FONT_HEADER, text_color=styles.TEXTO).grid(row=0, column=0, sticky="w", padx=12, pady=(12, 6))

        self.category_labels = {
            "machine_modules": "Módulos de Máquina",
            "air_sensors": "Sensores de Ar",
            "online_dosers": "Dosadoras Online",
        }
        self.category_keys = {value: key for key, value in self.category_labels.items()}
        self.category_var = ctk.StringVar(value=self.category_labels["machine_modules"])
        ctk.CTkLabel(right, text="Categoria", font=styles.FONT_ROW, text_color=styles.TEXTO_MUTED).grid(row=1, column=0, sticky="w", padx=12, pady=(4, 2))
        self.category_menu = ctk.CTkOptionMenu(right, values=list(self.category_labels.values()), variable=self.category_var, fg_color=styles.PAINEL, button_color=styles.BOTAO)
        self.category_menu.grid(row=2, column=0, padx=12, pady=2, sticky="ew")

        self.id_var = ctk.StringVar(value="")
        self.ip_var = ctk.StringVar(value="")
        ctk.CTkLabel(right, text="ID do dispositivo", font=styles.FONT_ROW, text_color=styles.TEXTO_MUTED).grid(row=3, column=0, sticky="w", padx=12, pady=(8, 2))
        ctk.CTkEntry(right, textvariable=self.id_var, fg_color=styles.FUNDO, border_color=styles.BORDER).grid(row=4, column=0, padx=12, pady=2, sticky="ew")
        ctk.CTkLabel(right, text="Endereço IP", font=styles.FONT_ROW, text_color=styles.TEXTO_MUTED).grid(row=5, column=0, sticky="w", padx=12, pady=(8, 2))
        ctk.CTkEntry(right, textvariable=self.ip_var, fg_color=styles.FUNDO, border_color=styles.BORDER).grid(row=6, column=0, padx=12, pady=2, sticky="ew")

        button_row = ctk.CTkFrame(right, fg_color="transparent")
        button_row.grid(row=7, column=0, sticky="ew", padx=12, pady=(10, 8))
        button_row.grid_columnconfigure((0, 1, 2), weight=1)
        ctk.CTkButton(button_row, text="Adicionar Dispositivo", fg_color=styles.BOTAO, hover_color=styles.HOVER, command=self._add_device).grid(row=0, column=0, padx=(0, 4))
        ctk.CTkButton(button_row, text="Editar Dispositivo", fg_color=styles.BOTAO, hover_color=styles.HOVER, command=self._edit_device).grid(row=0, column=1, padx=4)
        ctk.CTkButton(button_row, text="Remover Dispositivo", fg_color=styles.BOTAO, hover_color=styles.HOVER, command=self._remove_device).grid(row=0, column=2, padx=(4, 0))

        self.device_selector_var = ctk.StringVar(value="")
        ctk.CTkLabel(right, text="Selecionar dispositivo existente", font=styles.FONT_ROW, text_color=styles.TEXTO_MUTED).grid(row=8, column=0, sticky="w", padx=12, pady=(10, 2))
        self.selector_menu = ctk.CTkOptionMenu(right, values=self.device_choices, variable=self.device_selector_var, fg_color=styles.PAINEL, button_color=styles.BOTAO, command=self._populate_selected_device)
        self.selector_menu.grid(row=9, column=0, padx=12, pady=2, sticky="ew")
        self._refresh_device_selector()

        self.status_label = ctk.CTkLabel(right, text="Pronto para salvar", font=styles.FONT_LOG, text_color=styles.ONLINE)
        self.status_label.grid(row=10, column=0, sticky="w", padx=12, pady=(12, 8))

    @property
    def device_choices(self) -> List[str]:
        choices = []
        for category in ("machine_modules", "air_sensors", "online_dosers"):
            for item in self.config.get(category, []):
                device_id = item.get("id", "")
                if device_id:
                    choices.append(f"{self.category_labels.get(category, category)}:{device_id}")
        return choices

    def _refresh_device_selector(self):
        if not hasattr(self, "selector_menu"):
            return
        self.selector_menu.configure(values=self.device_choices)

    def _selected_category_key(self) -> str:
        return self.category_keys.get(self.category_var.get(), self.category_var.get())

    def _populate_selected_device(self, value: str):
        if ":" not in value:
            return
        category_label, device_id = value.split(":", 1)
        category = next((key for key, label in self.category_labels.items() if label == category_label), category_label)
        for item in self.config.get(category, []):
            if str(item.get("id", "")) == device_id:
                self.category_var.set(self.category_labels.get(category, category))
                self.id_var.set(str(item.get("id", "")))
                self.ip_var.set(str(item.get("ip", "")))
                return

    def _add_device(self):
        device_id = self.id_var.get().strip()
        ip_address = self.ip_var.get().strip()
        if not device_id or not ip_address:
            self.status_label.configure(text="Preencha o ID do dispositivo e o endereço IP", text_color=styles.OFFLINE)
            return

        category = self._selected_category_key()
        new_entry = {"id": device_id, "ip": ip_address}
        self.config.setdefault(category, [])
        self.config[category].append(new_entry)
        self.on_save(self.config)
        self.status_label.configure(text=f"Dispositivo adicionado na categoria {category}", text_color=styles.ONLINE)
        self._refresh_device_selector()

    def _edit_device(self):
        device_id = self.id_var.get().strip()
        ip_address = self.ip_var.get().strip()
        if not device_id or not ip_address:
            self.status_label.configure(text="Preencha o ID do dispositivo e o endereço IP", text_color=styles.OFFLINE)
            return
        category = self._selected_category_key()
        for item in self.config.get(category, []):
            if str(item.get("id", "")) == device_id:
                item["id"] = device_id
                item["ip"] = ip_address
                self.on_save(self.config)
                self.status_label.configure(text="Dispositivo atualizado", text_color=styles.ONLINE)
                self._refresh_device_selector()
                return
        self.status_label.configure(text="Dispositivo não encontrado para editar", text_color=styles.OFFLINE)

    def _remove_device(self):
        device_id = self.id_var.get().strip()
        category = self._selected_category_key()
        if not device_id:
            self.status_label.configure(text="Selecione um dispositivo para remover", text_color=styles.OFFLINE)
            return
        self.config[category] = [item for item in self.config.get(category, []) if str(item.get("id", "")) != device_id]
        self.on_save(self.config)
        self.status_label.configure(text="Dispositivo removido", text_color=styles.ONLINE)
        self._refresh_device_selector()

    def _import_json(self):
        path = filedialog.askopenfilename(title="Importar JSON", filetypes=[("JSON", "*.json")])
        if not path:
            return
        import json
        with open(path, "r", encoding="utf-8") as handle:
            imported = json.load(handle)
        self.config = imported
        self.on_save(self.config)
        self.status_label.configure(text="Configuração importada", text_color=styles.ONLINE)

    def _export_json(self):
        path = filedialog.asksaveasfilename(title="Exportar JSON", defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not path:
            return
        import json
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(self.config, handle, indent=2)
        self.status_label.configure(text="Configuração exportada", text_color=styles.ONLINE)

    def _on_interval_change(self, value: str):
        if self.on_interval_change:
            self.on_interval_change(int(value))

    def _on_theme_change(self, value: str):
        theme_map = {"Escuro": "Dark", "Claro": "Light", "Sistema": "System"}
        if self.on_theme_change:
            self.on_theme_change(theme_map.get(value, value))


class HitestMainWindow(ctk.CTk):
    """Main dashboard window for the Hitest system."""

    def __init__(
        self,
        config: Dict[str, List[Dict[str, str]]],
        on_refresh_click: Optional[Callable[[], None]] = None,
        on_command_result: Optional[Callable[[str, bool], None]] = None,
        on_settings_save: Optional[Callable[[Dict[str, List[Dict[str, str]]]], None]] = None,
        on_monitoring_interval_changed: Optional[Callable[[int], None]] = None,
        on_theme_changed: Optional[Callable[[str], None]] = None,
    ):
        super().__init__()

        self.config = config
        self.on_refresh_click = on_refresh_click
        self.on_command_result = on_command_result
        self.on_settings_save = on_settings_save
        self.on_monitoring_interval_changed = on_monitoring_interval_changed
        self.on_theme_changed = on_theme_changed
        self.device_cards: Dict[str, Any] = {}
        self.current_tab = "machine_modules"
        self.log_visible = True

        self.title("HITEST - Sistema de Controle e Monitoramento ESP8266")
        self.geometry("940x840")
        self.minsize(860, 720)
        self.configure(fg_color=styles.FUNDO)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=1)
        self.grid_rowconfigure(4, weight=0)
        self.grid_rowconfigure(5, weight=0)

        self.icon_path = os.path.join("assets", "logo.ico")
        if os.path.exists(self.icon_path):
            try:
                self.iconbitmap(self.icon_path)
            except Exception:
                pass

        self._create_header()
        self._create_metrics_panel()
        self._create_tabs()
        self._create_content_area()
        self._create_log_panel()
        self._create_status_bar()
        self._setup_gui_log_handler()
        self._refresh_status_bar()

    def _create_header(self):
        """Creates the top header panel."""
        self.header_frame = ctk.CTkFrame(self, fg_color=styles.PAINEL, height=80, corner_radius=0, border_width=0)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        self.header_frame.grid_columnconfigure(0, weight=1)
        self.header_frame.grid_columnconfigure(1, weight=0)

        title_container = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        title_container.grid(row=0, column=0, padx=25, pady=12, sticky="w")
        ctk.CTkLabel(title_container, text="HITEST", font=styles.FONT_TITLE, text_color=styles.TEXTO).pack(anchor="w")
        ctk.CTkLabel(title_container, text="Sistema de Controle e Monitoramento ESP8266", font=styles.FONT_SUBTITLE, text_color=styles.TEXTO_MUTED).pack(anchor="w")

        right_actions = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        right_actions.grid(row=0, column=1, padx=18, pady=12, sticky="e")
        self.btn_refresh = ctk.CTkButton(right_actions, text="ATUALIZAR", font=styles.FONT_BUTTON, fg_color=styles.BOTAO, hover_color=styles.HOVER, text_color=styles.TEXTO, corner_radius=styles.RADIUS_BUTTON, width=110, height=32, command=self._handle_refresh_click)
        self.btn_refresh.pack(side="left", padx=(0, 6))
        self.btn_settings = ctk.CTkButton(right_actions, text="⚙", font=styles.FONT_BUTTON, fg_color=styles.BOTAO, hover_color=styles.HOVER, text_color=styles.TEXTO, corner_radius=styles.RADIUS_BUTTON, width=38, height=32, command=self._handle_settings_click)
        self.btn_settings.pack(side="left")

    def _create_metrics_panel(self):
        """Creates the summary metric cards above the tabs."""
        self.metrics_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.metrics_frame.grid(row=1, column=0, sticky="ew", padx=styles.SPACING_OUTER, pady=(16, 8))
        self.metrics_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1, uniform="equal")

        self.card_total = MetricCard(self.metrics_frame, label="Total", value="0", value_color=styles.TEXTO)
        self.card_total.grid(row=0, column=0, padx=(0, 6), sticky="nsew")
        self.card_online = MetricCard(self.metrics_frame, label="Online", value="0", value_color=styles.ONLINE)
        self.card_online.grid(row=0, column=1, padx=6, sticky="nsew")
        self.card_offline = MetricCard(self.metrics_frame, label="Offline", value="0", value_color=styles.OFFLINE)
        self.card_offline.grid(row=0, column=2, padx=6, sticky="nsew")
        self.card_last_update = MetricCard(self.metrics_frame, label="Últ. Atualização", value="--:--:--", value_color=styles.TEXTO)
        self.card_last_update.grid(row=0, column=3, padx=6, sticky="nsew")
        self.card_system_status = MetricCard(self.metrics_frame, label="Status", value="PRONTO", value_color=styles.ONLINE)
        self.card_system_status.grid(row=0, column=4, padx=(6, 0), sticky="nsew")

    def _create_tabs(self):
        """Creates the horizontal tab buttons below the summary cards."""
        self.tabs_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.tabs_frame.grid(row=2, column=0, sticky="ew", padx=styles.SPACING_OUTER, pady=(6, 10))
        self.tabs_frame.grid_columnconfigure((0, 1, 2), weight=1, uniform="tabs")

        self.tab_buttons = {}
        for idx, tab_name in enumerate([("machine_modules", "Módulos de Máquina"), ("air_sensors", "Sensores de Ar"), ("online_dosers", "Dosadoras Online")]):
            button = ctk.CTkButton(
                self.tabs_frame,
                text=tab_name[1],
                font=styles.FONT_BUTTON,
                fg_color=styles.BOTAO,
                hover_color=styles.HOVER,
                text_color=styles.TEXTO,
                corner_radius=styles.RADIUS_BUTTON,
                height=34,
                command=lambda key=tab_name[0]: self._switch_tab(key),
            )
            button.grid(row=0, column=idx, padx=4, sticky="nsew")
            self.tab_buttons[tab_name[0]] = button
        self._refresh_tab_selection()

    def _create_content_area(self):
        """Creates the scrollable content area where each category view is shown."""
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=3, column=0, sticky="nsew", padx=styles.SPACING_OUTER, pady=(0, 10))
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

        self.category_frames = {}
        for tab_key in ("machine_modules", "air_sensors", "online_dosers"):
            frame = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent", corner_radius=0)
            frame.grid(row=0, column=0, sticky="nsew")
            frame.grid_columnconfigure(0, weight=1)
            self.category_frames[tab_key] = frame
        self._populate_content()
        self._show_tab(self.current_tab)

    def _create_log_panel(self):
        """Creates a collapsible log panel at the bottom of the window."""
        self.log_panel = ctk.CTkFrame(self, fg_color=styles.PAINEL, corner_radius=styles.RADIUS_PANEL)
        self.log_panel.grid(row=4, column=0, sticky="ew", padx=styles.SPACING_OUTER, pady=(0, 10))
        self.log_panel.grid_columnconfigure(0, weight=1)
        self.log_panel.grid_rowconfigure(1, weight=1)
        ctk.CTkButton(self.log_panel, text="Ocultar Registros", fg_color=styles.BOTAO, hover_color=styles.HOVER, command=self._toggle_log).grid(row=0, column=0, sticky="e", padx=12, pady=(8, 4))
        self.log_textbox = ctk.CTkTextbox(self.log_panel, height=110, fg_color="#090d16", text_color=styles.TEXTO, font=styles.FONT_LOG, border_width=1, border_color=styles.BORDER, corner_radius=8)
        self.log_textbox.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))
        self.log_textbox.configure(state="disabled")

    def _create_status_bar(self):
        """Creates the bottom status bar with runtime status values."""
        self.status_bar = ctk.CTkFrame(self, fg_color=styles.PAINEL, corner_radius=styles.RADIUS_PANEL)
        self.status_bar.grid(row=5, column=0, sticky="ew", padx=styles.SPACING_OUTER, pady=(0, 16))
        self.status_bar.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1, uniform="status")
        self.status_ready = ctk.CTkLabel(self.status_bar, text="Pronto", font=styles.STATUS_FONT, text_color=styles.ONLINE)
        self.status_ready.grid(row=0, column=0, padx=8, pady=8, sticky="w")
        self.status_comm = ctk.CTkLabel(self.status_bar, text="Comunicação", font=styles.STATUS_FONT, text_color=styles.TEXTO_MUTED)
        self.status_comm.grid(row=0, column=1, padx=8, pady=8, sticky="w")
        self.status_last_command = ctk.CTkLabel(self.status_bar, text="Últ. Comando", font=styles.STATUS_FONT, text_color=styles.TEXTO_MUTED)
        self.status_last_command.grid(row=0, column=2, padx=8, pady=8, sticky="w")
        self.status_user = ctk.CTkLabel(self.status_bar, text="Usuário", font=styles.STATUS_FONT, text_color=styles.TEXTO_MUTED)
        self.status_user.grid(row=0, column=3, padx=8, pady=8, sticky="w")
        self.status_version = ctk.CTkLabel(self.status_bar, text="Versão", font=styles.STATUS_FONT, text_color=styles.TEXTO_MUTED)
        self.status_version.grid(row=0, column=4, padx=8, pady=8, sticky="w")
        self.status_time = ctk.CTkLabel(self.status_bar, text="Hora", font=styles.STATUS_FONT, text_color=styles.TEXTO_MUTED)
        self.status_time.grid(row=0, column=5, padx=8, pady=8, sticky="w")

    def _populate_content(self):
        """Builds the cards for each device category."""
        for tab_key in ("machine_modules", "air_sensors", "online_dosers"):
            frame = self.category_frames[tab_key]
            for child in frame.winfo_children():
                child.destroy()

            devices = self.config.get(tab_key, [])
            if not devices:
                placeholder = ctk.CTkLabel(frame, text="Nenhum dispositivo configurado nesta categoria", font=styles.FONT_ROW, text_color=styles.TEXTO_MUTED)
                placeholder.grid(row=0, column=0, padx=10, pady=10, sticky="w")
                continue

            for index, device in enumerate(devices):
                device_id = str(device.get("id", ""))
                ip_address = str(device.get("ip", ""))
                if tab_key == "machine_modules":
                    row = DeviceRow(frame, device_id=device_id, ip=ip_address, on_send_click=self._handle_send_command)
                    row.grid(row=index, column=0, sticky="ew", padx=4, pady=5)
                    self.device_cards[device_id] = row
                elif tab_key == "air_sensors":
                    row = AirSensorCard(frame, device_id=device_id, ip=ip_address)
                    row.grid(row=index, column=0, sticky="ew", padx=4, pady=5)
                    self.device_cards[device_id] = row
                else:
                    row = DoserCard(frame, device_id=device_id, ip=ip_address, on_send_click=self._handle_send_command)
                    row.grid(row=index, column=0, sticky="ew", padx=4, pady=5)
                    self.device_cards[device_id] = row

    def _show_tab(self, tab_key: str):
        """Shows only the selected category frame."""
        for key, frame in self.category_frames.items():
            frame.grid_forget()
        self.category_frames[tab_key].grid(row=0, column=0, sticky="nsew")
        self.current_tab = tab_key
        self._refresh_tab_selection()

    def _switch_tab(self, tab_key: str):
        """Switches the currently displayed tab without recreating the window."""
        self._show_tab(tab_key)

    def _refresh_tab_selection(self):
        """Highlights the active tab button."""
        for key, button in self.tab_buttons.items():
            if key == self.current_tab:
                button.configure(fg_color=styles.HOVER, hover_color=styles.HOVER)
            else:
                button.configure(fg_color=styles.BOTAO, hover_color=styles.HOVER)

    def _toggle_log(self):
        """Toggles the log panel visibility."""
        self.log_visible = not self.log_visible
        if self.log_visible:
            self.log_panel.grid()
            self.log_panel.winfo_children()[0].configure(text="Ocultar Registros")
        else:
            self.log_panel.grid_remove()
            self.log_panel.winfo_children()[0].configure(text="Mostrar Registros")

    def _setup_gui_log_handler(self):
        """Attaches a log handler to display new log records in the CTkTextbox."""
        class GuiLogHandler(logging.Handler):
            def __init__(self, write_cb):
                super().__init__()
                self.write_cb = write_cb

            def emit(self, record):
                try:
                    self.write_cb(self.format(record))
                except Exception:
                    self.handleError(record)

        from services.logger import CustomFormatter

        hitest_logger = logging.getLogger("Hitest")
        if not any(isinstance(handler, GuiLogHandler) for handler in hitest_logger.handlers):
            gui_handler = GuiLogHandler(self._append_log_message)
            gui_handler.setFormatter(CustomFormatter())
            hitest_logger.addHandler(gui_handler)

    def _append_log_message(self, message: str):
        """Append log message thread-safely."""
        self.after(0, self._safe_append_log, message)

    def _safe_append_log(self, message: str):
        """Appends log message to the textbox and scrolls it down."""
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", message + "\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def apply_config(self, config: Dict[str, List[Dict[str, str]]]):
        """Refreshes the UI state when the configuration is updated."""
        self.config = config
        self._populate_content()
        self._show_tab(self.current_tab)

    def on_device_status_change(self, device_id: str, is_online: bool, details: Optional[Dict[str, Any]] = None):
        """Thread-safe status update callback from the monitor."""
        self.after(0, self._safe_update_device_ui, device_id, is_online, details)

    def on_monitor_cycle_complete(self, online_cnt: int, offline_cnt: int, timestamp: str):
        """Thread-safe cycle update callback from the monitor."""
        self.after(0, self._safe_update_metrics_ui, online_cnt, offline_cnt, timestamp)

    def _safe_update_device_ui(self, device_id: str, is_online: bool, details: Optional[Dict[str, Any]] = None):
        """Updates the matching widget with the latest status and telemetry."""
        widget = self.device_cards.get(device_id)
        if widget:
            widget.update_status(is_online, details)
        else:
            logger.warning(f"Dispositivo {device_id} não encontrado na interface UI")

    def _safe_update_metrics_ui(self, online_cnt: int, offline_cnt: int, timestamp: str):
        """Updates metrics panel widgets."""
        self.card_total.update_value(str(len(self.config.get("machine_modules", [])) + len(self.config.get("air_sensors", [])) + len(self.config.get("online_dosers", []))))
        self.card_online.update_value(str(online_cnt))
        self.card_offline.update_value(str(offline_cnt))
        self.card_last_update.update_value(timestamp)
        self.card_system_status.update_value("PRONTO")

    def _refresh_status_bar(self):
        """Keeps the status bar values current."""
        now = datetime.now()
        self.status_ready.configure(text=f"Pronto | {now.strftime('%H:%M:%S')}")
        self.status_comm.configure(text="Comunicação: heartbeat HTTP")
        self.status_last_command.configure(text="Últ. Comando: nenhum")
        self.status_user.configure(text=f"Usuário: {getpass.getuser()}")
        self.status_version.configure(text="Versão: 2.1")
        self.status_time.configure(text=f"Hora: {now.strftime('%d/%m/%Y %H:%M:%S')}")
        self.after(1000, self._refresh_status_bar)

    def _handle_refresh_click(self):
        """Triggered when clicking the configuration refresh button."""
        if self.on_refresh_click:
            self.on_refresh_click()

    def _handle_settings_click(self):
        """Opens the settings dialog without recreating the main window."""
        SettingsDialog(self, self.config, self._handle_settings_save, self._handle_monitoring_interval_change, self._handle_theme_change)

    def _handle_settings_save(self, config: Dict[str, List[Dict[str, str]]]):
        """Saves configuration updates coming from the settings dialog."""
        if self.on_settings_save:
            self.on_settings_save(config)

    def _handle_monitoring_interval_change(self, value: int):
        """Forwards the monitoring interval selection to the controller."""
        if self.on_monitoring_interval_changed:
            self.on_monitoring_interval_changed(value)

    def _handle_theme_change(self, value: str):
        """Forwards the selected theme to the controller."""
        if self.on_theme_changed:
            self.on_theme_changed(value)

    def _handle_send_command(self, device_id: str, ip: str):
        """Triggered when the user clicks the command button in a device card."""
        widget = self.device_cards.get(device_id)
        if widget and hasattr(widget, "set_button_busy"):
            widget.set_button_busy(True)

        thread = threading.Thread(target=self._run_send_command_thread, args=(device_id, ip), name=f"SendCommand-{device_id}")
        thread.daemon = True
        thread.start()

    def _run_send_command_thread(self, device_id: str, ip: str):
        """Sends the command and reports back to the UI thread."""
        success, _ = NetworkService.send_command(device_id, ip)
        self.after(0, self._safe_on_send_command_complete, device_id, success)

    def _safe_on_send_command_complete(self, device_id: str, success: bool):
        """Re-enables command button and forwards the command result to the controller."""
        widget = self.device_cards.get(device_id)
        if widget and hasattr(widget, "set_button_busy"):
            widget.set_button_busy(False)

        if self.on_command_result:
            self.on_command_result(device_id, success)

        if success:
            logger.info(f"Comando enviado com sucesso para {device_id}")
        else:
            logger.warning(f"Falha ao enviar comando para {device_id}")