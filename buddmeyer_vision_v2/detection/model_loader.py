# -*- coding: utf-8 -*-
"""
Carregador de modelos de detecção DETR/RT-DETR.
"""

import warnings
from pathlib import Path
from typing import Optional, Tuple, Any, Dict
import torch

from core.logger import get_logger
from core.exceptions import ModelLoadError

logger = get_logger("detection.loader")


class ModelLoader:
    """
    Carregador de modelos DETR/RT-DETR do Hugging Face.
    
    Suporta modelos locais e download do hub.
    """
    
    # Modelos padrão suportados
    SUPPORTED_MODELS = {
        "rtdetr_r50vd": "PekingU/rtdetr_r50vd",
        "rtdetr_r101vd": "PekingU/rtdetr_r101vd",
        "detr_resnet50": "facebook/detr-resnet-50",
        "detr_resnet101": "facebook/detr-resnet-101",
    }
    
    def __init__(self):
        self._model = None
        self._processor = None
        self._device: str = "cpu"
        self._model_name: str = ""
    
    def load(
        self,
        model_path: str,
        device: str = "auto",
    ) -> Tuple[Any, Any]:
        """
        Carrega modelo e processador.
        
        Args:
            model_path: Caminho local ou ID do Hugging Face
            device: Device (cpu, cuda, auto)
        
        Returns:
            Tuple (model, processor)
        """
        try:
            from transformers import AutoModelForObjectDetection, AutoImageProcessor
        except ImportError:
            raise ModelLoadError(
                "Transformers não instalado. Execute: pip install transformers",
                {"package": "transformers"}
            )
        
        # Determina device
        self._device = self._resolve_device(device)
        logger.info("loading_model", model_path=model_path, device=self._device)
        
        try:
            # Verifica se é caminho local
            local_path = Path(model_path)
            
            # Se for caminho relativo, tenta resolver
            if not local_path.is_absolute():
                # Tenta resolver em relação ao diretório do projeto
                base_path = Path(__file__).parent.parent
                local_path = base_path / model_path
            
            if local_path.exists() and local_path.is_dir():
                # Verifica se tem arquivos de modelo válidos
                has_config = (local_path / "config.json").exists()
                has_preprocessor = (local_path / "preprocessor_config.json").exists()
                has_weights = any(
                    (local_path / weight).exists()
                    for weight in ["model.safetensors", "pytorch_model.bin", "model.bin"]
                )
                
                if has_config and has_preprocessor and has_weights:
                    model_source = str(local_path)
                    logger.info("loading_local_model", path=model_source)
                else:
                    # Diretório existe mas não tem modelo válido, usa Hugging Face
                    logger.warning("local_path_invalid_using_hf", path=str(local_path))
                    model_source = model_path
                    logger.info("loading_hf_model", model_id=model_source)
            else:
                # Usa como ID do Hugging Face
                model_source = model_path
                logger.info("loading_hf_model", model_id=model_source)
            
            # Suprime UserWarnings durante o carregamento (PyTorch/timm "assign=True", etc.)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                # Carrega processador (use_fast=True evita aviso "slow processor" e acelera pré-processamento)
                self._processor = AutoImageProcessor.from_pretrained(model_source, use_fast=True)
                # Carrega modelo (backbone timm pode ser baixado do hub na primeira vez)
                self._model = AutoModelForObjectDetection.from_pretrained(model_source)
            self._model.to(self._device)
            self._model.eval()
            
            self._model_name = model_path
            
            logger.info(
                "model_loaded",
                model=model_path,
                device=self._device,
                num_labels=self._model.config.num_labels,
            )
            
            return self._model, self._processor
            
        except Exception as e:
            logger.error("model_load_failed", error=str(e), model_path=model_path)
            raise ModelLoadError(
                f"Falha ao carregar modelo: {e}",
                {"model_path": model_path, "error": str(e)}
            )
    
    def _resolve_device(self, device: str) -> str:
        """
        Resolve o device a ser usado.
        
        Args:
            device: cpu, cuda, ou auto
        
        Returns:
            Device resolvido
        """
        if device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            else:
                logger.info("cuda_not_available_using_cpu")
                return "cpu"
        elif device == "cuda":
            if not torch.cuda.is_available():
                logger.warning("cuda_not_available_fallback_cpu")
                return "cpu"
            return "cuda"
        else:
            return "cpu"
    
    @property
    def model(self) -> Any:
        """Retorna o modelo carregado."""
        return self._model
    
    @property
    def processor(self) -> Any:
        """Retorna o processador carregado."""
        return self._processor
    
    @property
    def device(self) -> str:
        """Retorna o device atual."""
        return self._device
    
    @property
    def model_name(self) -> str:
        """Retorna o nome do modelo."""
        return self._model_name
    
    @property
    def is_loaded(self) -> bool:
        """Verifica se modelo está carregado."""
        return self._model is not None and self._processor is not None
    
    def get_model_info(self) -> Dict[str, Any]:
        """Retorna informações do modelo."""
        if not self.is_loaded:
            return {"loaded": False}
        
        return {
            "loaded": True,
            "name": self._model_name,
            "device": self._device,
            "num_labels": self._model.config.num_labels,
            "id2label": getattr(self._model.config, "id2label", {}),
        }
    
    def unload(self) -> None:
        """Descarrega o modelo."""
        if self._model is not None:
            del self._model
            self._model = None
        
        if self._processor is not None:
            del self._processor
            self._processor = None
        
        # Limpa cache CUDA
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        logger.info("model_unloaded")
    
    @staticmethod
    def get_cuda_info() -> Dict[str, Any]:
        """Retorna informações sobre CUDA."""
        if not torch.cuda.is_available():
            return {"available": False}
        
        return {
            "available": True,
            "device_count": torch.cuda.device_count(),
            "current_device": torch.cuda.current_device(),
            "device_name": torch.cuda.get_device_name(0),
            "memory_allocated": torch.cuda.memory_allocated(0),
            "memory_reserved": torch.cuda.memory_reserved(0),
        }
