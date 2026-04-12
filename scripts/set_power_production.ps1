# Check for administrator privileges and elevate if necessary
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "Requesting Administrator privileges..." -ForegroundColor Yellow
    $arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    Start-Process powershell -ArgumentList $arguments -Verb RunAs
    exit
}

# --- STOP INTERFERING SOFTWARE (IPM+) ---
Write-Host "Attempting to disable IPM+ Power Management Software..." -ForegroundColor Yellow

# Try stopping the service first
if (Get-Service "IPMPlusService" -ErrorAction SilentlyContinue) {
    Write-Host "Stopping IPMPlusService..." -ForegroundColor Cyan
    Stop-Service "IPMPlusService" -Force -ErrorAction SilentlyContinue
}

# Force kill any stubborn IPM+ processes
$IPMProcesses = @("IPMPlusAgentWe", "IPMPlusMonitor", "IPMPlusService", "IPMPlusUserInteract")
foreach ($procName in $IPMProcesses) {
    if (Get-Process $procName -ErrorAction SilentlyContinue) {
        Write-Host "Killing process: $procName" -ForegroundColor Cyan
        Stop-Process -Name $procName -Force -ErrorAction SilentlyContinue
    }
}

# Set system to High Performance and disable all sleep/hibernate timeouts
Write-Host "Configuring Power Settings for Production Training (Elevated)..." -ForegroundColor Cyan

$HighPerfGUID = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"

# Set active plan to High Performance
powercfg /setactive $HighPerfGUID

# Disable standby (sleep) timeouts
powercfg /x -standby-timeout-ac 0
powercfg /x -standby-timeout-dc 0

# Disable hibernation globally (requires admin, which we now have)
powercfg /h off

# Configure the CURRENT active plan as a fallback
powercfg /x -standby-timeout-ac 0
powercfg /x -standby-timeout-dc 0
powercfg /x -hibernate-timeout-ac 0
powercfg /x -hibernate-timeout-dc 0
powercfg /x -monitor-timeout-ac 0
powercfg /x -monitor-timeout-dc 0
powercfg /x -disk-timeout-ac 0
powercfg /x -disk-timeout-dc 0

# Disable monitor timeouts (optional, keeps display on)
powercfg /x -monitor-timeout-ac 0
powercfg /x -monitor-timeout-dc 0

# Disable disk idle timeout
powercfg /x -disk-timeout-ac 0
powercfg /x -disk-timeout-dc 0

Write-Host "Power configuration applied: High Performance, Standby: Never, Hibernate: Never." -ForegroundColor Green
