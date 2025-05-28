[Setup]
AppName=System Information Collector
AppVersion=1.0.0
AppPublisher=System Information Collector
AppPublisherURL=https://github.com/
DefaultDirName={autopf}\SystemInformationCollector
DefaultGroupName=System Information Collector
OutputDir=installer_output
OutputBaseFilename=SystemInformationCollector_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
SetupIconFile=app_icon.ico
UninstallDisplayIcon={app}\SystemInformationCollector.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\SystemInformationCollector.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "requirements.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\System Information Collector"; Filename: "{app}\SystemInformationCollector.exe"
Name: "{group}\{cm:UninstallProgram,System Information Collector}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\System Information Collector"; Filename: "{app}\SystemInformationCollector.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\SystemInformationCollector.exe"; Description: "{cm:LaunchProgram,System Information Collector}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
  if not IsAdminLoggedOn then
  begin
    MsgBox('This installer requires administrator privileges to install the system information collector properly.', mbInformation, MB_OK);
    Result := False;
  end;
end;
