# force-restore.ps1
# Force restore all files from remote repository

Set-Location $PSScriptRoot

Write-Host "Restoring deleted files..." -ForegroundColor Yellow

# Reset the index and restore all deleted files
git reset HEAD --hard

# Clean any untracked files
git clean -fd

# Force checkout from remote
git fetch origin
git reset --hard origin/claude/analyze-and-finish-011CUoY3DpifWRTKxmGHVzHD

Write-Host "Files restored!" -ForegroundColor Green

# List the restored files
Write-Host "`nChecking for required files:" -ForegroundColor Cyan
if (Test-Path "theme_frame.py") { Write-Host "✓ theme_frame.py exists" -ForegroundColor Green } else { Write-Host "✗ theme_frame.py MISSING" -ForegroundColor Red }
if (Test-Path "tools.py") { Write-Host "✓ tools.py exists" -ForegroundColor Green } else { Write-Host "✗ tools.py MISSING" -ForegroundColor Red }

Write-Host "`nDone! Try running: python MCP_Search.pyw" -ForegroundColor Cyan
