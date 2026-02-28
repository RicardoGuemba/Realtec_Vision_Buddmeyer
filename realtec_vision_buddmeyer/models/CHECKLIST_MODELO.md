# ✅ Checklist de Arquivos do Modelo

Este documento lista todos os arquivos necessários para que o modelo funcione corretamente.

## 📋 Arquivos Obrigatórios

### ✅ config.json
**Descrição:** Configuração do modelo DETR/RT-DETR  
**Tamanho aproximado:** ~2-5 KB  
**Conteúdo:** Arquitetura, hiperparâmetros, mapeamento de classes (id2label, label2id)

**Campos essenciais:**
- `model_type`: Tipo do modelo (ex: "detr", "rtdetr")
- `id2label`: Mapeamento ID → Nome da classe
- `label2id`: Mapeamento Nome da classe → ID

### ✅ preprocessor_config.json
**Descrição:** Configuração do pré-processador de imagens  
**Tamanho aproximado:** ~1-2 KB  
**Conteúdo:** Normalização, redimensionamento, formato de entrada

**Campos essenciais:**
- `image_processor_type`: Tipo (ex: "DetrImageProcessor")
- `size`: Tamanho da imagem (height, width)
- `image_mean`: Média para normalização
- `image_std`: Desvio padrão para normalização

### ✅ model.safetensors (ou pytorch_model.bin)
**Descrição:** Pesos do modelo treinado  
**Tamanho aproximado:** 100-500 MB (depende do modelo)  
**Formato preferido:** `.safetensors` (mais seguro)  
**Formato alternativo:** `pytorch_model.bin` ou `model.bin`

## 📝 Arquivos Opcionais

### ⚪ class_config.json
**Descrição:** Configuração customizada de classes  
**Uso:** Se você quiser personalizar as classes detectadas

### ⚪ README.md
**Descrição:** Documentação do modelo  
**Uso:** Informações sobre o modelo, treinamento, etc.

### ⚪ tokenizer_config.json
**Descrição:** Configuração do tokenizer (geralmente não necessário para modelos de detecção)

## 🔍 Verificação

Execute o script de verificação:

```bash
python realtec_vision_buddmeyer/scripts/check_model.py
```

Ou no código Python:

```python
from detection.model_validator import ModelValidator
from pathlib import Path

models_dir = Path("C:/Realtec_Vision_Buddmeyer/realtec_vision_buddmeyer/models")
is_valid, missing, warnings = ModelValidator.validate_model_directory(models_dir)

if is_valid:
    print("Modelo válido!")
else:
    print(f"Arquivos faltando: {missing}")
```

## 📍 Localização

**Diretório padrão:**
```
C:\Realtec_Vision_Buddmeyer\realtec_vision_buddmeyer\models\
```

**Configuração em `config.yaml`:**
```yaml
detection:
  model_path: C:/Realtec_Vision_Buddmeyer/realtec_vision_buddmeyer/models
```

## 🚀 Download Automático

Se os arquivos não estiverem presentes, o sistema tentará baixar automaticamente do Hugging Face na primeira execução usando o `default_model` configurado:

```yaml
detection:
  default_model: PekingU/rtdetr_r50vd
```

O modelo será baixado para o cache do Hugging Face (geralmente em `~/.cache/huggingface/`).

## ✅ Status Atual

Execute o script de verificação para ver o status atual do modelo.
