@echo off
setlocal enabledelayedexpansion

echo ==========================================================
echo        LogiPop Sync - Instalador para Windows
echo ==========================================================
echo.

set "DEST_DIR=%APPDATA%\LogiPop"
if not exist "%DEST_DIR%" mkdir "%DEST_DIR%"

echo [1/3] Compilando aplicacion nativa LogiPop.exe...
set "CSC=C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
if not exist "%CSC%" set "CSC=C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe"

if not exist "%CSC%" (
    echo Error: No se encontro el compilador de .NET en Windows.
    echo Asegurese de tener instalado .NET Framework 4.5 o superior.
    pause
    exit /b 1
)

"%CSC%" /target:winexe /out:"%DEST_DIR%\LogiPop.exe" "%~dp0LogiPop.cs"
if errorlevel 1 (
    echo Error al compilar LogiPop.exe.
    pause
    exit /b 1
)
echo      Compilacion exitosa.

echo [2/3] Configurando inicio automatico con Windows...
set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%STARTUP_DIR%\LogiPop.lnk'); $s.TargetPath = '%DEST_DIR%\LogiPop.exe'; $s.Save()"
echo      Acceso directo creado en la carpeta de inicio.

echo [3/3] Iniciando LogiPop en segundo plano...
taskkill /f /im LogiPop.exe 2>nul
start "" "%DEST_DIR%\LogiPop.exe"

echo.
echo ==========================================================
echo  Instalacion completada con exito en Windows!
echo.
echo  Atajos activos en segundo plano:
echo    [Win + Alt + 1] - Conectar al Dispositivo 1
echo    [Win + Alt + 2] - Conectar al Dispositivo 2
echo    [Win + Alt + 3] - Conectar al Dispositivo 3
echo.
echo  La aplicacion quedara residente en el area de notificaciones
echo  (junto al reloj) y arrancara sola al iniciar sesion.
echo ==========================================================
echo.
pause
