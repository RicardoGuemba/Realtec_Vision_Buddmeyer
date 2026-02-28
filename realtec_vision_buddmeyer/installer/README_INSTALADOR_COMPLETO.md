# Instalador Completo - Buddmeyer Vision System v2.0

## Descrição

Este instalador completo instala automaticamente:
- ✅ Todas as dependências Python necessárias
- ✅ Modelos de detecção de objetos
- ✅ Vídeos de exemplo
- ✅ Código fonte completo
- ✅ Scripts de inicialização

## Como Criar o Instalador .exe

### Pré-requisitos

1. Python 3.10+ instalado
2. PyInstaller instalado:
   ```bash
   pip install pyinstaller
   ```

### Passo a Passo

1. **Navegue até o diretório do instalador:**
   ```bash
   cd realtec_vision_buddmeyer\installer
   ```

2. **Execute o script de construção:**
   ```bash
   python build_complete_installer.py
   ```
   
   Ou use o arquivo .bat:
   ```bash
   criar_instalador_completo.bat
   ```

3. **Aguarde a conclusão:**
   - O processo pode levar 5-15 minutos
   - O arquivo será criado em `dist/BuddmeyerVisionInstallerCompleto.exe`

## Como Usar o Instalador

1. **Execute o arquivo .exe:**
   - Dê duplo clique em `BuddmeyerVisionInstallerCompleto.exe`

2. **Siga as instruções:**
   - O instalador verificará Python
   - Criará ambiente virtual
   - Instalará todas as dependências
   - Copiará modelos e vídeos
   - Criará scripts de inicialização

3. **Inicie o sistema:**
   - Navegue até o diretório de instalação (padrão: `C:\Users\<Usuario>\BuddmeyerVision`)
   - Dê duplo clique em `Iniciar_Buddmeyer_Vision.bat`

## Estrutura do Instalador

O instalador inclui:

```
BuddmeyerVisionInstallerCompleto.exe
├── install_complete.py (script de instalação)
├── realtec_vision_buddmeyer/ (código fonte)
│   ├── models/ (modelos de detecção)
│   ├── videos/ (vídeos de exemplo)
│   └── ... (outros arquivos)
```

## Diretório de Instalação Padrão

- **Windows:** `C:\Users\<Usuario>\BuddmeyerVision`
- Pode ser alterado passando o caminho como argumento

## Dependências Instaladas

### Básicas
- PySide6 (Interface gráfica)
- pydantic, pydantic-settings (Configuração)
- pyyaml (YAML)
- opencv-python (Processamento de imagem)
- Pillow, numpy (Imagens)
- structlog, colorama (Logging)
- qasync (Async/Qt)
- matplotlib (Gráficos)

### Machine Learning
- torch, torchvision (PyTorch)
- transformers (Hugging Face)
- accelerate, safetensors
- timm (Modelos DETR)

### Comunicação
- aphyt (CLP Omron)

## Verificação de Instalação

O instalador verifica automaticamente:
- ✅ Python instalado
- ✅ Dependências instaladas
- ✅ Modelos copiados
- ✅ Vídeos copiados

## Solução de Problemas

### Erro: "Python não encontrado"
- Instale Python 3.10+ de https://www.python.org/downloads/
- Certifique-se de marcar "Add Python to PATH" durante instalação

### Erro: "pip não encontrado"
- Reinstale Python com pip incluído
- Ou instale pip manualmente

### Erro: "PyTorch não instalado"
- O instalador tenta CUDA primeiro, depois CPU
- Se ambos falharem, instale manualmente após a instalação

### Modelos/Vídeos não copiados
- Verifique se os arquivos existem no diretório fonte
- O instalador criará diretórios vazios se não encontrar

## Tamanho do Instalador

- **Aproximadamente:** 50-100 MB
- Inclui todos os arquivos necessários
- Não requer conexão com internet (exceto para baixar dependências)

## Distribuição

Para distribuir o sistema:
1. Crie o instalador usando `build_complete_installer.py`
2. Envie apenas o arquivo `BuddmeyerVisionInstallerCompleto.exe`
3. O usuário executa o .exe e tudo é instalado automaticamente

## Notas

- O instalador cria um ambiente virtual isolado
- Não interfere com outras instalações Python
- Pode ser instalado em múltiplos locais
- Requer Python 3.10+ pré-instalado no sistema
