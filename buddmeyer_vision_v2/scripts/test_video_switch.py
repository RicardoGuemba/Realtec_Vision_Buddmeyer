# -*- coding: utf-8 -*-
"""
Script de teste para verificar a troca de video durante execucao.
"""

import sys
import time
from pathlib import Path

# Adiciona o diretório pai ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from config import get_settings
from streaming.stream_manager import StreamManager
from detection.inference_engine import InferenceEngine
from core.logger import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger("test.video_switch")


class VideoSwitchTest:
    """Teste de troca de video."""
    
    def __init__(self):
        self.settings = get_settings()
        self.stream_manager = StreamManager()
        self.inference_engine = InferenceEngine()
        
        self.frame_count = 0
        self.detection_count = 0
        self.current_video = None
        self.test_phase = 0
        self.frames_video1 = 0
        self.frames_video2 = 0
        self.initial_frames = 0
        self.success = False
        
        # Lista de vídeos para testar
        videos_dir = Path(__file__).parent.parent / "videos"
        self.videos = list(videos_dir.glob("*.mp4"))
        
        # Conecta sinais
        self.stream_manager.frame_info_available.connect(self._on_frame)
        self.stream_manager.frame_info_available.connect(
            lambda info: self.inference_engine.process_frame(info.frame, info.frame_id)
        )
        self.inference_engine.detection_result.connect(self._on_detection)
    
    def _on_frame(self, frame_info):
        self.frame_count += 1
        if self.frame_count % 30 == 0:
            print(f"  [FRAME] Video: {self.current_video} - Frame #{self.frame_count}")
    
    def _on_detection(self, result):
        self.detection_count += 1
        if result.detections:
            print(f"  [DETECCAO] Video: {self.current_video} - {len(result.detections)} objetos")
    
    def run(self):
        """Executa o teste."""
        print("=" * 60)
        print("TESTE DE TROCA DE VIDEO DURANTE EXECUCAO")
        print("=" * 60)
        
        if len(self.videos) < 1:
            print("[ERRO] Nenhum video encontrado!")
            return False
        
        print(f"\n[INFO] Videos encontrados:")
        for v in self.videos:
            print(f"  - {v.name}")
        
        # Carrega modelo
        print("\n[INFO] Carregando modelo de deteccao...")
        if not self.inference_engine.load_model():
            print("[ERRO] Falha ao carregar modelo!")
            return False
        print("[OK] Modelo carregado!")
        
        # Inicia inferência
        print("[INFO] Iniciando inferencia...")
        if not self.inference_engine.start():
            print("[ERRO] Falha ao iniciar inferencia!")
            return False
        print("[OK] Inferencia iniciada!")
        
        # Teste com primeiro vídeo
        video1 = self.videos[0]
        self.current_video = video1.name
        print(f"\n[TESTE 1] Iniciando stream com: {video1.name}")
        
        self.settings.streaming.video_path = str(video1)
        self.settings.streaming.source_type = "video"
        
        self.stream_manager.change_source(
            source_type="video",
            video_path=str(video1),
            loop_video=True,
        )
        
        if not self.stream_manager.start():
            print("[ERRO] Falha ao iniciar stream!")
            return False
        print("[OK] Stream iniciado!")
        
        # Configura timer para próxima fase
        self.test_phase = 1
        self.initial_frames = self.frame_count
        QTimer.singleShot(3000, self._phase2)
        
        return True
    
    def _phase2(self):
        """Segunda fase: troca de vídeo."""
        self.frames_video1 = self.frame_count - self.initial_frames
        print(f"[INFO] Frames processados do video 1: {self.frames_video1}")
        
        if self.frames_video1 == 0:
            print("[ERRO] Nenhum frame processado do video 1!")
            self._finish(False)
            return
        
        # Troca para segundo vídeo
        video2 = self.videos[1] if len(self.videos) > 1 else self.videos[0]
        self.current_video = video2.name
        print(f"\n[TESTE 2] Trocando para: {video2.name}")
        
        self.initial_frames = self.frame_count
        
        success = self.stream_manager.change_source(
            source_type="video",
            video_path=str(video2),
            loop_video=True,
        )
        
        if not success:
            print("[ERRO] Falha ao trocar video!")
            self._finish(False)
            return
        print("[OK] Video trocado!")
        
        # Configura timer para finalizar
        QTimer.singleShot(3000, self._phase3)
    
    def _phase3(self):
        """Terceira fase: verificação."""
        self.frames_video2 = self.frame_count - self.initial_frames
        print(f"[INFO] Frames processados do video 2: {self.frames_video2}")
        
        if self.frames_video2 == 0:
            print("[ERRO] Nenhum frame processado do video 2!")
            self._finish(False)
            return
        
        # Verifica se inferência ainda está rodando
        if not self.inference_engine.is_running:
            print("[ERRO] Inferencia parou apos troca de video!")
            self._finish(False)
            return
        print("[OK] Inferencia continua rodando!")
        
        self._finish(True)
    
    def _finish(self, success: bool):
        """Finaliza o teste."""
        self.success = success
        
        print("\n" + "=" * 60)
        print("RESULTADO DO TESTE")
        print("=" * 60)
        print(f"Total de frames processados: {self.frame_count}")
        print(f"Total de deteccoes: {self.detection_count}")
        print(f"Frames do video 1: {self.frames_video1}")
        print(f"Frames do video 2: {self.frames_video2}")
        print(f"Inferencia ativa: {self.inference_engine.is_running}")
        print(f"Stream ativo: {self.stream_manager.is_running}")
        print("=" * 60)
        
        if success:
            print("[SUCESSO] TESTE DE TROCA DE VIDEO PASSOU!")
        else:
            print("[FALHA] TESTE DE TROCA DE VIDEO FALHOU!")
        print("=" * 60)
        
        # Limpa recursos
        print("\n[INFO] Limpando recursos...")
        self.stream_manager.stop()
        self.inference_engine.stop()
        print("[OK] Recursos liberados!")
        
        # Encerra aplicação
        QApplication.quit()


def main():
    """Main."""
    app = QApplication(sys.argv)
    
    test = VideoSwitchTest()
    
    # Inicia o teste após o event loop começar
    QTimer.singleShot(100, test.run)
    
    # Executa o event loop
    app.exec()
    
    return 0 if test.success else 1


if __name__ == "__main__":
    sys.exit(main())
