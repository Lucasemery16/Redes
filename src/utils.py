"""
Utilitários para a aplicação de transporte confiável
Implementa checksum, criptografia e outras funções auxiliares
"""

import hashlib
import time
import random
from cryptography.fernet import Fernet
from typing import Optional, Tuple

def calculate_checksum(data: str) -> int:
    """
    Calcula a soma de verificação (checksum) para os dados
    
    Args:
        data: String com os dados para calcular o checksum
        
    Returns:
        int: Valor do checksum calculado
    """
    if not data:
        return 0
    
    # Usa MD5 para calcular o checksum
    hash_obj = hashlib.md5(data.encode('utf-8'))
    hash_hex = hash_obj.hexdigest()
    
    # Converte para inteiro usando os primeiros 8 caracteres
    return int(hash_hex[:8], 16)

def verify_checksum(data: str, expected_checksum: int) -> bool:
    """
    Verifica se o checksum dos dados está correto
    
    Args:
        data: String com os dados
        expected_checksum: Checksum esperado
        
    Returns:
        bool: True se o checksum estiver correto, False caso contrário
    """
    calculated_checksum = calculate_checksum(data)
    return calculated_checksum == expected_checksum

def introduce_error(data: str, error_type: str = "random") -> str:
    """
    Introduz um erro determinístico nos dados para simulação
    
    Args:
        data: String original
        error_type: Tipo de erro ("random", "bit_flip", "character_change")
        
    Returns:
        str: String com erro introduzido
    """
    if not data or len(data) == 0:
        return data
    
    if error_type == "random":
        # Muda um caractere aleatório
        pos = random.randint(0, len(data) - 1)
        new_char = chr((ord(data[pos]) + 1) % 256)
        return data[:pos] + new_char + data[pos + 1:]
    
    elif error_type == "bit_flip":
        # Simula um flip de bit
        pos = random.randint(0, len(data) - 1)
        char_code = ord(data[pos])
        # Flip do bit menos significativo
        new_char_code = char_code ^ 1
        new_char = chr(new_char_code)
        return data[:pos] + new_char + data[pos + 1:]
    
    elif error_type == "character_change":
        # Muda um caractere para um valor específico
        pos = random.randint(0, len(data) - 1)
        return data[:pos] + 'X' + data[pos + 1:]
    
    return data

def simulate_packet_loss(probability: float = 0.1) -> bool:
    """
    Simula perda de pacote baseada em probabilidade
    
    Args:
        probability: Probabilidade de perda (0.0 a 1.0)
        
    Returns:
        bool: True se o pacote deve ser perdido, False caso contrário
    """
    return random.random() < probability

class EncryptionManager:
    """Gerenciador de criptografia simétrica usando AES"""
    
    def __init__(self, key: Optional[bytes] = None):
        """
        Inicializa o gerenciador de criptografia
        
        Args:
            key: Chave de criptografia (se None, gera uma nova)
        """
        if key is None:
            self.key = Fernet.generate_key()
        else:
            self.key = key
        self.cipher = Fernet(self.key)
    
    def get_key(self) -> bytes:
        """Retorna a chave de criptografia"""
        return self.key
    
    def encrypt(self, data: str) -> str:
        """
        Criptografa os dados
        
        Args:
            data: String para criptografar
            
        Returns:
            str: Dados criptografados em base64
        """
        if not data:
            return ""
        
        encrypted_bytes = self.cipher.encrypt(data.encode('utf-8'))
        return encrypted_bytes.decode('utf-8')
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Descriptografa os dados
        
        Args:
            encrypted_data: Dados criptografados em base64
            
        Returns:
            str: Dados descriptografados
        """
        if not encrypted_data:
            return ""
        
        try:
            decrypted_bytes = self.cipher.decrypt(encrypted_data.encode('utf-8'))
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Erro ao descriptografar: {e}")

class Timer:
    """Classe para gerenciar temporizadores"""
    
    def __init__(self, timeout: float = 5.0):
        """
        Inicializa o temporizador
        
        Args:
            timeout: Tempo limite em segundos
        """
        self.timeout = timeout
        self.start_time = None
        self.is_running = False
    
    def start(self):
        """Inicia o temporizador"""
        self.start_time = time.time()
        self.is_running = True
    
    def stop(self):
        """Para o temporizador"""
        self.is_running = False
    
    def is_expired(self) -> bool:
        """
        Verifica se o temporizador expirou
        
        Returns:
            bool: True se expirou, False caso contrário
        """
        if not self.is_running or self.start_time is None:
            return False
        
        elapsed = time.time() - self.start_time
        return elapsed >= self.timeout
    
    def get_elapsed_time(self) -> float:
        """
        Retorna o tempo decorrido
        
        Returns:
            float: Tempo decorrido em segundos
        """
        if not self.is_running or self.start_time is None:
            return 0.0
        
        return time.time() - self.start_time
    
    def reset(self):
        """Reinicia o temporizador"""
        self.start_time = time.time()

def split_message(message: str, max_payload_size: int = 4) -> list:
    """
    Divide uma mensagem em pacotes menores
    
    Args:
        message: Mensagem completa
        max_payload_size: Tamanho máximo do payload por pacote
        
    Returns:
        list: Lista de strings com os pacotes
    """
    if not message:
        return []
    
    packets = []
    for i in range(0, len(message), max_payload_size):
        packet = message[i:i + max_payload_size]
        packets.append(packet)
    
    return packets

def format_metadata(sequence: int, payload: str, checksum: int, 
                   window_size: int, timestamp: Optional[float] = None) -> str:
    """
    Formata metadados para exibição
    
    Args:
        sequence: Número de sequência
        payload: Carga útil
        checksum: Soma de verificação
        window_size: Tamanho da janela
        timestamp: Timestamp (opcional)
        
    Returns:
        str: String formatada com os metadados
    """
    timestamp_str = f" [{timestamp:.3f}s]" if timestamp else ""
    return (f"Seq: {sequence:03d} | "
            f"Payload: '{payload}' | "
            f"Checksum: {checksum:08X} | "
            f"Window: {window_size}{timestamp_str}")

def log_message(direction: str, message_type: str, metadata: str):
    """
    Registra uma mensagem no log
    
    Args:
        direction: Direção da mensagem ("SEND", "RECV")
        message_type: Tipo da mensagem
        metadata: Metadados formatados
    """
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {direction} {message_type}: {metadata}")

def validate_message_size(message: str, min_size: int = 30) -> bool:
    """
    Valida se a mensagem atende ao tamanho mínimo
    
    Args:
        message: Mensagem para validar
        min_size: Tamanho mínimo
        
    Returns:
        bool: True se válida, False caso contrário
    """
    return len(message) >= min_size

def get_current_timestamp() -> float:
    """Retorna o timestamp atual"""
    return time.time()
