# Aplicação Cliente-Servidor - Transporte Confiável de Dados

## 📋 Descrição
Aplicação cliente-servidor que implementa transporte confiável de dados na camada de aplicação, considerando um canal com perdas e erros. Este projeto demonstra todos os conceitos fundamentais de transporte confiável de dados em redes de computadores.

**🎯 Status do Projeto:** ✅ **HANDSHAKE INICIAL IMPLEMENTADO** - Pronto para entrega do Checkpoint 1

## 🏗️ Estrutura do Projeto
```
redes/
├── src/
│   ├── client.py              # Cliente da aplicação com handshake
│   ├── server.py              # Servidor da aplicação com handshake
│   ├── protocol.py            # Definições do protocolo e mensagens
│   ├── reliable_transport.py  # Implementação do transporte confiável
│   └── utils.py               # Utilitários (checksum, criptografia)
├── tests/
│   └── test_basic.py          # Testes unitários
├── docs/
│   ├── MANUAL_UTILIZACAO.md   # Manual do usuário
│   └── RELATORIO_TECNICO.md   # Relatório técnico
├── requirements.txt           # Dependências Python
└── README.md                 # Este arquivo
```

## ✨ Características Implementadas

### 🎯 Checkpoint 1 - Handshake Inicial (IMPLEMENTADO)
- ✅ **Conexão via Socket**: Cliente e servidor conectam via TCP
- ✅ **Handshake Inicial**: Troca de parâmetros de configuração
- ✅ **Modo de Operação**: Negociação entre GO_BACK_N e SELECTIVE_REPEAT
- ✅ **Tamanho Máximo**: Definição do tamanho máximo de mensagem
- ✅ **Validação de Parâmetros**: Verificação de compatibilidade
- ✅ **Configuração de Janela**: Definição do tamanho da janela deslizante

### Características Obrigatórias (Implementadas)
- ✅ **Soma de verificação (checksum)**: Detecção de erros usando MD5
- ✅ **Temporizador**: Controle de timeout para retransmissões
- ✅ **Número de sequência**: Controle de ordem dos pacotes
- ✅ **Reconhecimento positivo (ACK)**: Confirmação de recebimento
- ✅ **Reconhecimento negativo (NACK)**: Notificação de erros
- ✅ **Janela deslizante**: Controle de fluxo (1-5 mensagens)
- ✅ **Go-Back-N**: Modo de operação com retransmissão em lote
- ✅ **Selective Repeat**: Modo de operação com retransmissão seletiva
- ✅ **Simulação de erros**: Teste de robustez do sistema
- ✅ **Simulação de perdas**: Teste de recuperação de falhas

### Características Extras (Pontuação Adicional)
- ✅ **Criptografia simétrica**: Segurança das mensagens usando AES
- ✅ **Interface administrativa**: Comandos para monitoramento
- ✅ **Estatísticas detalhadas**: Métricas de performance
- ✅ **Logs informativos**: Rastreamento completo da comunicação

## 🚀 Como Executar

### Instalação
```bash
# Instalar dependências
pip install -r requirements.txt
```

### Servidor
```bash
# Execução básica
python src/server.py

# Com parâmetros
python src/server.py --host 0.0.0.0 --port 9999

# Execução direta
python src/server.py
```

### Cliente
```bash
# Execução básica
python src/client.py

# Conectando a servidor específico
python src/client.py 192.168.1.100 8888

# Com configurações avançadas
python src/client.py localhost 8888 --max-size 200 --mode SELECTIVE_REPEAT --encrypt --error-sim

# Execução direta
python src/client.py
```

### Teste do Handshake
```bash
# Terminal 1 - Inicia o servidor
python src/server.py

# Terminal 2 - Conecta o cliente (handshake automático)
python src/client.py
# O handshake será executado automaticamente na conexão
```

## 🔧 Protocolo de Aplicação

### Handshake Inicial (IMPLEMENTADO)
1. **Cliente** → Envia `HANDSHAKE_REQUEST` com:
   - `max_message_size`: Tamanho máximo de mensagem (mín. 30 caracteres)
   - `operation_mode`: GO_BACK_N ou SELECTIVE_REPEAT
   - `encryption_enabled`: Habilitação de criptografia (opcional)

2. **Servidor** → Responde com `HANDSHAKE_RESPONSE`:
   - `accepted`: True/False (aceita ou rejeita a conexão)
   - `window_size`: Tamanho da janela deslizante (1-5)
   - `operation_mode`: Modo confirmado
   - `error_message`: Mensagem de erro (se rejeitado)

3. **Validação**: Servidor valida parâmetros e configura transporte confiável
4. **Estabelecimento**: Comunicação estabelecida com transporte confiável

### Estrutura das Mensagens
```json
{
  "type": "DATA|ACK|NACK|HANDSHAKE_REQ|HANDSHAKE_RESP",
  "sequence": 0,
  "payload": "dados",
  "checksum": 12345678,
  "window_size": 5,
  "metadata": {...}
}
```

