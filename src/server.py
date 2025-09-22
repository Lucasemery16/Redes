"""
Servidor da Aplicação de Transporte Confiável
Implementa o lado servidor da comunicação cliente-servidor
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
    simulate_packet_loss, EncryptionManager
)

class ReliableServer:
    """Servidor com transporte confiável"""
    
    def __init__(self, host: str = 'localhost', port: int = 8888):
        """
        Inicializa o servidor
        
        Args:
            host: Endereço do servidor
            port: Porta do servidor
        """
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        
        # Configurações do servidor
        self.max_message_size = 100  # Tamanho máximo de mensagem
        self.window_size = DEFAULT_WINDOW_SIZE
        self.operation_mode = OperationMode.GO_BACK_N
        self.encryption_enabled = False
        self.encryption_manager = None
        
        # Simulação de erros
        self.error_simulation = {
            'packet_loss_probability': 0.0,
            'error_introduction': False,
            'error_type': 'random'
        }
        
        # Clientes conectados
        self.clients: Dict[socket.socket, Dict[str, Any]] = {}
        
        # Estatísticas
        self.stats = {
            'total_connections': 0,
            'active_connections': 0,
            'messages_received': 0,
            'bytes_received': 0,
            'errors_detected': 0
        }
    
    def start(self):
        """Inicia o servidor"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            
            self.running = True
            print(f"🚀 Servidor iniciado em {self.host}:{self.port}")
            print(f"📊 Configurações:")
            print(f"   - Tamanho máximo de mensagem: {self.max_message_size} caracteres")
            print(f"   - Tamanho da janela: {self.window_size}")
            print(f"   - Modo de operação: {self.operation_mode.value}")
            print(f"   - Criptografia: {'Habilitada' if self.encryption_enabled else 'Desabilitada'}")
            print(f"   - Simulação de erros: {'Habilitada' if self.error_simulation['error_introduction'] else 'Desabilitada'}")
            print("-" * 50)
            
            # Thread principal para aceitar conexões
            accept_thread = threading.Thread(target=self._accept_connections, daemon=True)
            accept_thread.start()
            
            # Thread para monitoramento
            monitor_thread = threading.Thread(target=self._monitor_server, daemon=True)
            monitor_thread.start()
            
            # Aguarda comando do usuário
            self._handle_user_input()
            
        except Exception as e:
            print(f"❌ Erro ao iniciar servidor: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Para o servidor"""
        self.running = False
        
        # Fecha todas as conexões de clientes
        for client_socket in list(self.clients.keys()):
            try:
                client_socket.close()
            except:
                pass
        
        self.clients.clear()
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        
        print("🛑 Servidor parado")
    
    def _accept_connections(self):
        """Aceita novas conexões de clientes"""
        while self.running:
            try:
                client_socket, client_address = self.socket.accept()
                print(f"🔗 Nova conexão de {client_address}")
                
                # Inicializa dados do cliente
                self.clients[client_socket] = {
                    'address': client_address,
                    'transport': None,
                    'message_buffer': '',
                    'handshake_completed': False,
                    'connected_time': time.time()
                }
                
                self.stats['total_connections'] += 1
                self.stats['active_connections'] += 1
                
                # Thread para tratar o cliente
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket,),
                    daemon=True
                )
                client_thread.start()
                
            except Exception as e:
                if self.running:
                    print(f"❌ Erro ao aceitar conexão: {e}")
    
    def _handle_client(self, client_socket: socket.socket):
        """Trata comunicação com um cliente específico"""
        client_data = self.clients[client_socket]
        
        try:
            while self.running:
                # Recebe dados do cliente
                data = client_socket.recv(4096)
                if not data:
                    break
                
                # Simula perda de pacote se habilitado
                if simulate_packet_loss(self.error_simulation['packet_loss_probability']):
                    print(f"📦 Pacote perdido (simulação) de {client_data['address']}")
                    continue
                
                try:
                    # Decodifica mensagem
                    message = ProtocolMessage.from_bytes(data)
                    self._process_message(client_socket, message)
                    
                except Exception as e:
                    print(f"❌ Erro ao processar mensagem de {client_data['address']}: {e}")
                    self.stats['errors_detected'] += 1
        
        except Exception as e:
            print(f"❌ Erro na comunicação com {client_data['address']}: {e}")
        
        finally:
            # Remove cliente
            if client_socket in self.clients:
                del self.clients[client_socket]
            self.stats['active_connections'] -= 1
            client_socket.close()
            print(f"🔌 Cliente {client_data['address']} desconectado")
    
    def _process_message(self, client_socket: socket.socket, message: ProtocolMessage):
        """Processa mensagem recebida do cliente"""
        client_data = self.clients[client_socket]
        
        if message.msg_type == MessageType.HANDSHAKE_REQUEST:
            self._handle_handshake(client_socket, message)
        
        elif message.msg_type == MessageType.DATA:
            self._handle_data_message(client_socket, message)
        
        elif message.msg_type in [MessageType.ACK, MessageType.NACK, MessageType.WINDOW_UPDATE]:
            # Processa através do transporte confiável
            if client_data['transport']:
                client_data['transport'].receive_message(message)
    
    def _handle_handshake(self, client_socket: socket.socket, message: HandshakeRequest):
        """Processa handshake do cliente"""
        client_data = self.clients[client_socket]
        
        try:
            # Extrai parâmetros do handshake
            max_message_size = message.metadata.get('max_message_size', 30)
            operation_mode_str = message.metadata.get('operation_mode', 'GO_BACK_N')
            encryption_enabled = message.metadata.get('encryption_enabled', False)
            
            # Valida parâmetros
            if max_message_size < 30:
                response = HandshakeResponse(
                    accepted=False,
                    error_message="Tamanho mínimo de mensagem é 30 caracteres"
                )
            else:
                # Configura transporte confiável
                operation_mode = OperationMode(operation_mode_str)
                transport = ReliableTransport(
                    operation_mode=operation_mode,
                    window_size=self.window_size
                )
                
                # Configura callbacks
                transport.set_send_callback(lambda msg: self._send_to_client(client_socket, msg))
                transport.set_receive_callback(lambda msg: self._on_data_received(client_socket, msg))
                
                transport.start()
                
                # Atualiza dados do cliente
                client_data['transport'] = transport
                client_data['handshake_completed'] = True
                client_data['max_message_size'] = max_message_size
                client_data['operation_mode'] = operation_mode
                
                # Configura criptografia se solicitado
                if encryption_enabled:
                    self.encryption_manager = EncryptionManager()
                    client_data['encryption_enabled'] = True
                    client_data['encryption_key'] = self.encryption_manager.get_key()
                
                response = HandshakeResponse(
                    accepted=True,
                    window_size=self.window_size,
                    operation_mode=operation_mode
                )
                
                print(f"✅ Handshake aceito para {client_data['address']}")
                print(f"   - Tamanho máximo: {max_message_size}")
                print(f"   - Modo: {operation_mode.value}")
                print(f"   - Janela: {self.window_size}")
                print(f"   - Criptografia: {'Sim' if encryption_enabled else 'Não'}")
            
            # Envia resposta
            self._send_to_client(client_socket, response)
            
        except Exception as e:
            print(f"❌ Erro no handshake com {client_data['address']}: {e}")
            response = HandshakeResponse(
                accepted=False,
                error_message=f"Erro interno: {str(e)}"
            )
            self._send_to_client(client_socket, response)
    
    def _handle_data_message(self, client_socket: socket.socket, message: DataMessage):
        """Processa mensagem de dados"""
        client_data = self.clients[client_socket]
        
        if not client_data['handshake_completed']:
            print(f"⚠️  Dados recebidos antes do handshake de {client_data['address']}")
            return
        
        # Processa através do transporte confiável
        if client_data['transport']:
            client_data['transport'].receive_message(message)
    
    def _on_data_received(self, client_socket: socket.socket, message: DataMessage):
        """Callback chamado quando dados são recebidos com sucesso"""
        client_data = self.clients[client_socket]
        
        # Adiciona à mensagem completa
        client_data['message_buffer'] += message.payload
        self.stats['messages_received'] += 1
        self.stats['bytes_received'] += len(message.payload)
        
        # Exibe metadados
        timestamp = get_current_timestamp()
        metadata = format_metadata(
            message.sequence,
            message.payload,
            message.checksum,
            client_data['transport'].window_size,
            timestamp
        )
        print(f"📨 {metadata}")
        
        # Se é o último pacote, exibe mensagem completa
        if message.metadata.get('is_final', False):
            complete_message = client_data['message_buffer']
            
            # Descriptografa se necessário
            if client_data.get('encryption_enabled', False):
                try:
                    complete_message = self.encryption_manager.decrypt(complete_message)
                except Exception as e:
                    print(f"❌ Erro ao descriptografar: {e}")
                    return
            
            print(f"📝 Mensagem completa recebida de {client_data['address']}:")
            print(f"   '{complete_message}'")
            print(f"   Tamanho: {len(complete_message)} caracteres")
            print("-" * 50)
            
            # Limpa buffer
            client_data['message_buffer'] = ''
    
    def _send_to_client(self, client_socket: socket.socket, message: ProtocolMessage):
        """Envia mensagem para o cliente"""
        try:
            data = message.to_bytes()
            client_socket.send(data)
            
            # Log da mensagem enviada
            if message.msg_type == MessageType.ACK:
                log_message("SEND", "ACK", f"Seq: {message.sequence:03d}")
            elif message.msg_type == MessageType.NACK:
                log_message("SEND", "NACK", f"Seq: {message.sequence:03d}")
            elif message.msg_type == MessageType.HANDSHAKE_RESPONSE:
                log_message("SEND", "HANDSHAKE_RESP", f"Accepted: {message.metadata.get('accepted', False)}")
            
        except Exception as e:
            print(f"❌ Erro ao enviar mensagem para {self.clients[client_socket]['address']}: {e}")
    
    def _monitor_server(self):
        """Monitora o servidor e exibe estatísticas"""
        while self.running:
            time.sleep(30)  # Atualiza a cada 30 segundos
            if self.running:
                self._display_stats()
    
    def _display_stats(self):
        """Exibe estatísticas do servidor"""
        print("\n📊 Estatísticas do Servidor:")
        print(f"   - Conexões totais: {self.stats['total_connections']}")
        print(f"   - Conexões ativas: {self.stats['active_connections']}")
        print(f"   - Mensagens recebidas: {self.stats['messages_received']}")
        print(f"   - Bytes recebidos: {self.stats['bytes_received']}")
        print(f"   - Erros detectados: {self.stats['errors_detected']}")
        print("-" * 50)
    
    def _handle_user_input(self):
        """Trata entrada do usuário para comandos do servidor"""
        print("\n💡 Comandos disponíveis:")
        print("   - 'stats': Exibe estatísticas")
        print("   - 'clients': Lista clientes conectados")
        print("   - 'config': Exibe configurações")
        print("   - 'error <prob>': Define probabilidade de perda de pacotes (0.0-1.0)")
        print("   - 'window <size>': Define tamanho da janela (1-5)")
        print("   - 'mode <GO_BACK_N|SELECTIVE_REPEAT>': Define modo de operação")
        print("   - 'quit': Para o servidor")
        print()
        
        while self.running:
            try:
                command = input("servidor> ").strip().lower()
                
                if command == 'quit':
                    break
                elif command == 'stats':
                    self._display_stats()
                elif command == 'clients':
                    self._list_clients()
                elif command == 'config':
                    self._display_config()
                elif command.startswith('error '):
                    self._set_error_probability(command)
                elif command.startswith('window '):
                    self._set_window_size(command)
                elif command.startswith('mode '):
                    self._set_operation_mode(command)
                else:
                    print("❌ Comando inválido")
            
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Erro no comando: {e}")
    
    def _list_clients(self):
        """Lista clientes conectados"""
        if not self.clients:
            print("📭 Nenhum cliente conectado")
            return
        
        print("👥 Clientes conectados:")
        for client_socket, client_data in self.clients.items():
            uptime = time.time() - client_data['connected_time']
            print(f"   - {client_data['address']} (conectado há {uptime:.1f}s)")
    
    def _display_config(self):
        """Exibe configurações do servidor"""
        print("⚙️  Configurações do servidor:")
        print(f"   - Host: {self.host}")
        print(f"   - Porta: {self.port}")
        print(f"   - Tamanho máximo de mensagem: {self.max_message_size}")
        print(f"   - Tamanho da janela: {self.window_size}")
        print(f"   - Modo de operação: {self.operation_mode.value}")
        print(f"   - Probabilidade de perda: {self.error_simulation['packet_loss_probability']}")
    
    def _set_error_probability(self, command: str):
        """Define probabilidade de erro"""
        try:
            parts = command.split()
            if len(parts) != 2:
                print("❌ Uso: error <probabilidade>")
                return
            
            prob = float(parts[1])
            if 0.0 <= prob <= 1.0:
                self.error_simulation['packet_loss_probability'] = prob
                print(f"✅ Probabilidade de perda definida para {prob}")
            else:
                print("❌ Probabilidade deve estar entre 0.0 e 1.0")
        
        except ValueError:
            print("❌ Probabilidade deve ser um número")
    
    def _set_window_size(self, command: str):
        """Define tamanho da janela"""
        try:
            parts = command.split()
            if len(parts) != 2:
                print("❌ Uso: window <tamanho>")
                return
            
            size = int(parts[1])
            if MIN_WINDOW_SIZE <= size <= MAX_WINDOW_SIZE:
                self.window_size = size
                print(f"✅ Tamanho da janela definido para {size}")
            else:
                print(f"❌ Tamanho da janela deve estar entre {MIN_WINDOW_SIZE} e {MAX_WINDOW_SIZE}")
        
        except ValueError:
            print("❌ Tamanho deve ser um número inteiro")
    
    def _set_operation_mode(self, command: str):
        """Define modo de operação"""
        try:
            parts = command.split()
            if len(parts) != 2:
                print("❌ Uso: mode <GO_BACK_N|SELECTIVE_REPEAT>")
                return
            
            mode_str = parts[1].upper()
            if mode_str in ['GO_BACK_N', 'SELECTIVE_REPEAT']:
                self.operation_mode = OperationMode(mode_str)
                print(f"✅ Modo de operação definido para {mode_str}")
            else:
                print("❌ Modo deve ser GO_BACK_N ou SELECTIVE_REPEAT")
        
        except ValueError:
            print("❌ Modo inválido")

def main():
    """Função principal do servidor"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Servidor de Transporte Confiável')
    parser.add_argument('--host', default='localhost', help='Endereço do servidor')
    parser.add_argument('--port', type=int, default=8888, help='Porta do servidor')
    
    args = parser.parse_args()
    
    server = ReliableServer(args.host, args.port)
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n🛑 Servidor interrompido pelo usuário")
    finally:
        server.stop()

if __name__ == "__main__":
    main()

