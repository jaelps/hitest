import json
import socket
from typing import Any, Dict, Optional, Tuple
from urllib import error, request

from services.logger import logger


class NetworkService:
    """Handles lightweight HTTP communication with ESP8266 devices."""

    @staticmethod
    def _request(url: str, timeout: float = 2.0) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """Performs a GET request and returns a normalized success payload."""
        try:
            with request.urlopen(url, timeout=timeout) as response:
                body = response.read().decode("utf-8", errors="replace")
                status = getattr(response, "status", 200)
                if status >= 400:
                    return False, None, f"HTTP {status}"
                return True, {"status": status, "body": body}, body
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            return False, None, f"HTTP {exc.code}: {body or exc.reason}"
        except error.URLError as exc:
            reason = getattr(exc, "reason", str(exc))
            return False, None, f"Erro de rede: {reason}"
        except (socket.timeout, TimeoutError) as exc:
            return False, None, f"Tempo limite excedido: {exc}"
        except (socket.error, OSError) as exc:
            return False, None, f"Erro de conexão: {exc}"
        except Exception as exc:
            return False, None, f"Erro inesperado: {exc}"

    @staticmethod
    def probe_connectivity(ip: str, timeout: float = 2.0) -> bool:
        """Verifies a device is reachable via HTTP GET /."""
        url = f"http://{ip}/"
        success, _, detail = NetworkService._request(url, timeout=timeout)
        if not success:
            logger.warning(f"Falha na verificacao inicial de {ip}: {detail}")
        return success

    @staticmethod
    def ping_device(ip: str, timeout: float = 2.0) -> bool:
        """Backward-compatible alias for initial HTTP connectivity checks."""
        return NetworkService.probe_connectivity(ip, timeout=timeout)

    @staticmethod
    def check_heartbeat(ip: str, timeout: float = 2.0) -> Dict[str, Any]:
        """Requests the device heartbeat endpoint and returns normalized metadata."""
        url = f"http://{ip}/heartbeat"
        success, payload, detail = NetworkService._request(url, timeout=timeout)

        if not success:
            logger.warning(f"Heartbeat timeout/erro para {ip}: {detail}")
            return {
                "success": False,
                "error": detail,
                "device_id": "",
                "firmware_version": "",
                "uptime": 0,
                "status": "offline",
            }

        try:
            body = payload.get("body", "") if payload else ""
            parsed = json.loads(body) if body else {}
            if not isinstance(parsed, dict):
                raise ValueError("Resposta do heartbeat não é um objeto JSON válido")

            logger.info(f"Heartbeat recebido de {ip}: {parsed}")
            return {
                "success": True,
                "error": "",
                "device_id": str(parsed.get("device", "")),
                "firmware_version": str(parsed.get("version", "")),
                "uptime": int(parsed.get("uptime", 0)),
                "status": str(parsed.get("status", "ok")),
            }
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            logger.warning(f"JSON inválido recebido de {ip}: {exc}")
            return {
                "success": False,
                "error": f"JSON inválido: {exc}",
                "device_id": "",
                "firmware_version": "",
                "uptime": 0,
                "status": "offline",
            }

    @staticmethod
    def send_command(device_id: str, ip: str, timeout: float = 2.0) -> Tuple[bool, str]:
        """Sends a command by calling the device's /lb endpoint."""
        url = f"http://{ip}/lb"
        logger.info(f"Comando enviado para {ip} (ID: {device_id})")

        success, _, detail = NetworkService._request(url, timeout=timeout)
        if success:
            logger.info(f"Comando executado com sucesso em {ip}")
            return True, "Comando executado com sucesso"

        logger.error(f"Erro ao enviar comando para {ip}: {detail}")
        return False, detail