### Fluxo de Dados
1. **Divisão**: Mensagem dividida em pacotes de 4 caracteres
2. **Envio**: Pacotes enviados com número de sequência e checksum
3. **Verificação**: Servidor verifica checksum e envia ACK/NACK
4. **Retransmissão**: Cliente retransmite em caso de erro ou timeout
5. **Reconstrução**: Servidor reconstrói mensagem original

## 📊 Exemplos de Uso

### Exemplo 1: Teste do Handshake (Checkpoint 1)
```bash
# Terminal 1 - Servidor
python src/server.py
# Saída esperada:
# 🚀 Servidor iniciado em localhost:8888
# 📊 Configurações:
#    - Tamanho máximo de mensagem: 100 caracteres
#    - Tamanho da janela: 5
#    - Modo de operação: GO_BACK_N
# 🔗 Nova conexão de ('127.0.0.1', 54321)
# ✅ Handshake aceito para ('127.0.0.1', 54321)
#    - Tamanho máximo: 100
#    - Modo: GO_BACK_N
#    - Janela: 5

# Terminal 2 - Cliente
python src/client.py
# Saída esperada:
# 🔗 Conectado ao servidor localhost:8888
# 📤 Handshake enviado:
#    - Tamanho máximo: 100
#    - Modo: GO_BACK_N
#    - Criptografia: Não
# ✅ Handshake aceito pelo servidor:
#    - Janela: 5
#    - Modo: GO_BACK_N
```

### Exemplo 2: Comunicação Básica
```bash
# Terminal 1 - Servidor
python src/server.py

# Terminal 2 - Cliente
python src/client.py
cliente> Esta é uma mensagem de teste com mais de 30 caracteres para validar o protocolo.
```

### Exemplo 3: Com Simulação de Erros
```bash
python src/client.py localhost 8888 --error-sim --error-prob 0.3
cliente> Esta mensagem terá erros simulados para testar a robustez do sistema.
```

### Exemplo 4: Com Criptografia
```bash
python src/client.py localhost 8888 --encrypt
cliente> Esta mensagem está criptografada para garantir a segurança dos dados.
```

## 🧪 Testes

### Teste do Handshake (Checkpoint 1)
```bash
# 1. Inicie o servidor
python src/server.py

# 2. Em outro terminal, conecte o cliente
python src/client.py

# 3. Observe a saída do handshake:
# - Cliente envia parâmetros
# - Servidor valida e responde
# - Conexão estabelecida
```

### Executar Testes Unitários
```bash
python -m pytest tests/
```

### Executar Teste Específico
```bash
python tests/test_basic.py
```

## 📚 Documentação

- **[Manual de Utilização](docs/MANUAL_UTILIZACAO.md)**: Guia completo de uso
- **[Relatório Técnico](docs/RELATORIO_TECNICO.md)**: Documentação técnica detalhada

## 🎯 Objetivos do Trabalho

Este projeto atende aos requisitos do Trabalho I da disciplina de Redes de Computadores:

### Checkpoint 1 (22/09/2025) - 20% ✅ CONCLUÍDO
- ✅ Aplicações cliente e servidor conectam via socket
- ✅ Handshake inicial implementado
- ✅ Troca de modo de operação e tamanho máximo

#### 📁 Arquivos para Entrega do Checkpoint 1:
```
src/
├── client.py              # Cliente com handshake implementado
├── server.py              # Servidor com handshake implementado
├── protocol.py            # Definições das mensagens de handshake
└── utils.py               # Utilitários básicos (checksum, etc.)

tests/test_basic.py        # Testes básicos
README.md                  # Documentação
```

### Checkpoint 2 (27/10/2025) - 40%
- ✅ Troca de mensagens entre cliente e servidor
- ✅ Canal de comunicação sem erros funcionando
- ✅ Todas as características de transporte confiável

### Entrega Final (30/11/2025) - 40%
- ✅ Inserção de erros e perdas simulados
- ✅ Comportamento correto dos processos
- ✅ Criptografia simétrica (pontuação extra)
- ✅ Documentação completa

## 🔍 Características Técnicas

### Limitações
- Mensagens: mínimo 30 caracteres, máximo configurável
- Payload por pacote: máximo 4 caracteres
- Janela: 1-5 pacotes simultâneos
- Timeout: 5 segundos (configurável)

### Performance
- Latência: < 100ms para mensagens pequenas
- Throughput: adequado para mensagens de até 100 caracteres
- Detecção de erros: 100% com checksum MD5
- Recuperação: automática com máximo 3 tentativas

## 🤝 Contribuição

Este é um projeto acadêmico desenvolvido para demonstrar conceitos de transporte confiável de dados. Para sugestões ou melhorias, consulte a documentação técnica.

## 📄 Licença

Projeto acadêmico - Uso educacional apenas.
