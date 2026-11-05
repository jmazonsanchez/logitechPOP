@echo off
setlocal

echo ==========================================================
echo        LogiPop Sync - Desinstalador para Windows
echo ==========================================================
echo.

echo [1/3] Cerrando aplicacion LogiPop...
taskkill /f /im LogiPop.exe 2>nul

echo [2/3] Eliminando inicio automatico...
del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\LogiPop.lnk" 2>nul

echo [3/3] Eliminando archivos de aplicacion...
rmdir /s /q "%APPDATA%\LogiPop" 2>nul

echo.
echo ==========================================================
echo  LogiPop ha sido desinstalado completamente de Windows.
echo  Tus perifericos vuelven a su estado de fabrica.
echo ==========================================================
echo.
pause
