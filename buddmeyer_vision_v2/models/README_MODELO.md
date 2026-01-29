# 📦 Modelo de Detecção - Buddmeyer Vision System

## 📍 Localização

**Diretório:** `C:\Vision_Buddmeyer_PySide\buddmeyer_vision_v2\models`

## ✅ Arquivos Presentes

O modelo está **COMPLETO** e pronto para uso:

- ✅ `config.json` - Configuração do modelo DETR
- ✅ `preprocessor_config.json` - Configuração do pré-processador
- ✅ `model.safetensors` (158.78 MB) - Pesos do modelo treinado
- ✅ `class_config.json` - Configuração de classes
- ✅ `README.md` - Documentação

## 🎯 Classe Detectada

O modelo está configurado para detectar:
- **Classe:** `Embalagem`
- **ID:** `0`

## 🔧 Configuração

O sistema está configurado para usar este modelo local automaticamente.

**Arquivo de configuração:** `config/config.yaml`

```yaml
detection:
  model_path: C:/Vision_Buddmeyer_PySide/buddmeyer_vision_v2/models
  default_model: PekingU/rtdetr_r50vd  # Fallback se modelo local não funcionar
```

## 🚀 Como Funciona

1. **Primeira tentativa:** O sistema verifica se existe modelo local em `models/`
2. **Se encontrado:** Usa o modelo local (mais rápido, não precisa de internet)
3. **Se não encontrado:** Baixa automaticamente do Hugging Face usando `default_model`

## ✅ Verificação

Para verificar se o modelo está completo:

```bash
python buddmeyer_vision_v2/scripts/check_model.py
```

## 📝 Notas

- O modelo local tem **prioridade** sobre o modelo do Hugging Face
- Se o modelo local estiver incompleto, o sistema tentará usar o Hugging Face
- O modelo local é mais rápido pois não precisa baixar na primeira execução
