param(
    [int]$IntervalSeconds = 30
)

# Use C# to access the PowerCreateRequest API for a formal system lock
$PowerRequestCode = @'
using System;
using System.Runtime.InteropServices;

public class PowerRequest
{
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    public struct REASON_CONTEXT
    {
        public uint Version;
        public uint Flags;
        public IntPtr Reason;
    }

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern IntPtr PowerCreateRequest(ref REASON_CONTEXT Context);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool PowerSetRequest(IntPtr PowerRequest, uint RequestType);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool PowerClearRequest(IntPtr PowerRequest, uint RequestType);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool CloseHandle(IntPtr hObject);

    // Request Types
    public const uint PowerRequestDisplayRequired = 0;
    public const uint PowerRequestSystemRequired = 1;
    public const uint PowerRequestAwayModeRequired = 2;
    public const uint PowerRequestExecutionRequired = 3;
}
'@

if (-not ([System.Management.Automation.PSTypeName]'PowerRequest').Type) {
    Add-Type -MemberDefinition $PowerRequestCode -Name "PowerRequest" -Namespace "Win32" -PassThru | Out-Null
}

Write-Host "Creating formal Power Request to block sleep..." -ForegroundColor Cyan

# Set up the reason context
$context = New-Object Win32.PowerRequest+REASON_CONTEXT
$context.Version = 0
$context.Flags = 1 # POWER_REQUEST_CONTEXT_SIMPLE_STRING
$reasonString = "Transformer Model Training in Progress"
$context.Reason = [System.Runtime.InteropServices.Marshal]::StringToHGlobalUni($reasonString)

# Create the request handle
$handle = [Win32.PowerRequest]::PowerCreateRequest([ref]$context)

if ($handle -eq [IntPtr]::Zero) {
    Write-Host "Failed to create Power Request. Falling back to old mechanism." -ForegroundColor Red
} else {
    # Set System, Display, and Execution required attributes
    [Win32.PowerRequest]::PowerSetRequest($handle, [Win32.PowerRequest]::PowerRequestSystemRequired) | Out-Null
    [Win32.PowerRequest]::PowerSetRequest($handle, [Win32.PowerRequest]::PowerRequestDisplayRequired) | Out-Null
    [Win32.PowerRequest]::PowerSetRequest($handle, [Win32.PowerRequest]::PowerRequestExecutionRequired) | Out-Null
    Write-Host "Power Request successfully registered. System locked awake." -ForegroundColor Green
}

# Legacy mechanism as a backup
$StateCode = @'
[DllImport("kernel32.dll", CharSet = CharSet.Auto, SetLastError = true)]
public static extern void SetThreadExecutionState(uint esFlags);
'@

if (-not ([System.Management.Automation.PSTypeName]'Win32.StayAwake').Type) {
    Add-Type -MemberDefinition $StateCode -Name "StayAwake" -Namespace "Win32"
}

$Flags = [uint32]0x80000043 # System + Display + AwayMode + Continuous

Write-Host "Keeping PC Awake (Interval: $IntervalSeconds s)..." -ForegroundColor Green

try {
    while ($true) {
        # Fallback assertion
        [Win32.StayAwake]::SetThreadExecutionState($Flags)
        
        # Re-assert power settings occasionally
        & ".\scripts\set_power_production.ps1" | Out-Null
        
        Start-Sleep -Seconds $IntervalSeconds
    }
}
finally {
    # Reset to normal
    [Win32.StayAwake]::SetThreadExecutionState([uint32]0x80000000)
    
    if ($handle -ne [IntPtr]::Zero) {
        [Win32.PowerRequest]::PowerClearRequest($handle, [Win32.PowerRequest]::PowerRequestSystemRequired) | Out-Null
        [Win32.PowerRequest]::PowerClearRequest($handle, [Win32.PowerRequest]::PowerRequestDisplayRequired) | Out-Null
        [Win32.PowerRequest]::PowerClearRequest($handle, [Win32.PowerRequest]::PowerRequestExecutionRequired) | Out-Null
        [Win32.PowerRequest]::CloseHandle($handle) | Out-Null
    }
    [System.Runtime.InteropServices.Marshal]::FreeHGlobal($context.Reason)
    
    Write-Host "Power Request released. PC can sleep normally." -ForegroundColor Cyan
}
