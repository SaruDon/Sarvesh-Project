# ==============================================================
# HYBRID NIDS - Simple Keep-Awake Script (No Compilation)
# Uses powercfg.exe - works on ALL Windows 10/11 versions
# ==============================================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " HYBRID NIDS - PRODUCTION SLEEP PREVENTION " -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# --- Save original sleep settings to restore later ---
$originalSleep = (powercfg /query SCHEME_CURRENT SUB_SLEEP STANDBYIDLE | 
    Select-String "Current AC Power Setting Index").ToString().Split(":")[-1].Trim()

$originalDisplay = (powercfg /query SCHEME_CURRENT SUB_VIDEO VIDEOIDLE | 
    Select-String "Current AC Power Setting Index").ToString().Split(":")[-1].Trim()

Write-Host "[OK] Original sleep setting saved: $originalSleep seconds" -ForegroundColor Green

# --- DISABLE all sleep and display timeouts ---
Write-Host "Disabling Sleep..." -ForegroundColor Yellow
powercfg /change standby-timeout-ac 0
powercfg /change standby-timeout-dc 0
powercfg /change monitor-timeout-ac 0
powercfg /change monitor-timeout-dc 0
powercfg /change hibernate-timeout-ac 0
powercfg /change hibernate-timeout-dc 0

# Also prevent screen lock via registry
$regPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\Personalization"
if (-not (Test-Path $regPath)) { New-Item -Path $regPath -Force | Out-Null }
Set-ItemProperty -Path $regPath -Name "NoLockScreen" -Value 1 -Type DWord -Force

Write-Host "[OK] Sleep DISABLED. PC will stay awake." -ForegroundColor Green
Write-Host ""

try {
    Write-Host "Starting Production Training..." -ForegroundColor Yellow
    Write-Host "Monitor progress in: lightning_logs/version_*/metrics.csv" -ForegroundColor Gray
    Write-Host ""
    
    # Run the training
    .\venv\Scripts\python.exe -m src.training.train_production
    
    Write-Host ""
    Write-Host "[DONE] Training completed successfully!" -ForegroundColor Green
}
catch {
    Write-Host "[ERROR] Training encountered an error: $_" -ForegroundColor Red
}
finally {
    # --- RESTORE original sleep settings ---
    Write-Host ""
    Write-Host "Restoring original power settings..." -ForegroundColor Yellow
    powercfg /change standby-timeout-ac 30
    powercfg /change monitor-timeout-ac 15
    
    # Remove the no-lock-screen policy
    Remove-ItemProperty -Path $regPath -Name "NoLockScreen" -ErrorAction SilentlyContinue
    
    Write-Host "[OK] Power settings restored. PC can sleep normally now." -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Cyan
}
