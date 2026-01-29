#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para verificar se o modelo está completo e pronto para uso.
"""

import sys
from pathlib import Path

# Adiciona diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from detection.model_validator import ModelValidator
from config import get_settings

def main():
    """Verifica o modelo."""
    print("=" * 60)
    print("VERIFICAÇÃO DE MODELO - Buddmeyer Vision System v2.0")
    print("=" * 60)
    print()
    
    # Obtém diretório de modelos
    settings = get_settings()
    models_dir = settings.get_models_path()
    
    print(f"Diretório de modelos: {models_dir}")
    print()
    
    # Valida modelo
    is_valid, missing, warnings = ModelValidator.validate_model_directory(models_dir)
    
    if is_valid:
        print("[OK] MODELO VALIDO")
        print()
        
        # Mostra informações
        info = ModelValidator.get_model_info(models_dir)
        
        print("Arquivos encontrados:")
        for filename, file_info in info["files"].items():
            size_mb = file_info["size_mb"]
            print(f"  [OK] {filename} ({size_mb} MB)")
        
        if warnings:
            print()
            print("Avisos:")
            for warning in warnings:
                print(f"  [AVISO] {warning}")
        
        # Mostra informações do config
        if info["config"]:
            print()
            print("Informacoes do modelo:")
            config = info["config"]
            print(f"  Tipo: {config.get('model_type', 'N/A')}")
            print(f"  Labels: {config.get('num_labels', 'N/A')}")
            if "id2label" in config:
                labels = list(config["id2label"].values())[:5]
                print(f"  Classes (primeiras 5): {', '.join(labels)}")
        
        print()
        print("=" * 60)
        print("Modelo esta pronto para uso!")
        print("=" * 60)
        return 0
        
    else:
        print("[ERRO] MODELO INCOMPLETO")
        print()
        print("Arquivos faltando:")
        for file in missing:
            print(f"  [FALTANDO] {file}")
        
        if warnings:
            print()
            print("Avisos:")
            for warning in warnings:
                print(f"  [AVISO] {warning}")
        
        print()
        print("=" * 60)
        print("AÇÃO NECESSÁRIA:")
        print("=" * 60)
        print()
        print("Para usar modelo local:")
        print(f"1. Coloque os arquivos faltantes em: {models_dir}")
        print()
        print("Arquivos necessários:")
        print("  - config.json")
        print("  - preprocessor_config.json")
        print("  - model.safetensors (ou pytorch_model.bin)")
        print()
        print("Ou use modelo do Hugging Face:")
        print("  O sistema baixará automaticamente na primeira execução")
        print()
        return 1

if __name__ == "__main__":
    sys.exit(main())
