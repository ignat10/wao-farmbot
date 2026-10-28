# Run from any directory: & 'C:\tap_scripts\run-main.ps1' -Instance 'LDPlayer'
# Stop with Ctrl+C. A nonzero exit code triggers a restart.
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateNotNullOrEmpty()]
    [string]$Instance,

    [ValidateRange(1, 3600)]
    [int]$RestartDelaySeconds = 5
)

$ErrorActionPreference = 'Stop'
$pythonExe = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
$mainScript = Join-Path $PSScriptRoot 'src\main.py'
foreach ($requiredFile in @($pythonExe, $mainScript)) {
    if (-not (Test-Path -LiteralPath $requiredFile -PathType Leaf)) {
        throw "File not found: $requiredFile"
    }
}

$oldPythonPath = $env:PYTHONPATH
$oldPythonIoEncoding = $env:PYTHONIOENCODING
$oldConsoleEncoding = [Console]::OutputEncoding
$ctrlCHandler = [ConsoleCancelEventHandler] {
    param($sender, $eventArgs)
    # Keep PowerShell's pipeline alive long enough to receive Python's traceback.
    # The same Ctrl+C event is still delivered to Python as SIGINT.
    if ($eventArgs.SpecialKey -eq [ConsoleSpecialKey]::ControlC) {
        $eventArgs.Cancel = $true
    }
}
[Console]::add_CancelKeyPress($ctrlCHandler)
Push-Location -LiteralPath $PSScriptRoot
try {
    # main.py also imports src.*; make the project root available to Python.
    $env:PYTHONPATH = $PSScriptRoot
    if ($oldPythonPath) { $env:PYTHONPATH += [IO.Path]::PathSeparator + $oldPythonPath }
    $env:PYTHONIOENCODING = 'utf-8'
    [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
    # PowerShell 7: handle failures using the process exit code below.
    $PSNativeCommandUseErrorActionPreference = $false
    # Windows PowerShell removes quote characters in arguments sent to native apps.
    # Backslashes preserve the Python string quotes passed to `python -c`.
    $pythonBootstrap = @'
import runpy
import signal
import sys
import traceback
import os

# Keep Python tracebacks on PowerShell's output stream instead of ErrorRecord objects.
sys.stderr = sys.stdout

def trim_traceback(tb):
    script_name = os.path.normcase(os.path.abspath(script_path))
    while tb is not None:
        filename = os.path.normcase(os.path.abspath(tb.tb_frame.f_code.co_filename))
        if filename == script_name:
            return tb
        tb = tb.tb_next
    return None

def show_exception(exc_type, exc_value, exc_traceback):
    trimmed_traceback = trim_traceback(exc_traceback)
    traceback.print_exception(
        exc_type,
        exc_value,
        trimmed_traceback,
        file=sys.stderr,
    )

def show_traceback_and_interrupt(signum, frame):
    print(\"\nCtrl+C received. Python traceback:\", file=sys.stderr, flush=True)
    stack = traceback.extract_stack(frame)
    script_name = os.path.normcase(os.path.abspath(script_path))
    for index, stack_frame in enumerate(stack):
        if os.path.normcase(os.path.abspath(stack_frame.filename)) == script_name:
            stack = stack[index:]
            break
    traceback.print_list(stack, file=sys.stderr)
    raise SystemExit(130)

signal.signal(signal.SIGINT, show_traceback_and_interrupt)
script_path = sys.argv[1]
sys.argv = [script_path, *sys.argv[2:]]
sys.excepthook = show_exception
runpy.run_path(script_path, run_name=\"__main__\")
'@

    while ($true) {
        Write-Host "Starting main.py; instance=$Instance"
        # Windows PowerShell 5.1 represents redirected stderr as ErrorRecord.
        # Continue lets Python finish and preserves its real exit code.
        $ErrorActionPreference = 'Continue'
        try {
            & $pythonExe -u -c $pythonBootstrap $mainScript $Instance 2>&1 | ForEach-Object {
                $line = $_.ToString()
                Write-Host $line
            }
            $exitCode = $LASTEXITCODE
        }
        finally {
            $ErrorActionPreference = 'Stop'
        }

        if ($exitCode -eq 0) {
            Write-Host 'Finished successfully (exit code 0).'
            break
        }
        # Do not restart after a keyboard interrupt.
        if ($exitCode -eq -1073741510 -or $exitCode -eq 130) {
            Write-Host "Interrupted (exit code $exitCode)."
            break
        }
        Write-Host "Failed (exit code $exitCode). Restarting in $RestartDelaySeconds seconds."
        Start-Sleep -Seconds $RestartDelaySeconds
    }
}
finally {
    [Console]::remove_CancelKeyPress($ctrlCHandler)
    $env:PYTHONPATH = $oldPythonPath
    $env:PYTHONIOENCODING = $oldPythonIoEncoding
    [Console]::OutputEncoding = $oldConsoleEncoding
    Pop-Location
}
