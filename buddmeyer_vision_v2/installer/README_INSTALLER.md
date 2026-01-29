# Instalador Buddmeyer Vision System v2.0

Este diretório contém os arquivos para criar um instalador .exe do sistema.

## 📦 Como Criar o Instalador

### Opção 1: Usando PyInstaller (Recomendado)

1. **Instale PyInstaller:**
```bash
pip install pyinstaller
```

2. **Execute o script de build:**
```bash
cd buddmeyer_vision_v2/installer
python build_installer.py
```

3. **O instalador será criado em:**
```
dist/BuddmeyerVisionInstaller.exe
```

### Opção 2: Usando Inno Setup (Instalador Windows Nativo)

1. **Baixe e instale Inno Setup:**
   - https://jrsoftware.org/isdl.php

2. **Abra o arquivo `installer.iss` no Inno Setup**

3. **Compile o instalador**

## 🚀 Como Usar o Instalador

1. **Execute o arquivo `.exe`**

2. **Siga as instruções na tela**

3. **O sistema será instalado em:**
   - Padrão: `C:\Users\[Usuário]\BuddmeyerVision`
   - Ou escolha um diretório personalizado

4. **Após a instalação:**
   - Navegue até o diretório de instalação
   - Dê duplo clique em `Iniciar_Buddmeyer_Vision.bat`

## 📋 O que o Instalador Faz

- ✅ Verifica se Python 3.10+ está instalado
- ✅ Cria ambiente virtual
- ✅ Instala todas as dependências:
  - PySide6 (Interface)
  - PyTorch (ML)
  - Transformers (RT-DETR)
  - OpenCV (Processamento de Imagem)
  - aphyt (Comunicação CIP)
  - E mais 30+ pacotes
- ✅ Cria scripts de inicialização
- ✅ Verifica instalação

## ⚙️ Requisitos

- Windows 10/11
- Python 3.10+ (será verificado pelo instalador)
- Conexão com internet (para download de dependências)
- ~5 GB de espaço em disco

## 🔧 Troubleshooting

### Erro: "Python não encontrado"
- Instale Python 3.10+ de https://www.python.org/downloads/
- Marque a opção "Add Python to PATH" durante a instalação

### Erro: "pip não encontrado"
- Reinstale Python com pip incluído

### Erro: "Falha ao instalar dependências"
- Verifique conexão com internet
- Execute o instalador como Administrador
- Verifique espaço em disco disponível
