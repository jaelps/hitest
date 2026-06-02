import requests
from typing import Tuple
from services.logger import logger

class NetworkService:
    """Handles HTTP communication with ESP8266 devices."""
    
    @staticmethod
    def ping_device(ip: str, timeout: float = 2.0) -> bool:
        """
        Checks if the ESP8266 is online.
        
        Args:
            ip: IP address of the device.
            timeout: Timeout in seconds for the request.
            
        Returns:
            bool: True if the device responds successfully, False otherwise.
        """
        url = f"http://{ip}/lb"
        try:
            # Using requests.get as strictly mandated
            response = requests.get(url, timeout=timeout)
            # A successful status code (2xx/3xx) means it is online
            return response.status_code < 400
        except requests.RequestException:
            return False

    @staticmethod
    def send_command(device_id: str, ip: str, timeout: float = 2.0) -> Tuple[bool, str]:
        """
        Sends the control command (HTTP GET to /lb) to the device.
        
        Args:
            device_id: ID of the device.
            ip: IP address of the device.
            timeout: Timeout in seconds.
            
        Returns:
            Tuple[bool, str]: (Success status, details/error message).
        """
        url = f"http://{ip}/lb"
        logger.info(f"Comando enviado para {ip} (ID: {device_id})")
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code < 400:
                msg = f"Sucesso: {response.status_code}"
                return True, msg
            else:
                msg = f"Erro HTTP {response.status_code}"
                logger.error(f"Erro ao enviar comando para {ip}: {msg}")
                return False, msg
        except requests.RequestException as e:
            msg = str(e)
            logger.error(f"Erro de rede ao enviar comando para {ip}: {msg}")
            return False, msg
