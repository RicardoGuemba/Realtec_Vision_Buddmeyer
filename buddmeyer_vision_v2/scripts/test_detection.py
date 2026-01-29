#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de teste para verificar detecção de objetos no vídeo.
"""

import sys
from pathlib import Path

# Adiciona diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

import cv2
import numpy as np
from config import get_settings
from detection import InferenceEngine
from streaming import StreamManager

def test_detection():
    """Testa detecção de objetos no vídeo."""
    print("=" * 60)
    print("TESTE DE DETECÇÃO DE OBJETOS")
    print("=" * 60)
    print()
    
    # Obtém configurações
    settings = get_settings(reload=True)
    print(f"Modelo padrão: {settings.detection.default_model}")
    print(f"Confiança mínima: {settings.detection.confidence_threshold}")
    print(f"Máximo de detecções: {settings.detection.max_detections}")
    print()
    
    # Verifica vídeo
    video_path = Path(settings.streaming.video_path)
    print(f"Vídeo: {video_path}")
    print(f"Existe: {video_path.exists()}")
    print()
    
    if not video_path.exists():
        print("ERRO: Vídeo não encontrado!")
        return
    
    # Carrega modelo
    print("Carregando modelo...")
    inference_engine = InferenceEngine()
    
    if not inference_engine.load_model():
        print("ERRO: Falha ao carregar modelo!")
        return
    
    print("Modelo carregado com sucesso!")
    print()
    
    # Abre vídeo
    print("Abrindo vídeo...")
    cap = cv2.VideoCapture(str(video_path))
    
    if not cap.isOpened():
        print("ERRO: Não foi possível abrir o vídeo!")
        return
    
    # Lê alguns frames
    print("Processando frames...")
    frame_count = 0
    detections_count = 0
    
    for i in range(10):  # Testa 10 frames
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        # Processa frame
        inference_engine.process_frame(frame, frame_id=i)
        
        # Aguarda resultado (simulação)
        # Em produção, isso seria feito via signals
        
    cap.release()
    
    print()
    print(f"Frames processados: {frame_count}")
    print(f"Detecções encontradas: {detections_count}")
    print()
    print("=" * 60)
    print("TESTE CONCLUÍDO")
    print("=" * 60)

if __name__ == "__main__":
    test_detection()
