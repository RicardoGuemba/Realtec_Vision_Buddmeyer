# Realtec Vision Buddmeyer - Script de Inicialização (Windows)
# Execute com: PowerShell -ExecutionPolicy Bypass -File "Iniciar_Buddmeyer_Vision.ps1"

$ErrorActionPreference = "Stop"

$ProjectDir = if ($PSScriptRoot) { $PSScriptRoot } else { Get-Location }
Set-Location $ProjectDir

if (Test-Path "$ProjectDir\venv\Scripts\Activate.ps1") {
    & "$ProjectDir\venv\Scripts\Activate.ps1"
}
python "$ProjectDir\realtec_vision_buddmeyer\main.py"
