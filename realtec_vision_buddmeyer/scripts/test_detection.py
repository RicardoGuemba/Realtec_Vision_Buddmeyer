#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de teste para verificar detecção de objetos usando câmera USB.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import cv2
from config import get_settings
from detection import InferenceEngine

def test_detection():
    """Testa detecção usando câmera USB (índice 0)."""
    print("=" * 60)
    print("TESTE DE DETECÇÃO DE OBJETOS (Câmera USB)")
    print("=" * 60)
    print()

    settings = get_settings(reload=True)
    print(f"Modelo: {settings.detection.default_model}")
    print(f"Confiança mínima: {settings.detection.confidence_threshold}")
    print()

    print("Carregando modelo...")
    inference_engine = InferenceEngine()
    if not inference_engine.load_model():
        print("ERRO: Falha ao carregar modelo!")
        return
    print("Modelo carregado.")
    print()

    camera_index = settings.streaming.usb_camera_index
    print(f"Abrindo câmera USB (índice {camera_index})...")
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print("ERRO: Não foi possível abrir a câmera USB!")
        return
    print("Câmera aberta.")
    print()

    print("Processando 10 frames...")
    frame_count = 0
    for i in range(10):
        ret, frame = cap.read()
        if not ret:
            break
        frame_count += 1
        inference_engine.process_frame(frame, frame_id=i)
    cap.release()

    print()
    print(f"Frames processados: {frame_count}")
    print("=" * 60)
    print("TESTE CONCLUÍDO")
    print("=" * 60)

if __name__ == "__main__":
    test_detection()
