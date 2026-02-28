#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de teste para verificar carregamento de modelo.
"""

import sys
from pathlib import Path

# Adiciona diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_settings
from detection import InferenceEngine

def test_model_loading():
    """Testa carregamento de modelo."""
    print("=" * 60)
    print("TESTE DE CARREGAMENTO DE MODELO")
    print("=" * 60)
    print()
    
    # Obtém configurações
    settings = get_settings(reload=True)
    print(f"Modelo padrão: {settings.detection.default_model}")
    print(f"Device: {settings.detection.device}")
    print(f"Model path: {settings.detection.model_path}")
    print()
    
    # Cria engine
    print("Criando InferenceEngine...")
    engine = InferenceEngine()
    print("OK: Engine criada")
    print()
    
    # Tenta carregar modelo
    print("Carregando modelo...")
    success = engine.load_model()
    
    if success:
        print("OK: Modelo carregado com sucesso!")
        print(f"   Modelo: {engine._loader._model_name}")
        print(f"   Device: {engine._loader.device}")
        print(f"   Labels: {engine._loader.model.config.num_labels}")
    else:
        print("ERRO: Falha ao carregar modelo!")
        return False
    
    print()
    print("=" * 60)
    print("TESTE CONCLUÍDO")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = test_model_loading()
    sys.exit(0 if success else 1)
