# -*- coding: utf-8 -*-
"""
Stream MJPEG over HTTP para supervisório web em tempo real.

Servidor leve que expõe o último frame anotado (frame + detecções) via
multipart/x-mixed-replace para visualização em navegador.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from threading import Thread
from typing import Optional, List, Tuple
import socket
import time

import cv2
import numpy as np

from core.logger import get_logger
from detection.events import Detection

logger = get_logger("output.mjpeg")


# Cores BGR para desenho (verde, amarelo, laranja, vermelho por confiança)
_COLORS = {
    "high": (0, 255, 0),
    "medium": (0, 255, 255),
    "low": (0, 165, 255),
    "very_low": (0, 0, 255),
}


def _color_for_confidence(confidence: float) -> Tuple[int, int, int]:
    """Retorna cor BGR baseada na confiança."""
    if confidence >= 0.8:
        return _COLORS["high"]
    if confidence >= 0.5:
        return _COLORS["medium"]
    if confidence >= 0.3:
        return _COLORS["low"]
    return _COLORS["very_low"]


class StreamFrameProvider:
    """
    Fornece frames anotados em JPEG para o stream MJPEG.

    Thread-safe: update() e get_jpeg_bytes() usam lock interno.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._frame: Optional[np.ndarray] = None
        self._detections: List[Detection] = []
        self._last_jpeg: Optional[bytes] = None

    def update(self, frame: Optional[np.ndarray], detections: Optional[List[Detection]]) -> None:
        """Atualiza frame e/ou detecções (thread-safe)."""
        with self._lock:
            if frame is not None:
                self._frame = frame.copy() if frame is not None else None
            if detections is not None:
                self._detections = list(detections)

    def _get_annotated_image(self) -> Optional[np.ndarray]:
        """
        Retorna cópia do frame com anotações de detecção (bbox, centroide, labels).
        Thread-safe. Retorna None se não houver frame.
        """
        with self._lock:
            if self._frame is None:
                return None
            img = self._frame.copy()
            if self._detections:
                best = max(self._detections, key=lambda d: d.confidence)
                bbox = best.bbox
                x1, y1 = int(bbox.x1), int(bbox.y1)
                x2, y2 = int(bbox.x2), int(bbox.y2)
                color = _color_for_confidence(best.confidence)
                cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                cv2.circle(img, (cx, cy), 10, color, 2)
                cv2.circle(img, (cx, cy), 8, (255, 255, 255), 2)
                label = f"{best.class_name} {best.confidence:.0%}"
                cv2.putText(
                    img, label, (x1, y1 - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2,
                )
                coord = f"({(bbox.x1+bbox.x2)/2:.0f}, {(bbox.y1+bbox.y2)/2:.0f})"
                cv2.putText(
                    img, coord, (cx - 50, y2 + 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1,
                )
            return img

    def get_jpeg_bytes(self) -> Optional[bytes]:
        """
        Retorna último frame anotado como JPEG, ou None se não houver frame.
        Thread-safe.
        """
        img = self._get_annotated_image()
        if img is None:
            with self._lock:
                return self._last_jpeg
        ok, buf = cv2.imencode(".jpg", img)
        if ok:
            with self._lock:
                self._last_jpeg = buf.tobytes()
            return self._last_jpeg
        with self._lock:
            return self._last_jpeg

    def get_raw_frame(self) -> Optional[Tuple[bytes, int, int]]:
        """
        Retorna frame anotado como bytes BGR (width, height).
        Usado para exportação de frames em formato bruto.
        Thread-safe. Retorna None se não houver frame.
        """
        img = self._get_annotated_image()
        if img is None:
            return None
        h, w = img.shape[:2]
        return img.tobytes(), w, h


class _MjpegHandler(BaseHTTPRequestHandler):
    """Handler HTTP para stream MJPEG e página viewer."""

    protocol_version = "HTTP/1.1"
    server: "MjpegStreamServer"

    def log_message(self, format, *args):
        logger.debug("http_request", path=self.path, client=self.client_address[0])

    def do_GET(self):
        path = self.path.split("?")[0].rstrip("/") or "/"

        if path == "/stream":
            self._serve_mjpeg()
        elif path in ("/", "/viewer"):
            self._serve_viewer()
        elif path == "/health":
            self._serve_health()
        else:
            self.send_error(404)

    def _serve_health(self):
        """GET /health -> 200 OK."""
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"ok"}')

    def _serve_viewer(self):
        """GET / ou /viewer -> página HTML com campo URL e img."""
        host = self.headers.get("Host", "localhost")
        default_url = f"http://{host}/stream"

        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Buddmeyer Vision - Stream</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ font-family: 'Segoe UI', sans-serif; margin: 20px; background: #1a1a2e; color: #e0e0e0; }}
    h1 {{ color: #00d4ff; font-size: 1.5rem; }}
    .ctrl {{ margin: 16px 0; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }}
    input[type="text"] {{ flex: 1; min-width: 280px; padding: 8px 12px; border: 1px solid #3d4852; border-radius: 4px; background: #2d3748; color: #e0e0e0; }}
    button {{ padding: 8px 16px; background: #00d4ff; color: #1a1a2e; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }}
    button:hover {{ background: #00b8e6; }}
    #stream {{ max-width: 100%; border: 2px solid #3d4852; border-radius: 4px; background: #000; }}
    .hint {{ font-size: 0.9rem; color: #8b9dc3; margin-top: 8px; }}
  </style>
</head>
<body>
  <h1>Buddmeyer Vision - Stream em Tempo Real</h1>
  <div class="ctrl">
    <input type="text" id="url" value="{default_url}" placeholder="http://IP:porta/stream">
    <button onclick="connect()">Conectar</button>
  </div>
  <p class="hint">Informe a URL do stream (ex: http://192.168.1.10:8765/stream) e clique em Conectar.</p>
  <div style="margin-top: 16px;">
    <img id="stream" src="" alt="Stream" style="display:none;">
  </div>
  <script>
    function connect() {{
      var url = document.getElementById('url').value.trim();
      var img = document.getElementById('stream');
      if (url) {{
        img.src = url;
        img.style.display = 'block';
      }}
    }}
    document.getElementById('url').addEventListener('keypress', function(e) {{
      if (e.key === 'Enter') connect();
    }});
  </script>
</body>
</html>"""

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(html.encode("utf-8")))
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def _serve_mjpeg(self):
        """GET /stream -> multipart/x-mixed-replace com JPEGs."""
        provider = self.server._provider
        fps = self.server._fps
        interval = 1.0 / fps if fps > 0 else 0.1

        self.send_response(200)
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=--jpgboundary")
        self.end_headers()

        try:
            while True:
                jpeg = provider.get_jpeg_bytes()
                if jpeg:
                    self.wfile.write(b"--jpgboundary\r\n")
                    self.wfile.write(b"Content-Type: image/jpeg\r\n")
                    self.wfile.write(f"Content-Length: {len(jpeg)}\r\n".encode())
                    self.wfile.write(b"\r\n")
                    self.wfile.write(jpeg)
                    self.wfile.write(b"\r\n")
                time.sleep(interval)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as e:
            logger.debug("mjpeg_client_disconnect", error=str(e))


class MjpegStreamServer:
    """
    Servidor HTTP em thread dedicada para stream MJPEG.

    Expõe:
    - GET /stream -> MJPEG
    - GET / ou /viewer -> página HTML com campo URL + img
    - GET /health -> 200 OK (health check)
    """

    def __init__(self, provider: StreamFrameProvider, port: int = 8765, fps: int = 10):
        self._provider = provider
        self._port = port
        self._fps = fps
        self._server: Optional[HTTPServer] = None
        self._thread: Optional[Thread] = None
        self._running = False

    def start(self) -> bool:
        """Inicia o servidor HTTP em thread separada."""
        if self._running:
            return True

        try:
            self._server = HTTPServer(("0.0.0.0", self._port), _MjpegHandler)
            self._server._provider = self._provider
            self._server._fps = self._fps
            self._thread = Thread(target=self._run, daemon=True)
            self._thread.start()
            self._running = True
            logger.info(
                "mjpeg_stream_started",
                port=self._port,
                fps=self._fps,
                url=f"http://<IP>:{self._port}/stream",
            )
            return True
        except OSError as e:
            logger.error("mjpeg_stream_start_failed", port=self._port, error=str(e))
            return False

    def _run(self):
        """Loop do servidor (executado na thread)."""
        try:
            self._server.serve_forever()
        except Exception as e:
            if self._running:
                logger.error("mjpeg_server_error", error=str(e))
        finally:
            if self._server:
                self._server.shutdown()

    def stop(self):
        """Para o servidor."""
        self._running = False
        if self._server:
            try:
                self._server.shutdown()
            except Exception:
                pass
            self._server = None
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        logger.info("mjpeg_stream_stopped", port=self._port)
