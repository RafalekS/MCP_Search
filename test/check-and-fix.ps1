# check-and-fix.ps1
# Check if theme_frame.py has the bug and force sync if needed

Set-Location $PSScriptRoot

Write-Host "Checking theme_frame.py for top_fg_color bug..." -ForegroundColor Yellow

# Check if the bug exists
$bugExists = Select-String -Path "theme_frame.py" -Pattern "widget.configure\(top_fg_color" -Quiet

if ($bugExists) {
    Write-Host "BUG FOUND! Forcing clean sync from remote..." -ForegroundColor Red

    # Stash any local changes
    git stash

    # Force reset to remote
    git fetch origin
    git reset --hard origin/claude/analyze-and-finish-011CUoY3DpifWRTKxmGHVzHD

    # Remove Python cache
    Get-ChildItem -Path . -Include __pycache__,*.pyc -Recurse -Force | Remove-Item -Force -Recurse

    Write-Host "`nFIXED! Checking again..." -ForegroundColor Green

    # Verify fix
    $stillBroken = Select-String -Path "theme_frame.py" -Pattern "widget.configure\(top_fg_color" -Quiet

    if ($stillBroken) {
        Write-Host "STILL BROKEN - manual intervention needed" -ForegroundColor Red
    } else {
        Write-Host "✓ Bug removed! theme_frame.py is clean" -ForegroundColor Green
    }
} else {
    Write-Host "✓ No bug found - theme_frame.py is already fixed" -ForegroundColor Green
}

Write-Host "`nTry running: python MCP_Search.pyw" -ForegroundColor Cyan
