@echo off
rem Builds Butterfly.exe with the C# compiler that ships with Windows 10/11 (.NET Framework 4.x).
setlocal
set FW=%WINDIR%\Microsoft.NET\Framework64\v4.0.30319
if not exist "%FW%\csc.exe" set FW=%WINDIR%\Microsoft.NET\Framework\v4.0.30319
cd /d "%~dp0"
"%FW%\csc.exe" /nologo /target:winexe /optimize+ /codepage:65001 /out:Butterfly.exe ^
  /win32icon:src\butterfly.ico ^
  /resource:src\butterfly.png,butterfly.png /resource:src\beetle.png,beetle.png ^
  /resource:src\spider.png,spider.png /resource:src\snail.png,snail.png ^
  /resource:src\ninja.png,ninja.png /resource:src\flags.png,flags.png /resource:src\flags.txt,flags.txt ^
  /r:System.dll /r:System.Core.dll /r:System.Drawing.dll /r:System.Windows.Forms.dll ^
  /r:"%FW%\WPF\UIAutomationClient.dll" /r:"%FW%\WPF\UIAutomationTypes.dll" /r:"%FW%\WPF\WindowsBase.dll" ^
  src\Program.cs src\Settings.cs src\SettingsForm.cs src\Lang.cs src\Importer.cs src\Help.cs src\Apps.cs src\Installer.cs
endlocal
