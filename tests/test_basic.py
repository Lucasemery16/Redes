"""
Testes básicos para a aplicação de transporte confiável
"""

import unittest
import sys
import os

# Adiciona o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from protocol import ProtocolMessage, MessageType, DataMessage, calculate_checksum
from utils import calculate_checksum as utils_checksum, verify_checksum, split_message

class TestProtocol(unittest.TestCase):
    """Testes para o protocolo de aplicação"""
    
    def test_message_creation(self):
        """Testa criação de mensagem"""
        message = DataMessage(sequence=1, payload="test", checksum=12345)
        self.assertEqual(message.sequence, 1)
        self.assertEqual(message.payload, "test")
        self.assertEqual(message.checksum, 12345)
        self.assertEqual(message.msg_type, MessageType.DATA)
    
    def test_message_serialization(self):
        """Testa serialização/deserialização de mensagem"""
        original = DataMessage(sequence=1, payload="test", checksum=12345)
        data = original.to_bytes()
        restored = ProtocolMessage.from_bytes(data)
        
        self.assertEqual(original.sequence, restored.sequence)
        self.assertEqual(original.payload, restored.payload)
        self.assertEqual(original.checksum, restored.checksum)
        self.assertEqual(original.msg_type, restored.msg_type)

class TestUtils(unittest.TestCase):
    """Testes para utilitários"""
    
    def test_checksum_calculation(self):
        """Testa cálculo de checksum"""
        data = "test data"
        checksum = calculate_checksum(data)
        self.assertIsInstance(checksum, int)
        self.assertGreater(checksum, 0)
    
    def test_checksum_verification(self):
        """Testa verificação de checksum"""
        data = "test data"
        checksum = calculate_checksum(data)
        
        # Checksum correto
        self.assertTrue(verify_checksum(data, checksum))
        
        # Checksum incorreto
        self.assertFalse(verify_checksum(data, checksum + 1))
    
    def test_message_splitting(self):
        """Testa divisão de mensagens"""
        message = "Esta é uma mensagem de teste"
        packets = split_message(message, 4)
        
        # Verifica que todos os pacotes têm no máximo 4 caracteres
        for packet in packets:
            self.assertLessEqual(len(packet), 4)
        
        # Verifica que a mensagem original pode ser reconstruída
        reconstructed = "".join(packets)
        self.assertEqual(message, reconstructed)

if __name__ == '__main__':
    unittest.main()
