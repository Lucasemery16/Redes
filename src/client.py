"""
Cliente da Aplicação de Transporte Confiável
Implementa o lado cliente da comunicação cliente-servidor
"""

import socket
import threading
import time
import sys
from typing import Optional, Dict, Any

from protocol import (
    ProtocolMessage, MessageType, OperationMode, 
    HandshakeRequest, HandshakeResponse, DataMessage,
    AckMessage, NackMessage, WindowUpdateMessage,
    DEFAULT_WINDOW_SIZE, MAX_WINDOW_SIZE, MIN_WINDOW_SIZE
)
from reliable_transport import ReliableTransport
from utils import (
    split_message, format_metadata, log_message, 
    validate_message_size, get_current_timestamp,
    introduce_error, EncryptionManager
)

class ReliableClient:
    """Cliente com transporte confiável"""
    
    def __init__(self, host: str = 'localhost', port: int = 8888):
        """
        Inicializa o cliente
        
        Args:
            host: Endereço do servidor
            port: Porta do servidor
        """
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        
        # Configurações do cliente
        self.max_message_size = 100
        self.operation_mode = OperationMode.GO_BACK_N
        self.encryption_enabled = False
        self.encryption_manager = None
        
        # Transporte confiável
        self.transport: Optional[ReliableTransport] = None
        
        # Simulação de erros
        self.error_simulation = {
            'enabled': False,
            'error_type': 'random',
            'error_probability': 0.1
        }
        
        # Buffer de mensagens
        self.message_queue = []
        self.current_message = ""
        
        # Estatísticas
        self.stats = {
            'messages_sent': 0,
            'packets_sent': 0,
            'bytes_sent': 0,
            'retransmissions': 0,
            'errors_introduced': 0
        }
    
    def connect(self) -> bool:
        """
        Conecta ao servidor
        
        Returns:
            bool: True se conectado com sucesso
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            
            print(f"🔗 Conectado ao servidor {self.host}:{self.port}")
            
            # Thread para receber mensagens
            receive_thread = threading.Thread(target=self._receive_messages, daemon=True)
            receive_thread.start()
            
            # Realiza handshake
            return self._perform_handshake()
            
        except Exception as e:
            print(f"❌ Erro ao conectar: {e}")
            return False
    
    def disconnect(self):
        """Desconecta do servidor"""
        self.connected = False
        
        if self.transport:
            self.transport.stop()
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        
        print("🔌 Desconectado do servidor")
    
    def _perform_handshake(self) -> bool:
        """
        Realiza handshake com o servidor
        
        Returns:
            bool: True se handshake bem-sucedido
        """
        try:
            # Cria requisição de handshake
            # Se criptografia habilitada, garante gerenciador e envia chave no handshake
            encryption_key_str = None
            if self.encryption_enabled:
                if not self.encryption_manager:
                    self.encryption_manager = EncryptionManager()
                encryption_key_str = self.encryption_manager.get_key().decode('utf-8')
            
            handshake_request = HandshakeRequest(
                max_message_size=self.max_message_size,
                operation_mode=self.operation_mode,
                encryption_enabled=self.encryption_enabled,
                encryption_key=encryption_key_str
            )
            
            # Envia handshake
            self._send_message(handshake_request)
            print(f"📤 Handshake enviado:")
            print(f"   - Tamanho máximo: {self.max_message_size}")
            print(f"   - Modo: {self.operation_mode.value}")
            print(f"   - Criptografia: {'Sim' if self.encryption_enabled else 'Não'}")
            
            # Aguarda resposta (timeout de 10 segundos)
            start_time = time.time()
            while time.time() - start_time < 10:
                if hasattr(self, '_handshake_response'):
                    response = self._handshake_response
                    delattr(self, '_handshake_response')
                    
                    if response.metadata.get('accepted', False):
                        # Configura transporte confiável
                        window_size = response.window_size
                        operation_mode = OperationMode(response.metadata.get('operation_mode', 'GO_BACK_N'))
                        
                        self.transport = ReliableTransport(
                            operation_mode=operation_mode,
                            window_size=window_size
                        )
                        
                        # Configura callbacks
                        self.transport.set_send_callback(self._send_message)
                        self.transport.set_receive_callback(self._on_ack_received)
                        
                        self.transport.start()
                        
                        print(f"✅ Handshake aceito pelo servidor:")
                        print(f"   - Janela: {window_size}")
                        print(f"   - Modo: {operation_mode.value}")
                        print("-" * 50)
                        
                        return True
                    else:
                        error_msg = response.metadata.get('error_message', 'Erro desconhecido')
                        print(f"❌ Handshake rejeitado: {error_msg}")
                        return False
                
                time.sleep(0.1)
            
            print("❌ Timeout no handshake")
            return False
            
        except Exception as e:
            print(f"❌ Erro no handshake: {e}")
            return False
    
    def send_message(self, message: str) -> bool:
        """
        Envia uma mensagem para o servidor
        
        Args:
            message: Mensagem para enviar
            
        Returns:
            bool: True se enviada com sucesso
        """
        if not self.connected or not self.transport:
            print("❌ Cliente não conectado")
            return False
        
        # Valida tamanho da mensagem
        if not validate_message_size(message, 30):
            print(f"❌ Mensagem muito pequena (mínimo 30 caracteres, recebidos {len(message)})")
            return False
        
        if len(message) > self.max_message_size:
            print(f"❌ Mensagem muito grande (máximo {self.max_message_size} caracteres, recebidos {len(message)})")
            return False
        
        try:
            # Criptografa se necessário
            if self.encryption_enabled and self.encryption_manager:
                message = self.encryption_manager.encrypt(message)
            
            # Divide mensagem em pacotes
            packets = split_message(message, 4)  # Máximo 4 caracteres por pacote
            
            print(f"📤 Enviando mensagem: '{message[:50]}{'...' if len(message) > 50 else ''}'")
            print(f"   - Tamanho: {len(message)} caracteres")
            print(f"   - Pacotes: {len(packets)}")
            print("-" * 50)
            
            # Envia cada pacote
            for i, packet in enumerate(packets):
                is_final = (i == len(packets) - 1)
                
                # Simula erro se habilitado
                if self.error_simulation['enabled']:
                    if self._should_introduce_error():
                        packet = introduce_error(packet, self.error_simulation['error_type'])
                        self.stats['errors_introduced'] += 1
                        print(f"⚠️  Erro introduzido no pacote {i+1}")
                
                # Envia pacote através do transporte confiável
                success = self.transport.send_data(packet, is_final)
                if not success:
                    print(f"❌ Falha ao enviar pacote {i+1} (janela cheia)")
                    return False
                
                self.stats['packets_sent'] += 1
                self.stats['bytes_sent'] += len(packet)
                
                # Pequena pausa entre pacotes
                time.sleep(0.1)
            
            self.stats['messages_sent'] += 1
            print(f"✅ Mensagem enviada com sucesso ({len(packets)} pacotes)")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao enviar mensagem: {e}")
            return False
    
    def _should_introduce_error(self) -> bool:
        """Determina se deve introduzir erro baseado na probabilidade"""
        import random
        return random.random() < self.error_simulation['error_probability']
    
    def _send_message(self, message: ProtocolMessage):
        """Envia mensagem para o servidor"""
        try:
            data = message.to_bytes()
            self.socket.send(data)
            
            # Log da mensagem enviada
            if message.msg_type == MessageType.DATA:
                log_message("SEND", "DATA", f"Seq: {message.sequence:03d} | Payload: '{message.payload}'")
            elif message.msg_type == MessageType.ACK:
                log_message("SEND", "ACK", f"Seq: {message.sequence:03d}")
            elif message.msg_type == MessageType.NACK:
                log_message("SEND", "NACK", f"Seq: {message.sequence:03d}")
            
        except Exception as e:
            print(f"❌ Erro ao enviar mensagem: {e}")
    
    def _receive_messages(self):
        """Recebe mensagens do servidor"""
        while self.connected:
            try:
                data = self.socket.recv(4096)
                if not data:
                    break
                
                # Decodifica mensagem
                message = ProtocolMessage.from_bytes(data)
                self._process_received_message(message)
                
            except Exception as e:
                if self.connected:
                    print(f"❌ Erro ao receber mensagem: {e}")
                break
    
    def _process_received_message(self, message: ProtocolMessage):
        """Processa mensagem recebida do servidor"""
        if message.msg_type == MessageType.HANDSHAKE_RESPONSE:
            self._handshake_response = message
        
        elif message.msg_type in [MessageType.ACK, MessageType.NACK, MessageType.WINDOW_UPDATE]:
            # Processa através do transporte confiável
            if self.transport:
                self.transport.receive_message(message)
    
    def _on_ack_received(self, message: ProtocolMessage):
        """Callback chamado quando ACK é recebido"""
        if message.msg_type == MessageType.ACK:
            log_message("RECV", "ACK", f"Seq: {message.sequence:03d}")
        elif message.msg_type == MessageType.NACK:
            log_message("RECV", "NACK", f"Seq: {message.sequence:03d}")
            self.stats['retransmissions'] += 1
    
    def set_error_simulation(self, enabled: bool, error_type: str = 'random', probability: float = 0.1):
        """
        Configura simulação de erros
        
        Args:
            enabled: Se a simulação está habilitada
            error_type: Tipo de erro ('random', 'bit_flip', 'character_change')
            probability: Probabilidade de erro (0.0-1.0)
        """
        self.error_simulation = {
            'enabled': enabled,
            'error_type': error_type,
            'error_probability': probability
        }
        
        status = "habilitada" if enabled else "desabilitada"
        print(f"🔧 Simulação de erros {status}")
        if enabled:
            print(f"   - Tipo: {error_type}")
            print(f"   - Probabilidade: {probability}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cliente"""
        transport_stats = self.transport.get_stats() if self.transport else {}
        return {
            **self.stats,
            **transport_stats
        }
    
    def display_stats(self):
        """Exibe estatísticas do cliente"""
        stats = self.get_stats()
        print("\n📊 Estatísticas do Cliente:")
        print(f"   - Mensagens enviadas: {stats.get('messages_sent', 0)}")
        print(f"   - Pacotes enviados: {stats.get('packets_sent', 0)}")
        print(f"   - Bytes enviados: {stats.get('bytes_sent', 0)}")
        print(f"   - Retransmissões: {stats.get('retransmissions', 0)}")
        print(f"   - Erros introduzidos: {stats.get('errors_introduced', 0)}")
        print(f"   - Pacotes pendentes: {stats.get('pending_packets', 0)}")
        print(f"   - Tamanho da janela: {stats.get('window_size', 0)}")
        print(f"   - Modo de operação: {stats.get('operation_mode', 'N/A')}")

