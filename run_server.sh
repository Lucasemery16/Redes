#!/bin/bash
# Script para executar o servidor

echo "🚀 Iniciando servidor de transporte confiável..."
cd "$(dirname "$0")/src"
python server.py "$@"
