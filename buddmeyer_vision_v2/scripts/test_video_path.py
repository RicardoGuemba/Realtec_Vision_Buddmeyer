#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de teste para verificar se o caminho de vídeo está sendo atualizado corretamente.
"""

import sys
from pathlib import Path

# Adiciona diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_settings
from streaming import StreamManager

def test_video_path():
    """Testa atualização de caminho de vídeo."""
    print("=" * 60)
    print("TESTE DE CAMINHO DE VÍDEO")
    print("=" * 60)
    print()
    
    # Obtém configurações
    settings = get_settings(reload=True)
    print(f"Caminho atual no config: {settings.streaming.video_path}")
    print()
    
    # Verifica se arquivo existe
    video_path = Path(settings.streaming.video_path)
    print(f"Arquivo existe: {video_path.exists()}")
    if video_path.exists():
        print(f"Tamanho: {video_path.stat().st_size / 1024 / 1024:.2f} MB")
    print()
    
    # Testa StreamManager
    print("Testando StreamManager...")
    stream_manager = StreamManager()
    
    # Simula mudança de fonte
    test_video = Path(__file__).parent.parent / "videos" / "Colcha.mp4"
    if test_video.exists():
        print(f"Testando com: {test_video}")
        
        # Atualiza configuração
        settings.streaming.video_path = str(test_video.resolve())
        print(f"Caminho atualizado: {settings.streaming.video_path}")
        
        # Muda fonte no StreamManager
        result = stream_manager.change_source(
            source_type="video",
            video_path=str(test_video.resolve()),
            loop_video=True,
        )
        
        print(f"change_source retornou: {result}")
        print()
        
        # Verifica configuração do StreamManager
        stream_settings = stream_manager._settings.streaming
        print(f"Caminho no StreamManager: {stream_settings.video_path}")
        print(f"Arquivo existe: {Path(stream_settings.video_path).exists()}")
    else:
        print(f"Arquivo de teste não encontrado: {test_video}")
    
    print()
    print("=" * 60)
    print("TESTE CONCLUÍDO")
    print("=" * 60)

if __name__ == "__main__":
    test_video_path()
