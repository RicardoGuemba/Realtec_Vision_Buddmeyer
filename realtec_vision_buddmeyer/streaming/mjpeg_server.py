# -*- coding: utf-8 -*-
"""
Servidor HTTP MJPEG para streaming de vídeo via navegador.
URL simples para copiar e colar na barra de endereços (ex.: http://127.0.0.1:8080/stream).
Compatível com Windows e macOS.
"""

import socket
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional

import cv2
import numpy as np

from core.logger import get_logger

logger = get_logger("streaming.mjpeg")


def get_local_ip() -> str:
    """
    Obtém IP local da interface de rede (para exibir na URL).
    Usa múltiplos métodos para compatibilidade com Windows e macOS.
    """
    # Método 1: socket UDP para gateway (funciona em muitas redes)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.2)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        if ip and ip != "0.0.0.0":
            return ip
    except Exception:
        pass

    # Método 2: hostname (macOS, Linux)
    try:
        ip = socket.gethostbyname(socket.gethostname())
        if ip and ip != "127.0.0.1" and not ip.startswith("127."):
            return ip
    except Exception:
        pass

    # Método 3: localhost para acesso no mesmo PC
    return "127.0.0.1"


def is_port_available(host: str, port: int) -> bool:
    """Verifica se a porta está disponível para bind."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            s.bind((host, port))
            return True
    except OSError:
        return False


BOUNDARY = "frame"


class MjpegHandler(BaseHTTPRequestHandler):
    """Handler HTTP que serve stream MJPEG (multipart/x-mixed-replace)."""

    server_instance: Optional["MjpegServer"] = None

    def log_message(self, format, *args):
        """Reduz logs de acesso (evita poluir console)."""
        logger.debug("http_request", method=self.command, path=self.path, client=self.client_address[0])

    def do_GET(self):
        """Responde GET com stream MJPEG ou 404."""
        if self.server_instance is None:
            self.send_error(500, "Server not configured")
            return

        path = self.path.split("?")[0].rstrip("/") or "/"
        config_path = self.server_instance.path.rstrip("/") or "/"
        if path != config_path:
            self.send_error(404, f"Not Found: {self.path}")
            return

        self.send_response(200)
        self.send_header("Content-Type", f"multipart/x-mixed-replace; boundary={BOUNDARY}")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()

        try:
            while True:
                frame = self.server_instance.get_latest_frame()
                if frame is None:
                    time.sleep(0.033)  # ~30 Hz poll, evita busy loop
                    continue
                _, jpeg = cv2.imencode(".jpg", frame)
                if jpeg is None:
                    time.sleep(0.033)
                    continue
                data = jpeg.tobytes()
                self.wfile.write(f"--{BOUNDARY}\r\n".encode())
                self.wfile.write(b"Content-Type: image/jpeg\r\n")
                self.wfile.write(f"Content-Length: {len(data)}\r\n\r\n".encode())
                self.wfile.write(data)
                self.wfile.write(b"\r\n")
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as e:
            logger.warning("mjpeg_stream_error", error=str(e))


class MjpegServer:
    """
    Servidor HTTP que serve stream MJPEG.
    Permite copiar URL e colar no navegador para visualizar o vídeo.
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 8080, path: str = "/stream"):
        self._host = host
        self._port = port
        self._path = path if path.startswith("/") else f"/{path}"
        self._server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None
        self._latest_frame: Optional[np.ndarray] = None
        self._lock = threading.Lock()
        self._running = False

    @property
    def path(self) -> str:
        return self._path

    def push_frame(self, frame: np.ndarray) -> None:
        """Atualiza o frame mais recente (thread-safe)."""
        with self._lock:
            self._latest_frame = frame.copy() if frame is not None else None

    def get_latest_frame(self) -> Optional[np.ndarray]:
        """Retorna o frame mais recente (thread-safe)."""
        with self._lock:
            if self._latest_frame is not None:
                return self._latest_frame.copy()
        return None

    def start(self) -> bool:
        """Inicia o servidor em thread separada."""
        if self._running:
            return True
        if not is_port_available(self._host, self._port):
            logger.error(
                "mjpeg_port_in_use",
                port=self._port,
                hint="Porta em uso. Feche outro app ou mude a porta em Configuração → Saída.",
            )
            return False
        try:
            MjpegHandler.server_instance = self
            self._server = HTTPServer((self._host, self._port), MjpegHandler)
            self._thread = threading.Thread(target=self._serve, daemon=True)
            self._thread.start()
            self._running = True
            url = f"http://{get_local_ip()}:{self._port}{self._path}"
            logger.info("mjpeg_server_started", url=url, port=self._port)
            return True
        except OSError as e:
            logger.error("mjpeg_server_start_failed", error=str(e), port=self._port)
            return False

    def get_stream_url(self) -> str:
        """Retorna a URL completa do stream (para exibir ao usuário)."""
        return f"http://{get_local_ip()}:{self._port}{self._path}"

    def get_stream_urls(self) -> tuple[str, str]:
        """Retorna (url_localhost, url_rede) para exibição."""
        local = f"http://127.0.0.1:{self._port}{self._path}"
        net = f"http://{get_local_ip()}:{self._port}{self._path}"
        return (local, net)

    def verify_listening(self, timeout: float = 0.5) -> bool:
        """Verifica se o servidor está aceitando conexões em localhost."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                s.connect(("127.0.0.1", self._port))
                return True
        except OSError:
            return False

    def _serve(self) -> None:
        """Loop do servidor HTTP."""
        if self._server:
            self._server.serve_forever()

    def stop(self) -> None:
        """Para o servidor e limpa o frame."""
        if not self._running and self._server is None:
            with self._lock:
                self._latest_frame = None
            return
        self._running = False
        MjpegHandler.server_instance = None
        if self._server:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        with self._lock:
            self._latest_frame = None
        logger.info("mjpeg_server_stopped", port=self._port)
