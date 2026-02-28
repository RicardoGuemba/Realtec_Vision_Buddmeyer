# Buddmeyer Vision System v2.0 - Script de Inicialização
# Execute com: PowerShell -ExecutionPolicy Bypass -File "Iniciar_Buddmeyer_Vision.ps1"

$ErrorActionPreference = "Stop"

# Diretório do projeto (onde está este script)
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Muda para o diretório do projeto
Set-Location $ProjectDir

# Ativa ambiente virtual
& "$ProjectDir\venv\Scripts\Activate.ps1"

# Executa o aplicativo
python "$ProjectDir\realtec_vision_buddmeyer\main.py"
