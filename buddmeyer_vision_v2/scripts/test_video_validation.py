#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de teste para validar arquivos de vídeo.
"""

import sys
from pathlib import Path

# Adiciona diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

import cv2
from config import get_settings

def test_video_validation():
    """Testa validação de vídeo."""
    print("=" * 60)
    print("TESTE DE VALIDAÇÃO DE VÍDEO")
    print("=" * 60)
    print()
    
    # Obtém configurações
    settings = get_settings(reload=True)
    video_path_str = settings.streaming.video_path
    video_path = Path(video_path_str)
    
    print(f"Caminho configurado: {video_path}")
    print(f"Existe: {video_path.exists()}")
    print(f"É arquivo: {video_path.is_file() if video_path.exists() else False}")
    print()
    
    if not video_path.exists():
        print("ERRO: Arquivo nao existe!")
        return False
    
    if not video_path.is_file():
        print("ERRO: Caminho nao e um arquivo!")
        return False
    
    # Testa abertura com OpenCV
    print("Testando abertura com OpenCV...")
    cap = cv2.VideoCapture(str(video_path))
    
    if not cap.isOpened():
        print("ERRO: OpenCV nao conseguiu abrir o arquivo!")
        cap.release()
        return False
    
    # Obtém propriedades
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"OK: Arquivo aberto com sucesso!")
    print(f"   Frames: {frame_count}")
    print(f"   FPS: {fps:.2f}")
    print(f"   Resolucao: {width}x{height}")
    print()
    
    # Tenta ler um frame
    ret, frame = cap.read()
    if ret:
        print(f"OK: Frame lido com sucesso!")
        print(f"   Shape: {frame.shape}")
    else:
        print("AVISO: Nao foi possivel ler o primeiro frame")
    
    cap.release()
    
    print()
    print("=" * 60)
    print("TESTE CONCLUÍDO")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = test_video_validation()
    sys.exit(0 if success else 1)
