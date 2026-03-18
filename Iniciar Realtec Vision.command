#!/usr/bin/env bash
# Realtec Vision Buddmeyer - Atalho para duplo-clique no macOS
# Abre o Terminal e inicia o sistema (Apple Silicon M1/M2/M3/M4 compatível)

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Ativa venv se existir
if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Remove cache Python antigo para garantir código atualizado
find realtec_vision_buddmeyer -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# Executa a partir do diretório raiz para imports corretos
exec python realtec_vision_buddmeyer/main.py
