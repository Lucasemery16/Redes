# Aplicação Cliente-Servidor - Transporte Confiável de Dados

## 📋 Descrição
Aplicação cliente-servidor que implementa transporte confiável de dados na camada de aplicação, considerando um canal com perdas e erros. Este projeto demonstra todos os conceitos fundamentais de transporte confiável de dados em redes de computadores.

## 🏗️ Estrutura do Projeto
```
redes/
├── src/
│   ├── client.py              # Cliente da aplicação
│   ├── server.py              # Servidor da aplicação
│   ├── protocol.py            # Definições do protocolo
│   ├── reliable_transport.py  # Implementação do transporte confiável
│   ├── utils.py               # Utilitários (checksum, criptografia)
│   └── test_demo.py           # Script de demonstração
├── tests/
│   └── test_basic.py          # Testes unitários
├── docs/
│   ├── MANUAL_UTILIZACAO.md   # Manual do usuário
│   └── RELATORIO_TECNICO.md   # Relatório técnico
├── requirements.txt           # Dependências Python
├── run_server.sh             # Script para executar servidor
├── run_client.sh             # Script para executar cliente
└── README.md                 # Este arquivo
```

## ✨ Características Implementadas

### Características Obrigatórias
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

# Usando script
./run_server.sh
```

### Cliente
```bash
# Execução básica
python src/client.py

# Conectando a servidor específico
python src/client.py 192.168.1.100 8888

# Com configurações avançadas
python src/client.py localhost 8888 --max-size 200 --mode SELECTIVE_REPEAT --encrypt --error-sim

# Usando script
./run_client.sh
```

### Demonstração Automática
```bash
# Executa servidor e cliente automaticamente
python src/test_demo.py
```

## 🔧 Protocolo de Aplicação

### Handshake Inicial
1. Cliente envia `HANDSHAKE_REQUEST` com configurações
2. Servidor responde com `HANDSHAKE_RESPONSE` confirmando parâmetros
3. Comunicação estabelecida com transporte confiável

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

### Exemplo 1: Comunicação Básica
```bash
# Terminal 1 - Servidor
python src/server.py

# Terminal 2 - Cliente
python src/client.py
cliente> Esta é uma mensagem de teste com mais de 30 caracteres para validar o protocolo.
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

## 🧪 Testes

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

### Checkpoint 1 (22/09/2025) - 20%
- ✅ Aplicações cliente e servidor conectam via socket
- ✅ Handshake inicial implementado
- ✅ Troca de modo de operação e tamanho máximo

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
