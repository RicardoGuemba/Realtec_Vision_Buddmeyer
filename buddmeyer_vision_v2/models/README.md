# Modelos de Machine Learning

Este diretório contém os modelos de detecção de objetos.

## Modelos Suportados

- **DETR** (facebook/detr-resnet-50)
- **RT-DETR** (PekingU/rtdetr_r50vd) - padrão

## Uso

### Download automático do Hugging Face

O sistema baixa automaticamente os modelos do Hugging Face na primeira execução.

### Modelo local

Para usar um modelo local:

1. Coloque os arquivos do modelo neste diretório:
   - `config.json`
   - `model.safetensors` ou `pytorch_model.bin`
   - `preprocessor_config.json`

2. Configure o caminho no `config.yaml`:
   ```yaml
   detection:
     model_path: ./models
   ```
