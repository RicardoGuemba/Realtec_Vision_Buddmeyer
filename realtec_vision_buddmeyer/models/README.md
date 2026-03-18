# Modelos de Machine Learning

Este diretório contém os modelos de detecção de objetos (DETR/RT-DETR).

## Modelos Suportados

- **DETR** (facebook/detr-resnet-50)
- **RT-DETR** (PekingU/rtdetr_r50vd) — padrão

## Arquivos necessários

- `config.json` — configuração do modelo
- `preprocessor_config.json` — pré-processador
- `model.safetensors` ou `pytorch_model.bin` — pesos
- `class_config.json` — classes (opcional)

## Uso

O sistema tenta primeiro o modelo local em `models/`. Se não encontrar, baixa do Hugging Face usando `default_model` em `config.yaml`.

## Verificação

```bash
python realtec_vision_buddmeyer/scripts/check_model.py
```
