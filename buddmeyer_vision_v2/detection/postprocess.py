# -*- coding: utf-8 -*-
"""
Pós-processamento de detecções.
"""

from typing import List, Optional, Dict, Any, Tuple
import numpy as np
import torch

from .events import BoundingBox, Detection, DetectionResult


class PostProcessor:
    """
    Pós-processador de detecções.
    
    Realiza:
    - Filtro por confiança
    - NMS (Non-Maximum Suppression)
    - Filtro por classes
    - Limitação de detecções
    """
    
    def __init__(
        self,
        confidence_threshold: float = 0.5,
        nms_threshold: float = 0.5,
        max_detections: int = 10,
        target_classes: Optional[List[str]] = None,
    ):
        """
        Inicializa o pós-processador.
        
        Args:
            confidence_threshold: Threshold mínimo de confiança
            nms_threshold: Threshold de IoU para NMS
            max_detections: Máximo de detecções a retornar
            target_classes: Classes alvo (None = todas)
        """
        self.confidence_threshold = confidence_threshold
        self.nms_threshold = nms_threshold
        self.max_detections = max_detections
        self.target_classes = target_classes
    
    def process(
        self,
        outputs: Any,
        target_sizes: torch.Tensor,
        id2label: Dict[int, str],
        frame_id: int = 0,
        inference_time_ms: float = 0.0,
    ) -> DetectionResult:
        """
        Processa saída do modelo.
        
        Args:
            outputs: Saída do modelo (logits, boxes)
            target_sizes: Tamanhos dos frames
            id2label: Mapeamento ID → label
            frame_id: ID do frame
            inference_time_ms: Tempo de inferência
        
        Returns:
            DetectionResult com detecções processadas
        """
        from transformers.models.detr.modeling_detr import DetrObjectDetectionOutput
        
        # Processa saída do modelo
        probas = outputs.logits.softmax(-1)[0, :, :-1]  # Remove classe "no object"
        keep = probas.max(-1).values > self.confidence_threshold
        
        # Converte boxes para formato [x1, y1, x2, y2]
        boxes = outputs.pred_boxes[0, keep]
        scores = probas[keep]
        
        if len(boxes) == 0:
            return DetectionResult(
                detections=[],
                inference_time_ms=inference_time_ms,
                frame_id=frame_id,
            )
        
        # Escala boxes para tamanho do frame
        img_h, img_w = target_sizes[0].tolist()
        boxes = self._box_cxcywh_to_xyxy(boxes)
        boxes = boxes * torch.tensor([img_w, img_h, img_w, img_h], device=boxes.device)
        
        # Obtém classe e score para cada box
        max_scores, labels = scores.max(-1)
        
        # Converte para numpy
        boxes_np = boxes.cpu().numpy()
        scores_np = max_scores.cpu().numpy()
        labels_np = labels.cpu().numpy()
        
        # Aplica NMS
        keep_indices = self._nms(boxes_np, scores_np, self.nms_threshold)
        
        # Cria detecções
        detections = []
        for i in keep_indices[:self.max_detections]:
            class_id = int(labels_np[i])
            class_name = id2label.get(class_id, f"class_{class_id}")
            
            # Filtra por classes alvo
            if self.target_classes and class_name not in self.target_classes:
                continue
            
            bbox = BoundingBox.from_list(boxes_np[i].tolist())
            
            detection = Detection(
                bbox=bbox,
                confidence=float(scores_np[i]),
                class_id=class_id,
                class_name=class_name,
            )
            detections.append(detection)
        
        return DetectionResult(
            detections=detections,
            inference_time_ms=inference_time_ms,
            frame_id=frame_id,
        )
    
    def _box_cxcywh_to_xyxy(self, boxes: torch.Tensor) -> torch.Tensor:
        """Converte de formato (center_x, center_y, width, height) para (x1, y1, x2, y2)."""
        cx, cy, w, h = boxes.unbind(-1)
        x1 = cx - 0.5 * w
        y1 = cy - 0.5 * h
        x2 = cx + 0.5 * w
        y2 = cy + 0.5 * h
        return torch.stack([x1, y1, x2, y2], dim=-1)
    
    def _nms(
        self,
        boxes: np.ndarray,
        scores: np.ndarray,
        threshold: float,
    ) -> List[int]:
        """
        Aplica Non-Maximum Suppression.
        
        Args:
            boxes: Array de bounding boxes [N, 4]
            scores: Array de scores [N]
            threshold: Threshold de IoU
        
        Returns:
            Índices das boxes mantidas
        """
        if len(boxes) == 0:
            return []
        
        x1 = boxes[:, 0]
        y1 = boxes[:, 1]
        x2 = boxes[:, 2]
        y2 = boxes[:, 3]
        
        areas = (x2 - x1) * (y2 - y1)
        order = scores.argsort()[::-1]
        
        keep = []
        while order.size > 0:
            i = order[0]
            keep.append(i)
            
            if order.size == 1:
                break
            
            # Calcula IoU com boxes restantes
            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])
            
            w = np.maximum(0, xx2 - xx1)
            h = np.maximum(0, yy2 - yy1)
            inter = w * h
            
            iou = inter / (areas[i] + areas[order[1:]] - inter)
            
            # Mantém boxes com IoU menor que threshold
            inds = np.where(iou <= threshold)[0]
            order = order[inds + 1]
        
        return keep
    
    def set_confidence_threshold(self, threshold: float) -> None:
        """Define threshold de confiança."""
        self.confidence_threshold = max(0.0, min(1.0, threshold))
    
    def set_nms_threshold(self, threshold: float) -> None:
        """Define threshold de NMS."""
        self.nms_threshold = max(0.0, min(1.0, threshold))
    
    def set_max_detections(self, max_detections: int) -> None:
        """Define máximo de detecções."""
        self.max_detections = max(1, max_detections)
    
    def set_target_classes(self, classes: Optional[List[str]]) -> None:
        """Define classes alvo."""
        self.target_classes = classes
