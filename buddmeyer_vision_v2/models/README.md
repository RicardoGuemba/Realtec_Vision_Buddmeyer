# Modelos de Machine Learning

Este diretório contém os modelos de detecção de objetos.

## Modelos Suportados

- **DETR** (facebook/detr-resnet-50)
- **RT-DETR** (PekingU/rtdetr_r50vd) - padrão

## Arquivos Necessários

O modelo local deve conter:

- `config.json` - Configuração do modelo DETR
- `preprocessor_config.json` - Configuração do pré-processador
- `model.safetensors` ou `pytorch_model.bin` - Pesos
- `class_config.json` - Mapeamento de classes (opcional)

## Uso

### Download automático do Hugging Face

O sistema baixa automaticamente os modelos do Hugging Face na primeira execução.

### Modelo local

1. Coloque os arquivos do modelo neste diretório.
2. Configure em `config.yaml`:
   ```yaml
   detection:
     model_path: ./models
   ```
3. O modelo local tem prioridade sobre o Hugging Face.

### Verificação

```bash
python buddmeyer_vision_v2/scripts/check_model.py
```
