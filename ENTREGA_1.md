# Entrega 1 - Handshake Inicial
**Data de Apresentação:** 22/09/2025 (monitores)  
**Status:** ✅ CONCLUÍDO

## 📋 Objetivo da Entrega

Implementar aplicações cliente e servidor que se conectem via socket e realizem o handshake inicial, trocando pelo menos o **modo de operação** e **tamanho máximo** de mensagem.

## 🎯 Requisitos Atendidos

### ✅ Conexão via Socket
- Cliente e servidor estabelecem conexão TCP
- Comunicação bidirecional implementada
- Gerenciamento adequado de conexões

### ✅ Handshake Inicial
- Protocolo de handshake estruturado
- Troca de parâmetros de configuração
- Validação de compatibilidade entre cliente e servidor

### ✅ Modo de Operação
- Negociação entre `GO_BACK_N` e `SELECTIVE_REPEAT`
- Cliente propõe modo de operação
- Servidor confirma ou rejeita a proposta

### ✅ Tamanho Máximo
- Definição do tamanho máximo de mensagem
- Validação de tamanho mínimo (30 caracteres)
- Configuração flexível de limites

## 🔧 Implementação Técnica

### Fluxo do Handshake

1. **Conexão TCP**: Cliente conecta ao servidor via socket
2. **Requisição**: Cliente envia `HANDSHAKE_REQUEST` com:
   - `max_message_size`: Tamanho máximo de mensagem
   - `operation_mode`: Modo de operação (GO_BACK_N/SELECTIVE_REPEAT)

3. **Validação**: Servidor valida parâmetros:
   - Verifica tamanho mínimo (30 caracteres)
   - Confirma modo de operação suportado

4. **Resposta**: Servidor envia `HANDSHAKE_RESPONSE` com:
   - `accepted`: True/False (aceita ou rejeita)
   - `window_size`: Tamanho da janela deslizante
   - `operation_mode`: Modo confirmado
   - `error_message`: Mensagem de erro (se rejeitado)

5. **Estabelecimento**: Comunicação estabelecida

### Estrutura das Mensagens

```json
{
  "type": "HANDSHAKE_REQ|HANDSHAKE_RESP",
  "sequence": 0,
  "payload": "",
  "checksum": 0,
  "window_size": 5,
  "metadata": {
    "max_message_size": 100,
    "operation_mode": "GO_BACK_N",
    "accepted": true,
    "error_message": ""
  }
}
```

## 📁 Arquivos para Entrega

### Código Fonte (Obrigatório)
```
src/
├── client.py              # Cliente com handshake
├── server.py              # Servidor com handshake
├── protocol.py            # Definições das mensagens
└── utils.py               # Utilitários básicos
```

### Instruções de Execução
```
# Executar servidor
python src/server.py

# Executar cliente
python src/client.py
```

### Documentação
```
README.md                  # Documentação principal
ENTREGA_1.md              # Este documento
```

## 🧪 Como Testar

### Execução Básica
```bash
# Terminal 1 - Servidor
python src/server.py

# Terminal 2 - Cliente
python src/client.py
```

### Saída Esperada
```
# Servidor:
🚀 Servidor iniciado em localhost:8888
📊 Configurações:
   - Tamanho máximo de mensagem: 100 caracteres
   - Tamanho da janela: 5
   - Modo de operação: GO_BACK_N
🔗 Nova conexão de ('127.0.0.1', 54321)
✅ Handshake aceito para ('127.0.0.1', 54321)
   - Tamanho máximo: 100
   - Modo: GO_BACK_N
   - Janela: 5

# Cliente:
🔗 Conectado ao servidor localhost:8888
📤 Handshake enviado:
   - Tamanho máximo: 100
   - Modo: GO_BACK_N
✅ Handshake aceito pelo servidor:
   - Janela: 5
   - Modo: GO_BACK_N
```

## 🔍 Características Técnicas

### Validações Implementadas
- **Tamanho mínimo**: Mensagens devem ter pelo menos 30 caracteres
- **Modo de operação**: Suporte a GO_BACK_N e SELECTIVE_REPEAT
- **Janela deslizante**: Tamanho configurável entre 1-5 pacotes
- **Timeout**: 10 segundos para handshake

### Tratamento de Erros
- Rejeição de handshake com parâmetros inválidos
- Mensagens de erro descritivas
- Timeout para handshake não respondido

## 📊 Métricas de Qualidade

### Funcionalidade
- ✅ Handshake 100% funcional
- ✅ Validação de parâmetros robusta
- ✅ Tratamento de erros adequado
- ✅ Logs informativos

### Código
- ✅ Estrutura modular e organizada
- ✅ Documentação inline adequada
- ✅ Tratamento de exceções
- ✅ Separação de responsabilidades

## 📝 Conclusão

A Entrega 1 foi **concluída com sucesso**, atendendo a todos os requisitos solicitados:

1. ✅ **Conexão via socket** estabelecida
2. ✅ **Handshake inicial** implementado
3. ✅ **Modo de operação** negociado
4. ✅ **Tamanho máximo** configurado
5. ✅ **Validação de parâmetros** funcional
6. ✅ **Tratamento de erros** adequado

O sistema está **pronto para demonstração** e atende completamente aos requisitos da entrega 1.
