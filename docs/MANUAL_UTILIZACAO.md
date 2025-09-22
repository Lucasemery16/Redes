# Manual de Utilização - Aplicação de Transporte Confiável

## Índice
1. [Introdução](#introdução)
2. [Instalação](#instalação)
3. [Execução](#execução)
4. [Funcionalidades](#funcionalidades)
5. [Comandos](#comandos)
6. [Exemplos de Uso](#exemplos-de-uso)
7. [Solução de Problemas](#solução-de-problemas)

## Introdução

Esta aplicação implementa um sistema cliente-servidor com transporte confiável de dados na camada de aplicação. O sistema garante a entrega confiável de mensagens mesmo em canais com perdas e erros, implementando todas as características necessárias para transporte confiável.

### Características Principais
- ✅ **Soma de verificação (Checksum)**: Detecção de erros usando MD5
- ✅ **Temporizador**: Controle de timeout para retransmissões
- ✅ **Número de sequência**: Controle de ordem dos pacotes
- ✅ **Reconhecimento positivo/negativo**: ACK e NACK
- ✅ **Janela deslizante**: Controle de fluxo (1-5 pacotes)
- ✅ **Go-Back-N e Selective Repeat**: Dois modos de operação
- ✅ **Simulação de erros**: Teste de robustez do sistema
- ✅ **Criptografia simétrica**: Segurança das mensagens (AES)

## Instalação

### Pré-requisitos
- Python 3.7 ou superior
- pip (gerenciador de pacotes Python)

### Passos de Instalação

1. **Clone ou baixe o projeto**
   ```bash
   cd /caminho/para/o/projeto
   ```

2. **Instale as dependências**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verifique a instalação**
   ```bash
   python src/server.py --help
   python src/client.py --help
   ```

## Execução

### Servidor

Para iniciar o servidor:

```bash
# Execução básica (localhost:8888)
python src/server.py

# Com parâmetros personalizados
python src/server.py --host 0.0.0.0 --port 9999
```

**Parâmetros do servidor:**
- `--host`: Endereço do servidor (padrão: localhost)
- `--port`: Porta do servidor (padrão: 8888)

### Cliente

Para conectar um cliente:

```bash
# Execução básica
python src/client.py

# Conectando a servidor específico
python src/client.py 192.168.1.100 8888

# Com configurações avançadas
python src/client.py localhost 8888 --max-size 200 --mode SELECTIVE_REPEAT --encrypt --error-sim
```

**Parâmetros do cliente:**
- `host`: Endereço do servidor (padrão: localhost)
- `port`: Porta do servidor (padrão: 8888)
- `--max-size`: Tamanho máximo de mensagem (padrão: 100)
- `--mode`: Modo de operação (GO_BACK_N ou SELECTIVE_REPEAT)
- `--encrypt`: Habilita criptografia
- `--error-sim`: Habilita simulação de erros
- `--error-type`: Tipo de erro (random, bit_flip, character_change)
- `--error-prob`: Probabilidade de erro (0.0-1.0)

## Funcionalidades

### 1. Handshake Inicial

O cliente e servidor realizam um handshake para estabelecer a comunicação:

1. Cliente envia `HANDSHAKE_REQUEST` com:
   - Tamanho máximo de mensagem
   - Modo de operação
   - Configuração de criptografia

2. Servidor responde com `HANDSHAKE_RESPONSE`:
   - Aceitação ou rejeição
   - Tamanho da janela
   - Modo de operação confirmado

### 2. Divisão de Mensagens

Mensagens são divididas em pacotes de até 4 caracteres:
- Mensagem: "Esta é uma mensagem de teste"
- Pacotes: ["Esta", " é u", "ma m", "ensa", "gem ", "de t", "este"]

### 3. Transporte Confiável

Cada pacote inclui:
- **Número de sequência**: Controle de ordem
- **Checksum**: Detecção de erros (MD5)
- **Payload**: Dados (máximo 4 caracteres)
- **Metadados**: Informações adicionais

### 4. Controle de Fluxo

- **Janela deslizante**: 1-5 pacotes simultâneos
- **Go-Back-N**: Retransmite a partir do pacote perdido
- **Selective Repeat**: Retransmite apenas pacotes perdidos

### 5. Detecção e Correção de Erros

- **Checksum**: Detecta corrupção de dados
- **Timeout**: Detecta perda de pacotes
- **Retransmissão**: Corrige erros automaticamente
- **NACK**: Notifica erros específicos

## Comandos

### Comandos do Servidor

Durante a execução do servidor, você pode usar:

```
servidor> stats          # Exibe estatísticas
servidor> clients        # Lista clientes conectados
servidor> config         # Exibe configurações
servidor> error 0.2      # Define probabilidade de perda (20%)
servidor> window 3       # Define tamanho da janela
servidor> mode GO_BACK_N # Define modo de operação
servidor> quit           # Para o servidor
```

### Comandos do Cliente

Durante a execução do cliente:

```
cliente> <mensagem>      # Envia mensagem
cliente> stats           # Exibe estatísticas
cliente> error on        # Liga simulação de erros
cliente> error off       # Desliga simulação de erros
cliente> quit            # Desconecta e sai
```

## Exemplos de Uso

### Exemplo 1: Comunicação Básica

**Terminal 1 (Servidor):**
```bash
python src/server.py
```

**Terminal 2 (Cliente):**
```bash
python src/client.py
cliente> Esta é uma mensagem de teste com mais de 30 caracteres para validar o protocolo de transporte confiável.
```

### Exemplo 2: Com Simulação de Erros

```bash
python src/client.py localhost 8888 --error-sim --error-prob 0.3
cliente> Esta mensagem terá erros simulados para testar a robustez do sistema.
```

### Exemplo 3: Com Criptografia

```bash
python src/client.py localhost 8888 --encrypt
cliente> Esta mensagem está criptografada para garantir a segurança dos dados.
```

### Exemplo 4: Modo Selective Repeat

```bash
python src/client.py localhost 8888 --mode SELECTIVE_REPEAT
cliente> Mensagem usando Selective Repeat para melhor eficiência.
```

### Exemplo 5: Script de Demonstração

```bash
python src/test_demo.py
```

## Solução de Problemas

### Problemas Comuns

**1. Erro de conexão recusada**
```
❌ Erro ao conectar: [Errno 61] Connection refused
```
**Solução:** Verifique se o servidor está rodando e a porta está correta.

**2. Handshake rejeitado**
```
❌ Handshake rejeitado: Tamanho mínimo de mensagem é 30 caracteres
```
**Solução:** Use mensagens com pelo menos 30 caracteres.

**3. Timeout no handshake**
```
❌ Timeout no handshake
```
**Solução:** Verifique a conectividade de rede e se o servidor está respondendo.

**4. Erro de dependências**
```
ModuleNotFoundError: No module named 'cryptography'
```
**Solução:** Execute `pip install -r requirements.txt`

### Logs e Debugging

O sistema gera logs detalhados mostrando:
- Metadados de cada pacote enviado/recebido
- Reconhecimentos (ACK/NACK)
- Retransmissões
- Erros detectados
- Estatísticas de comunicação

### Monitoramento

Use os comandos `stats` no cliente e servidor para monitorar:
- Número de pacotes enviados/recebidos
- Retransmissões
- Erros detectados
- Tamanho da janela
- Modo de operação

## Arquitetura do Sistema

```
┌─────────────┐    Socket TCP    ┌─────────────┐
│   Cliente   │◄─────────────────►│   Servidor  │
└─────────────┘                   └─────────────┘
       │                                 │
       ▼                                 ▼
┌─────────────┐                   ┌─────────────┐
│ Transporte  │                   │ Transporte  │
│ Confiável   │                   │ Confiável   │
└─────────────┘                   └─────────────┘
       │                                 │
       ▼                                 ▼
┌─────────────┐                   ┌─────────────┐
│ Protocolo   │                   │ Protocolo   │
│ Aplicação   │                   │ Aplicação   │
└─────────────┘                   └─────────────┘
```

## Conclusão

Esta aplicação demonstra todos os conceitos de transporte confiável de dados, incluindo detecção de erros, controle de fluxo, e recuperação de falhas. O sistema é robusto, configurável e adequado para ambientes com perdas e erros de transmissão.
