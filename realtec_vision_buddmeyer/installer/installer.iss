; Script Inno Setup para criar instalador Windows
; Compile usando Inno Setup Compiler

[Setup]
AppName=Buddmeyer Vision System
AppVersion=2.0.0
AppPublisher=Buddmeyer Automation
AppPublisherURL=https://www.buddmeyer.com
DefaultDirName={userpf}\BuddmeyerVision
DefaultGroupName=Buddmeyer Vision System
OutputDir=dist
OutputBaseFilename=BuddmeyerVisionInstaller
Compression=lzma
SolidCompression=yes
SetupIconFile=
WizardImageFile=
WizardSmallImageFile=
LicenseFile=
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "portuguese"; MessagesFile: "compiler:Languages\Portuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar ícone na área de trabalho"; GroupDescription: "Ícones adicionais"
Name: "quicklaunchicon"; Description: "Criar ícone na barra de tarefas"; GroupDescription: "Ícones adicionais"; Flags: unchecked

[Files]
Source: "..\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "install.py"; DestDir: "{app}\installer"; Flags: ignoreversion

[Icons]
Name: "{group}\Buddmeyer Vision System"; Filename: "{app}\Iniciar_Buddmeyer_Vision.bat"; WorkingDir: "{app}"
Name: "{group}\Desinstalar"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Buddmeyer Vision System"; Filename: "{app}\Iniciar_Buddmeyer_Vision.bat"; Tasks: desktopicon; WorkingDir: "{app}"
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\Buddmeyer Vision System"; Filename: "{app}\Iniciar_Buddmeyer_Vision.bat"; Tasks: quicklaunchicon; WorkingDir: "{app}"

[Run]
Filename: "{app}\installer\install.py"; Description: "Executar instalação"; Flags: nowait postinstall skipifsilent; StatusMsg: "Instalando dependências..."

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
