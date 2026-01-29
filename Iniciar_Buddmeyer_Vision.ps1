# Buddmeyer Vision System v2.0 - Script de Inicialização
# Execute com: PowerShell -ExecutionPolicy Bypass -File "Iniciar_Buddmeyer_Vision.ps1"

$ErrorActionPreference = "Stop"

# Diretório do projeto
$ProjectDir = "C:\Vision_Buddmeyer_PySide"

# Muda para o diretório do projeto
Set-Location $ProjectDir

# Ativa ambiente virtual
& "$ProjectDir\venv\Scripts\Activate.ps1"

# Executa o aplicativo
python "$ProjectDir\buddmeyer_vision_v2\main.py"
