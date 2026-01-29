# 🚀 Como Usar o Instalador .exe

## 📦 Arquivo Criado

O instalador foi criado em:
```
buddmeyer_vision_v2/installer/dist/BuddmeyerVisionInstaller.exe
```

## 🎯 Como Executar o Instalador

### Passo 1: Execute o arquivo .exe

Dê duplo clique em:
```
BuddmeyerVisionInstaller.exe
```

### Passo 2: Siga as instruções

O instalador irá:
1. ✅ Verificar se Python 3.10+ está instalado
2. ✅ Criar diretório de instalação (padrão: `C:\Users\[Usuário]\BuddmeyerVision`)
3. ✅ Copiar todos os arquivos do projeto
4. ✅ Criar ambiente virtual Python
5. ✅ Instalar todas as dependências:
   - PySide6 (Interface)
   - PyTorch (ML com CUDA)
   - Transformers (RT-DETR)
   - OpenCV (Processamento de Imagem)
   - aphyt (Comunicação CIP)
   - E mais 30+ pacotes
6. ✅ Criar scripts de inicialização
7. ✅ Verificar instalação

### Passo 3: Aguarde a conclusão

A instalação pode levar **10-30 minutos** dependendo da velocidade da internet, pois precisa baixar:
- PyTorch (~2.8 GB com CUDA)
- Transformers e outras bibliotecas ML
- Todas as dependências

### Passo 4: Inicie o sistema

Após a instalação:

1. Navegue até o diretório de instalação (ex: `C:\Users\[Usuário]\BuddmeyerVision`)

2. Dê duplo clique em:
   ```
   Iniciar_Buddmeyer_Vision.bat
   ```

Ou execute no terminal:
```powershell
cd C:\Users\[Usuário]\BuddmeyerVision
.\venv\Scripts\activate
python buddmeyer_vision_v2\main.py
```

## ⚠️ Requisitos Antes de Instalar

- ✅ **Windows 10/11**
- ✅ **Python 3.10+** instalado (o instalador verifica)
- ✅ **Conexão com internet** (para download de dependências)
- ✅ **~10 GB de espaço em disco** livre
- ✅ **Privilégios de administrador** (recomendado)

## 🔧 Troubleshooting

### Erro: "Python não encontrado"
- Instale Python 3.10+ de https://www.python.org/downloads/
- Marque "Add Python to PATH" durante instalação
- Reinicie o computador após instalar Python

### Erro: "Falha ao instalar dependências"
- Verifique conexão com internet
- Execute o instalador como Administrador
- Verifique espaço em disco disponível
- Tente novamente (algumas dependências podem falhar na primeira tentativa)

### Erro: "PyTorch não instalado"
- O instalador tentará instalar PyTorch CPU como fallback
- Se falhar, instale manualmente após a instalação:
  ```bash
  cd [diretório_instalação]
  .\venv\Scripts\activate
  pip install torch torchvision
  ```

### Instalação muito lenta
- Normal! PyTorch com CUDA tem ~2.8 GB
- Aguarde a conclusão
- Não feche a janela do instalador

## 📝 Notas Importantes

- O instalador **não requer** Python pré-instalado no sistema (mas é recomendado)
- Se Python não estiver instalado, o instalador mostrará instruções
- O ambiente virtual é criado automaticamente
- Todas as dependências são instaladas no ambiente virtual (isoladas)

## 🎉 Após Instalação Bem-Sucedida

Você verá:
```
============================================================
INSTALAÇÃO CONCLUÍDA COM SUCESSO!
============================================================
✓ Sistema instalado em: C:\Users\[Usuário]\BuddmeyerVision

Para iniciar o sistema:
  1. Navegue até: C:\Users\[Usuário]\BuddmeyerVision
  2. Dê duplo clique em: Iniciar_Buddmeyer_Vision.bat
```

## 📞 Suporte

Se encontrar problemas:
1. Verifique os logs em `[diretório_instalação]\logs\`
2. Execute o instalador novamente (ele pode continuar de onde parou)
3. Verifique se todas as dependências foram instaladas corretamente
