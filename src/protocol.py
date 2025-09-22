"""
Protocolo de Aplicação - Transporte Confiável de Dados
Implementa as regras de comunicação entre cliente e servidor
"""

import struct
import json
from enum import Enum
from typing import Dict, Any, Optional

class MessageType(Enum):
    """Tipos de mensagem do protocolo"""
    HANDSHAKE_REQUEST = "HANDSHAKE_REQ"
    HANDSHAKE_RESPONSE = "HANDSHAKE_RESP"
    DATA = "DATA"
    ACK = "ACK"
    NACK = "NACK"
    WINDOW_UPDATE = "WINDOW_UPDATE"
    ERROR = "ERROR"
    FINISH = "FINISH"

class OperationMode(Enum):
    """Modos de operação para controle de fluxo"""
    GO_BACK_N = "GO_BACK_N"
    SELECTIVE_REPEAT = "SELECTIVE_REPEAT"

class ProtocolMessage:
    """Classe base para mensagens do protocolo"""
    
    def __init__(self, msg_type: MessageType, sequence: int = 0, 
                 payload: str = "", checksum: int = 0, 
                 window_size: int = 5, metadata: Optional[Dict[str, Any]] = None):
        self.msg_type = msg_type
        self.sequence = sequence
        self.payload = payload
        self.checksum = checksum
        self.window_size = window_size
        self.metadata = metadata or {}
        self.timestamp = None
    
    def to_bytes(self) -> bytes:
        """Converte a mensagem para bytes para transmissão"""
        message_data = {
            'type': self.msg_type.value,
            'sequence': self.sequence,
            'payload': self.payload,
            'checksum': self.checksum,
            'window_size': self.window_size,
            'metadata': self.metadata,
            'timestamp': self.timestamp
        }
        
        json_str = json.dumps(message_data)
        return json_str.encode('utf-8')
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'ProtocolMessage':
        """Cria uma mensagem a partir de bytes recebidos"""
        try:
            json_str = data.decode('utf-8')
            message_data = json.loads(json_str)
            
            return cls(
                msg_type=MessageType(message_data['type']),
                sequence=message_data['sequence'],
                payload=message_data['payload'],
                checksum=message_data['checksum'],
                window_size=message_data['window_size'],
                metadata=message_data.get('metadata', {})
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise ValueError(f"Erro ao decodificar mensagem: {e}")
    
    def __str__(self) -> str:
        return (f"ProtocolMessage(type={self.msg_type.value}, "
                f"seq={self.sequence}, payload='{self.payload}', "
                f"checksum={self.checksum}, window={self.window_size})")

class HandshakeRequest(ProtocolMessage):
    """Mensagem de handshake do cliente"""
    
    def __init__(self, max_message_size: int, operation_mode: OperationMode, 
                 encryption_enabled: bool = False):
        super().__init__(MessageType.HANDSHAKE_REQUEST)
        self.metadata = {
            'max_message_size': max_message_size,
            'operation_mode': operation_mode.value,
            'encryption_enabled': encryption_enabled
        }

class HandshakeResponse(ProtocolMessage):
    """Resposta do servidor ao handshake"""
    
    def __init__(self, accepted: bool, window_size: int = 5, 
                 operation_mode: OperationMode = OperationMode.GO_BACK_N,
                 error_message: str = ""):
        super().__init__(MessageType.HANDSHAKE_RESPONSE, window_size=window_size)
        self.metadata = {
            'accepted': accepted,
            'operation_mode': operation_mode.value,
            'error_message': error_message
        }

class DataMessage(ProtocolMessage):
    """Mensagem de dados"""
    
    def __init__(self, sequence: int, payload: str, checksum: int = 0,
                 is_final: bool = False):
        super().__init__(MessageType.DATA, sequence, payload, checksum)
        self.metadata['is_final'] = is_final

class AckMessage(ProtocolMessage):
    """Mensagem de reconhecimento positivo"""
    
    def __init__(self, sequence: int, window_size: int = 5):
        super().__init__(MessageType.ACK, sequence, window_size=window_size)

class NackMessage(ProtocolMessage):
    """Mensagem de reconhecimento negativo"""
    
    def __init__(self, sequence: int, error_code: str = "CHECKSUM_ERROR"):
        super().__init__(MessageType.NACK, sequence)
        self.metadata['error_code'] = error_code

class WindowUpdateMessage(ProtocolMessage):
    """Mensagem de atualização de janela"""
    
    def __init__(self, new_window_size: int):
        super().__init__(MessageType.WINDOW_UPDATE, window_size=new_window_size)

class ErrorMessage(ProtocolMessage):
    """Mensagem de erro"""
    
    def __init__(self, error_code: str, error_message: str):
        super().__init__(MessageType.ERROR)
        self.metadata = {
            'error_code': error_code,
            'error_message': error_message
        }

class FinishMessage(ProtocolMessage):
    """Mensagem de finalização"""
    
    def __init__(self):
        super().__init__(MessageType.FINISH)

# Constantes do protocolo
MAX_PAYLOAD_SIZE = 4  # Máximo 4 caracteres por pacote
MIN_MESSAGE_SIZE = 30  # Mínimo 30 caracteres por mensagem
DEFAULT_WINDOW_SIZE = 5
MAX_WINDOW_SIZE = 5
MIN_WINDOW_SIZE = 1
DEFAULT_TIMEOUT = 5.0  # 5 segundos
MAX_RETRIES = 3

# Códigos de erro
ERROR_CODES = {
    'CHECKSUM_ERROR': 'Erro na soma de verificação',
    'SEQUENCE_ERROR': 'Erro no número de sequência',
    'WINDOW_OVERFLOW': 'Janela de transmissão excedida',
    'INVALID_PAYLOAD': 'Carga útil inválida',
    'TIMEOUT': 'Timeout na transmissão',
    'CONNECTION_LOST': 'Conexão perdida',
    'INVALID_HANDSHAKE': 'Handshake inválido'
}

