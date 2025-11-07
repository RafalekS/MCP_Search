# Find and remove the API key from the validation JSON
$file = "debug_results/validation/validation_results_20251105_135415.json"
$content = Get-Content $file -Raw
# Remove the API key pattern (OpenAI keys start with sk-)
$content = $content -replace 'sk-[a-zA-Z0-9]{48}', 'REDACTED'
Set-Content $file $content

# Now stage and commit everything
git add debug_results/validation/
git add debug_results/results/
git add debug_results/logs/

git commit -m "Add validation results (API keys redacted)"

git push origin claude/analyze-and-finish-011CUoY3DpifWRTKxmGHVzHD