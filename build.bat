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
  /resource:src\ninja.png,ninja.png /resource:src\ninja_sit.png,ninja_sit.png /resource:src\hand.png,hand.png /resource:src\luchador.png,luchador.png ^
  /resource:src\cloud_rain.png,cloud_rain.png /resource:src\cloud_snow.png,cloud_snow.png /resource:src\sun.png,sun.png /resource:src\sun_rays.png,sun_rays.png /resource:src\moon.png,moon.png /resource:src\flags.png,flags.png /resource:src\flags.txt,flags.txt ^
  /r:System.dll /r:System.Core.dll /r:System.Drawing.dll /r:System.Windows.Forms.dll ^
  /r:"%FW%\WPF\UIAutomationClient.dll" /r:"%FW%\WPF\UIAutomationTypes.dll" /r:"%FW%\WPF\WindowsBase.dll" ^
  src\Program.cs src\Settings.cs src\SettingsForm.cs src\Lang.cs src\Importer.cs src\Help.cs src\Apps.cs src\Installer.cs src\Fun.cs
endlocal
