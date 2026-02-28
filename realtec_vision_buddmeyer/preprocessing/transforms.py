# -*- coding: utf-8 -*-
"""
Transformações de imagem para pré-processamento.
"""

from typing import Tuple, Optional


def pixel_to_mm(centroid_px: Tuple[float, float], mm_per_pixel: float) -> Tuple[float, float]:
    """
    Converte coordenadas de pixel para milímetros.

    Args:
        centroid_px: Tupla (u, v) em pixels do frame.
        mm_per_pixel: Relação mm/pixel (calibração espacial). 1.0 = identidade (px = mm).

    Returns:
        Tupla (u, v) em milímetros quando mm_per_pixel > 0.
    """
    if mm_per_pixel <= 0:
        return centroid_px
    return (
        centroid_px[0] * mm_per_pixel,
        centroid_px[1] * mm_per_pixel,
    )
import numpy as np
import cv2


class ImageTransforms:
    """
    Coleção de transformações de imagem.
    """
    
    @staticmethod
    def adjust_brightness(image: np.ndarray, value: float) -> np.ndarray:
        """
        Ajusta brilho da imagem.
        
        Args:
            image: Imagem de entrada
            value: Valor de ajuste (-1.0 a 1.0)
        
        Returns:
            Imagem ajustada
        """
        if value == 0:
            return image
        
        # Converte para float
        img_float = image.astype(np.float32)
        
        # Ajusta brilho (value vai de -1 a 1, mapeado para -255 a 255)
        adjustment = value * 255
        img_float = img_float + adjustment
        
        # Clip para range válido
        img_float = np.clip(img_float, 0, 255)
        
        return img_float.astype(np.uint8)
    
    @staticmethod
    def adjust_contrast(image: np.ndarray, value: float) -> np.ndarray:
        """
        Ajusta contraste da imagem.
        
        Args:
            image: Imagem de entrada
            value: Valor de ajuste (-1.0 a 1.0)
        
        Returns:
            Imagem ajustada
        """
        if value == 0:
            return image
        
        # Converte para float
        img_float = image.astype(np.float32)
        
        # Calcula fator de contraste (value vai de -1 a 1)
        # -1 = contraste 0, 0 = contraste 1, 1 = contraste 3
        if value >= 0:
            factor = 1 + value * 2
        else:
            factor = 1 + value
        
        # Aplica contraste
        img_float = (img_float - 127.5) * factor + 127.5
        
        # Clip para range válido
        img_float = np.clip(img_float, 0, 255)
        
        return img_float.astype(np.uint8)
    
    @staticmethod
    def resize(
        image: np.ndarray,
        width: int,
        height: int,
        keep_aspect: bool = True,
    ) -> np.ndarray:
        """
        Redimensiona a imagem.
        
        Args:
            image: Imagem de entrada
            width: Largura desejada
            height: Altura desejada
            keep_aspect: Se True, mantém proporção
        
        Returns:
            Imagem redimensionada
        """
        h, w = image.shape[:2]
        
        if keep_aspect:
            # Calcula escala mantendo proporção
            scale = min(width / w, height / h)
            new_w = int(w * scale)
            new_h = int(h * scale)
        else:
            new_w, new_h = width, height
        
        return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    
    @staticmethod
    def crop(
        image: np.ndarray,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> np.ndarray:
        """
        Recorta uma região da imagem.
        
        Args:
            image: Imagem de entrada
            x: Coordenada X do canto superior esquerdo
            y: Coordenada Y do canto superior esquerdo
            width: Largura do recorte
            height: Altura do recorte
        
        Returns:
            Região recortada
        """
        h, w = image.shape[:2]
        
        # Garante que coordenadas estão dentro dos limites
        x = max(0, min(x, w - 1))
        y = max(0, min(y, h - 1))
        x2 = min(x + width, w)
        y2 = min(y + height, h)
        
        return image[y:y2, x:x2].copy()
    
    @staticmethod
    def normalize(image: np.ndarray) -> np.ndarray:
        """
        Normaliza a imagem para range [0, 1].
        
        Args:
            image: Imagem de entrada (uint8)
        
        Returns:
            Imagem normalizada (float32)
        """
        return image.astype(np.float32) / 255.0
    
    @staticmethod
    def denormalize(image: np.ndarray) -> np.ndarray:
        """
        Desnormaliza a imagem para range [0, 255].
        
        Args:
            image: Imagem normalizada (float32)
        
        Returns:
            Imagem uint8
        """
        return (image * 255).clip(0, 255).astype(np.uint8)
    
    @staticmethod
    def to_rgb(image: np.ndarray) -> np.ndarray:
        """
        Converte BGR para RGB.
        
        Args:
            image: Imagem em BGR
        
        Returns:
            Imagem em RGB
        """
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    @staticmethod
    def to_bgr(image: np.ndarray) -> np.ndarray:
        """
        Converte RGB para BGR.
        
        Args:
            image: Imagem em RGB
        
        Returns:
            Imagem em BGR
        """
        return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    
    @staticmethod
    def to_grayscale(image: np.ndarray) -> np.ndarray:
        """
        Converte para escala de cinza.
        
        Args:
            image: Imagem colorida
        
        Returns:
            Imagem em escala de cinza
        """
        if len(image.shape) == 2:
            return image
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    @staticmethod
    def gaussian_blur(image: np.ndarray, kernel_size: int = 5) -> np.ndarray:
        """
        Aplica blur gaussiano.
        
        Args:
            image: Imagem de entrada
            kernel_size: Tamanho do kernel (deve ser ímpar)
        
        Returns:
            Imagem suavizada
        """
        if kernel_size % 2 == 0:
            kernel_size += 1
        return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
    
    @staticmethod
    def sharpen(image: np.ndarray) -> np.ndarray:
        """
        Aplica sharpening.
        
        Args:
            image: Imagem de entrada
        
        Returns:
            Imagem com sharpening
        """
        kernel = np.array([
            [-1, -1, -1],
            [-1,  9, -1],
            [-1, -1, -1]
        ])
        return cv2.filter2D(image, -1, kernel)
    
    @staticmethod
    def histogram_equalization(image: np.ndarray) -> np.ndarray:
        """
        Aplica equalização de histograma.
        
        Args:
            image: Imagem de entrada
        
        Returns:
            Imagem equalizada
        """
        if len(image.shape) == 3:
            # Para imagem colorida, equaliza o canal V do HSV
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            hsv[:, :, 2] = cv2.equalizeHist(hsv[:, :, 2])
            return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        else:
            return cv2.equalizeHist(image)
    
    @staticmethod
    def clahe(
        image: np.ndarray,
        clip_limit: float = 2.0,
        tile_grid_size: Tuple[int, int] = (8, 8),
    ) -> np.ndarray:
        """
        Aplica CLAHE (Contrast Limited Adaptive Histogram Equalization).
        
        Args:
            image: Imagem de entrada
            clip_limit: Limite de clip
            tile_grid_size: Tamanho do grid
        
        Returns:
            Imagem com CLAHE aplicado
        """
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
        
        if len(image.shape) == 3:
            # Para imagem colorida, aplica no canal L do LAB
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            lab[:, :, 0] = clahe.apply(lab[:, :, 0])
            return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        else:
            return clahe.apply(image)
