# Unified Runner for Overnight Hybrid NIDS Production
# Combines keep_awake.ps1 logic with train_production.py

# 1. Define the Keep-Awake Logic (Embedded for simplicity)
$PowerRequestCode = @'
using System;
using System.Runtime.InteropServices;

public class PowerRequest
{
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    public struct REASON_CONTEXT { public uint Version; public uint Flags; public IntPtr Reason; }

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern IntPtr PowerCreateRequest(ref REASON_CONTEXT Context);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool PowerSetRequest(IntPtr PowerRequest, uint RequestType);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool PowerClearRequest(IntPtr PowerRequest, uint RequestType);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool CloseHandle(IntPtr hObject);

    public const uint PowerRequestDisplayRequired = 0;
    public const uint PowerRequestSystemRequired = 1;
    public const uint PowerRequestExecutionRequired = 3;
}
'@

Add-Type -MemberDefinition $PowerRequestCode -Name "PowerRequest" -Namespace "Win32" -ErrorAction SilentlyContinue

Write-Host "--- OVERNIGHT PRODUCTION RUN INITIALIZED ---" -ForegroundColor Cyan
Write-Host "Enforcing System Awake State..." -ForegroundColor Green

# Set up the reason context
$context = New-Object Win32.PowerRequest+REASON_CONTEXT
$context.Version = 0
$context.Flags = 1 
$reasonString = "Hybrid NIDS 17M Production Training"
$context.Reason = [System.Runtime.InteropServices.Marshal]::StringToHGlobalUni($reasonString)

$handle = [Win32.PowerRequest]::PowerCreateRequest([ref]$context)
[Win32.PowerRequest]::PowerSetRequest($handle, [Win32.PowerRequest]::PowerRequestSystemRequired) | Out-Null
[Win32.PowerRequest]::PowerSetRequest($handle, [Win32.PowerRequest]::PowerRequestExecutionRequired) | Out-Null

try {
    Write-Host "Starting 17-hour Production Training..." -ForegroundColor Yellow
    
    # 2. RUN THE TRAINING
    .\venv\Scripts\python.exe -m src.training.train_production
    
    Write-Host "Training Completed Successfully." -ForegroundColor Green
}
catch {
    Write-Host "Training encountered an error: $_" -ForegroundColor Red
}
finally {
    # 3. CLEANUP
    if ($handle -ne [IntPtr]::Zero) {
        [Win32.PowerRequest]::PowerClearRequest($handle, [Win32.PowerRequest]::PowerRequestSystemRequired) | Out-Null
        [Win32.PowerRequest]::PowerClearRequest($handle, [Win32.PowerRequest]::PowerRequestExecutionRequired) | Out-Null
        [Win32.PowerRequest]::CloseHandle($handle) | Out-Null
    }
    [System.Runtime.InteropServices.Marshal]::FreeHGlobal($context.Reason)
    
    Write-Host "Power Request released. PC can sleep normally." -ForegroundColor Cyan
    Write-Host "--- END OF PRODUCTION LOG ---"
}
