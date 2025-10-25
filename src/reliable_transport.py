"""
Módulo de Transporte Confiável
Implementa as características de transporte confiável de dados
"""

import time
import threading
from typing import Dict, List, Optional, Callable, Any
from collections import deque
from dataclasses import dataclass

from protocol import (
    ProtocolMessage, MessageType, OperationMode, 
    DataMessage, AckMessage, NackMessage, WindowUpdateMessage,
    DEFAULT_TIMEOUT, MAX_RETRIES
)
from utils import Timer, calculate_checksum, verify_checksum, log_message

@dataclass
class PendingPacket:
    """Representa um pacote pendente de confirmação"""
    message: ProtocolMessage
    timestamp: float
    retry_count: int = 0

class ReliableTransport:
    """Implementa transporte confiável com janela deslizante"""
    
    def __init__(self, operation_mode: OperationMode = OperationMode.GO_BACK_N,
                 window_size: int = 5, timeout: float = DEFAULT_TIMEOUT):
        """
        Inicializa o transporte confiável
        
        Args:
            operation_mode: Modo de operação (Go-Back-N ou Selective Repeat)
            window_size: Tamanho da janela
            timeout: Timeout para retransmissão
        """
        self.operation_mode = operation_mode
        self.window_size = window_size
        self.timeout = timeout
        
        # Controle de sequência
        self.next_seq_num = 0
        self.expected_seq_num = 0
        
        # Janela deslizante
        self.window_start = 0
        self.window_end = window_size - 1
        
        # Pacotes pendentes
        self.pending_packets: Dict[int, PendingPacket] = {}
        self.received_packets: Dict[int, ProtocolMessage] = {}
        
        # Timers
        self.timers: Dict[int, Timer] = {}
        
        # Callbacks
        self.send_callback: Optional[Callable[[ProtocolMessage], None]] = None
        self.receive_callback: Optional[Callable[[ProtocolMessage], None]] = None
        
        # Thread para monitoramento de timeouts
        self.monitor_thread = None
        self.running = False
        
        # Estatísticas
        self.stats = {
            'packets_sent': 0,
            'packets_received': 0,
            'retransmissions': 0,
            'errors_detected': 0,
            'duplicate_packets': 0
        }
    
    def start(self):
        """Inicia o transporte confiável"""
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_timeouts, daemon=True)
        self.monitor_thread.start()
    
    def stop(self):
        """Para o transporte confiável"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
    
    def set_send_callback(self, callback: Callable[[ProtocolMessage], None]):
        """Define callback para envio de mensagens"""
        self.send_callback = callback
    
    def set_receive_callback(self, callback: Callable[[ProtocolMessage], None]):
        """Define callback para recebimento de mensagens"""
        self.receive_callback = callback
    
    def send_data(self, payload: str, is_final: bool = False) -> bool:
        """
        Envia dados usando transporte confiável
        
        Args:
            payload: Dados para enviar
            is_final: Se é o último pacote da mensagem
            
        Returns:
            bool: True se enviado com sucesso, False se janela cheia
        """
        if not self._can_send():
            return False
        
        # Calcula checksum
        checksum = calculate_checksum(payload)
        
        # Cria mensagem de dados
        message = DataMessage(
            sequence=self.next_seq_num,
            payload=payload,
            checksum=checksum,
            is_final=is_final
        )
        
        # Adiciona aos pacotes pendentes
        self.pending_packets[self.next_seq_num] = PendingPacket(
            message=message,
            timestamp=time.time()
        )
        
        # Cria e inicia timer
        timer = Timer(self.timeout)
        timer.start()
        self.timers[self.next_seq_num] = timer
        
        # Envia mensagem
        if self.send_callback:
            self.send_callback(message)
            self.stats['packets_sent'] += 1
            log_message("SEND", "DATA", f"Seq: {self.next_seq_num:03d} | Payload: '{payload}' | Checksum: {checksum:08X}")
        
        # Atualiza número de sequência
        self.next_seq_num = (self.next_seq_num + 1) % 1000  # Wrap around em 1000
        
        return True
    
    def receive_message(self, message: ProtocolMessage) -> bool:
        """
        Processa mensagem recebida
        
        Args:
            message: Mensagem recebida
            
        Returns:
            bool: True se processada com sucesso
        """
        if message.msg_type == MessageType.DATA:
            return self._handle_data_message(message)
        elif message.msg_type == MessageType.ACK:
            return self._handle_ack_message(message)
        elif message.msg_type == MessageType.NACK:
            return self._handle_nack_message(message)
        elif message.msg_type == MessageType.WINDOW_UPDATE:
            return self._handle_window_update(message)
        
        return False
    
    def _handle_data_message(self, message: DataMessage) -> bool:
        """Processa mensagem de dados recebida"""
        seq_num = message.sequence
        
        # Verifica checksum
        if not verify_checksum(message.payload, message.checksum):
            self.stats['errors_detected'] += 1
            nack = NackMessage(seq_num, "CHECKSUM_ERROR")
            if self.send_callback:
                self.send_callback(nack)
            return False
        
        # Verifica se é duplicata
        if seq_num in self.received_packets:
            self.stats['duplicate_packets'] += 1
            # Reenvia ACK para duplicata
            ack = AckMessage(seq_num, self.window_size)
            if self.send_callback:
                self.send_callback(ack)
            return True
        
        # Armazena pacote recebido
        self.received_packets[seq_num] = message
        self.stats['packets_received'] += 1
        
        # Envia ACK
        ack = AckMessage(seq_num, self.window_size)
        if self.send_callback:
            self.send_callback(ack)
        
        log_message("RECV", "DATA", f"Seq: {seq_num:03d} | Payload: '{message.payload}' | Checksum: {message.checksum:08X}")
        
        # Processa pacotes em ordem se Go-Back-N
        if self.operation_mode == OperationMode.GO_BACK_N:
            self._process_ordered_packets()
        
        # Chama callback de recebimento
        if self.receive_callback:
            self.receive_callback(message)
        
        return True
    
    def _handle_ack_message(self, message: AckMessage) -> bool:
        """Processa mensagem de ACK"""
        seq_num = message.sequence
        
        if seq_num in self.pending_packets:
            # Remove pacote dos pendentes
            del self.pending_packets[seq_num]
            
            # Para timer
            if seq_num in self.timers:
                self.timers[seq_num].stop()
                del self.timers[seq_num]
            
            # Atualiza janela
            self._update_window()
            
            log_message("RECV", "ACK", f"Seq: {seq_num:03d} | Window: {message.window_size}")
        
        # Se todos os pacotes da janela atual foram confirmados, imprime acknowledge resumido
        # para simular "ACK1 e 2", "ACK3 e 4", etc.
        if self.operation_mode == OperationMode.GO_BACK_N:
            try:
                # Determina o tamanho da janela atual
                win_size = max(1, self.window_size)
                # O último ack recebido pertence ao bloco (seq // win_size)
                last_block_end = ((seq_num // win_size) + 1) * win_size - 1
                # Se não há pendentes neste bloco, podemos imprimir um resumo
                block_start = (seq_num // win_size) * win_size
                block_done = all(((n not in self.pending_packets) for n in range(block_start, last_block_end + 1)))
                if block_done:
                    print(f"← ACK {block_start+1} e {last_block_end+1}")
            except Exception:
                pass
        
        return True
    
    def _handle_nack_message(self, message: NackMessage) -> bool:
        """Processa mensagem de NACK"""
        seq_num = message.sequence
        
        if seq_num in self.pending_packets:
            # Retransmite pacote
            self._retransmit_packet(seq_num)
            log_message("RECV", "NACK", f"Seq: {seq_num:03d} | Error: {message.metadata.get('error_code', 'UNKNOWN')}")
        
        return True
    
    def _handle_window_update(self, message: WindowUpdateMessage) -> bool:
        """Processa atualização de janela"""
        old_window_size = self.window_size
        self.window_size = message.window_size
        self._update_window()
        
        log_message("RECV", "WINDOW_UPDATE", f"Old: {old_window_size} | New: {self.window_size}")
        return True
    
    def _can_send(self) -> bool:
        """Verifica se pode enviar mais pacotes"""
        return len(self.pending_packets) < self.window_size
    
    def _update_window(self):
        """Atualiza a janela deslizante"""
        if self.operation_mode == OperationMode.GO_BACK_N:
            # Go-Back-N: move janela quando recebe ACK do primeiro pacote
            while self.window_start in self.pending_packets:
                del self.pending_packets[self.window_start]
                if self.window_start in self.timers:
                    self.timers[self.window_start].stop()
                    del self.timers[self.window_start]
                self.window_start = (self.window_start + 1) % 1000
        
        elif self.operation_mode == OperationMode.SELECTIVE_REPEAT:
            # Selective Repeat: move janela baseado em ACKs recebidos
            # Implementação mais complexa seria necessária aqui
            pass
    
    def _process_ordered_packets(self):
        """Processa pacotes em ordem para Go-Back-N"""
        while self.expected_seq_num in self.received_packets:
            packet = self.received_packets[self.expected_seq_num]
            if self.receive_callback:
                self.receive_callback(packet)
            del self.received_packets[self.expected_seq_num]
            self.expected_seq_num = (self.expected_seq_num + 1) % 1000
    
    def _retransmit_packet(self, seq_num: int):
        """Retransmite um pacote"""
        if seq_num in self.pending_packets:
            packet = self.pending_packets[seq_num]
            packet.retry_count += 1
            
            if packet.retry_count <= MAX_RETRIES:
                if self.send_callback:
                    self.send_callback(packet.message)
                self.stats['retransmissions'] += 1
                log_message("SEND", "RETRANSMIT", f"Seq: {seq_num:03d} | Retry: {packet.retry_count}")
                
                # Reinicia timer
                if seq_num in self.timers:
                    self.timers[seq_num].reset()
            else:
                # Máximo de tentativas excedido
                log_message("ERROR", "MAX_RETRIES", f"Seq: {seq_num:03d} | Max retries exceeded")
                del self.pending_packets[seq_num]
                if seq_num in self.timers:
                    del self.timers[seq_num]
    
    def _monitor_timeouts(self):
        """Monitora timeouts em thread separada"""
        while self.running:
            current_time = time.time()
            expired_packets = []
            
            for seq_num, timer in self.timers.items():
                if timer.is_expired():
                    expired_packets.append(seq_num)
            
            for seq_num in expired_packets:
                self._retransmit_packet(seq_num)
            
            time.sleep(0.1)  # Verifica a cada 100ms
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do transporte"""
        return {
            **self.stats,
            'pending_packets': len(self.pending_packets),
            'window_size': self.window_size,
            'operation_mode': self.operation_mode.value
        }
    
    def reset(self):
        """Reinicia o transporte confiável"""
        self.next_seq_num = 0
        self.expected_seq_num = 0
        self.window_start = 0
        self.window_end = self.window_size - 1
        
        # Limpa estruturas
        self.pending_packets.clear()
        self.received_packets.clear()
        
        # Para todos os timers
        for timer in self.timers.values():
            timer.stop()
        self.timers.clear()
        
        # Reset estatísticas
        self.stats = {
            'packets_sent': 0,
            'packets_received': 0,
            'retransmissions': 0,
            'errors_detected': 0,
            'duplicate_packets': 0
        }

