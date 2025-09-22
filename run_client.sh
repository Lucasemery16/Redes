#!/bin/bash
# Script para executar o cliente

echo "🔗 Iniciando cliente de transporte confiável..."
cd "$(dirname "$0")/src"
python client.py "$@"
