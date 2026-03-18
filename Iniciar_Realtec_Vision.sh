#!/usr/bin/env bash
# Realtec Vision Buddmeyer - Launcher para macOS (incl. Apple Silicon M1/M2/M3/M4)
# Uso: ./Iniciar_Realtec_Vision.sh   ou   bash Iniciar_Realtec_Vision.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Ativa venv se existir
if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Executa a partir do diretório do pacote para imports corretos
exec python realtec_vision_buddmeyer/main.py
