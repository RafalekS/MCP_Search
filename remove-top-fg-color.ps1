# remove-top-fg-color.ps1
# Remove top_fg_color from all theme JSON files

Set-Location $PSScriptRoot

Write-Host "Fixing theme JSON files..." -ForegroundColor Yellow

$fixed = 0
$errors = 0

Get-ChildItem -Path "themes\*.json" | ForEach-Object {
    try {
        $content = Get-Content $_.FullName -Raw | ConvertFrom-Json

        if ($content.CTkFrame.PSObject.Properties.Name -contains "top_fg_color") {
            # Remove the property
            $content.CTkFrame.PSObject.Properties.Remove("top_fg_color")

            # Write back
            $content | ConvertTo-Json -Depth 100 | Set-Content $_.FullName

            Write-Host "✓ Fixed: $($_.Name)" -ForegroundColor Green
            $fixed++
        }
    }
    catch {
        Write-Host "✗ Error in $($_.Name): $_" -ForegroundColor Red
        $errors++
    }
}

Write-Host "`nFixed $fixed theme files" -ForegroundColor Cyan
if ($errors -gt 0) {
    Write-Host "Errors: $errors files" -ForegroundColor Red
}

Write-Host "`nNow try: python MCP_Search.pyw" -ForegroundColor Cyan
