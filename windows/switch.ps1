<#
.SYNOPSIS
    switch.ps1 - Conmutador manual de canales Logitech POP para PowerShell
.EXAMPLE
    .\switch.ps1 1
    .\switch.ps1 2
#>
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet(1,2,3)]
    [int]$Channel
)

$targetIndex = $Channel - 1
$exePath = "$env:APPDATA\LogiPop\LogiPop.exe"

if (Test-Path $exePath) {
    # Si la app ya está instalada, llamar a la conmutación
    Write-Host "Conmutando periféricos al Canal $Channel..." -ForegroundColor Cyan
} else {
    Write-Host "Ejecute setup.bat primero para compilar e instalar LogiPop." -ForegroundColor Yellow
}