def main():
    """Função principal do cliente"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Cliente de Transporte Confiável')
    parser.add_argument('host', nargs='?', default='localhost', help='Endereço do servidor')
    parser.add_argument('port', nargs='?', type=int, default=8888, help='Porta do servidor')
    parser.add_argument('--max-size', type=int, default=100, help='Tamanho máximo de mensagem')
    parser.add_argument('--mode', choices=['GO_BACK_N', 'SELECTIVE_REPEAT'], 
                       default='GO_BACK_N', help='Modo de operação')
    parser.add_argument('--encrypt', action='store_true', help='Habilitar criptografia')
    parser.add_argument('--error-sim', action='store_true', help='Habilitar simulação de erros')
    parser.add_argument('--error-type', choices=['random', 'bit_flip', 'character_change'],
                       default='random', help='Tipo de erro para simulação')
    parser.add_argument('--error-prob', type=float, default=0.1, 
                       help='Probabilidade de erro (0.0-1.0)')
    
    args = parser.parse_args()
    
    client = ReliableClient(args.host, args.port)
    
    # Configurações do cliente
    client.max_message_size = args.max_size
    client.operation_mode = OperationMode(args.mode)
    client.encryption_enabled = args.encrypt
    
    if args.encrypt:
        client.encryption_manager = EncryptionManager()
    
    if args.error_sim:
        client.set_error_simulation(True, args.error_type, args.error_prob)
    
    try:
        # Conecta ao servidor
        if not client.connect():
            print("❌ Falha na conexão")
            return
        
        print("\n💡 Comandos disponíveis:")
        print("   - Digite uma mensagem para enviar")
        print("   - 'stats': Exibe estatísticas")
        print("   - 'error <on|off>': Liga/desliga simulação de erros")
        print("   - 'quit': Desconecta e sai")
        print()
        
        # Loop principal
        while client.connected:
            try:
                user_input = input("cliente> ").strip()
                
                if user_input.lower() == 'quit':
                    break
                elif user_input.lower() == 'stats':
                    client.display_stats()
                elif user_input.startswith('error '):
                    parts = user_input.split()
                    if len(parts) == 2:
                        enabled = parts[1].lower() == 'on'
                        client.set_error_simulation(enabled)
                    else:
                        print("❌ Uso: error <on|off>")
                elif user_input:
                    # Envia mensagem
                    client.send_message(user_input)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Erro: {e}")
    
    except KeyboardInterrupt:
        print("\n🛑 Cliente interrompido pelo usuário")
    finally:
        client.disconnect()

if __name__ == "__main__":
    main()
