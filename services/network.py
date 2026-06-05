import subprocess
import shutil
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
            # Check if curl is available
            if shutil.which('curl') is None:
                logger.warning("curl não encontrado no PATH. Usando fallback.")
                return False
            
            # Using curl command to send test request
            cmd = f'curl -s -m {int(timeout)} "{url}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, timeout=timeout+1)
            # A successful exit code (0) means it is online
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            return False
        except Exception as e:
            logger.error(f"Erro ao verificar dispositivo {ip}: {str(e)}")
            return False

    @staticmethod
    def send_command(device_id: str, ip: str, timeout: float = 2.0) -> Tuple[bool, str]:
        """
        Sends the control command (curl to /lb) to the device.
        
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
            # Check if curl is available
            if shutil.which('curl') is None:
                msg = "curl não encontrado no sistema"
                logger.error(f"Erro ao enviar comando para {ip}: {msg}")
                return False, msg
            
            cmd = f'curl -s -m {int(timeout)} "{url}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, timeout=timeout+1, text=True)
            if result.returncode == 0:
                msg = f"Sucesso: {result.stdout.strip()}"
                return True, msg
            else:
                try:
                    error_msg = result.stderr.strip()
                except (UnicodeDecodeError, AttributeError):
                    error_msg = "Erro ao decodificar resposta"
                msg = f"Erro: {error_msg}"
                logger.error(f"Erro ao enviar comando para {ip}: {msg}")
                return False, msg
        except subprocess.TimeoutExpired as e:
            msg = f"Timeout: {str(e)}"
            logger.error(f"Erro de rede ao enviar comando para {ip}: {msg}")
            return False, msg
        except Exception as e:
            msg = str(e)
            logger.error(f"Erro ao enviar comando para {ip}: {msg}")
            return False, msg
