param(
  [Parameter(Mandatory = $false)]
  [string]$DbPassword,

  [Parameter(Mandatory = $false)]
  [string]$DatabaseUrl
)

$ErrorActionPreference = "Stop"

$projectRef = "fmqgghclblunippbaawi"
$backendDir = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $backendDir ".venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
  throw "Python venv tidak ditemukan di $pythonExe"
}

if ([string]::IsNullOrWhiteSpace($DatabaseUrl)) {
  if ([string]::IsNullOrWhiteSpace($DbPassword)) {
    $secure = Read-Host "Masukkan password database Supabase" -AsSecureString
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try {
      $DbPassword = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    } finally {
      if ($ptr -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
      }
    }
  }

  if ([string]::IsNullOrWhiteSpace($DbPassword)) {
    throw "Password database kosong."
  }

  $encodedPassword = [System.Uri]::EscapeDataString($DbPassword)
  $DatabaseUrl = "postgresql+psycopg://postgres:$encodedPassword@db.$projectRef.supabase.co:5432/postgres?sslmode=require"
}

$env:TARGET_DATABASE_URL = $DatabaseUrl

Write-Host "Menjalankan migrasi ke Supabase project $projectRef ..."
Push-Location $backendDir
try {
  & $pythonExe "scripts\migrate_local_to_postgres.py"
} finally {
  Pop-Location
}

Write-Host ""
Write-Host "Migrasi selesai."
Write-Host "DATABASE_URL untuk backend cloud sudah siap dipakai."
Write-Host "Host  : db.$projectRef.supabase.co"
Write-Host "Driver: postgresql+psycopg"
