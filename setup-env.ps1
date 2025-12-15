# PowerShell script to setup environment variables

Write-Host "Setting up environment variables..." -ForegroundColor Cyan

# Check if .env already exists
if (Test-Path .env) {
    $overwrite = Read-Host ".env file already exists! Overwrite? (y/N)"
    if ($overwrite -ne "y" -and $overwrite -ne "Y") {
        Write-Host "Cancelled." -ForegroundColor Yellow
        exit
    }
}

# Prompt for API keys
Write-Host ""
$grokKeys = Read-Host "Enter your Grok API keys (comma-separated if multiple)"

# Set default backend URL
$backendUrl = Read-Host "Backend URL [http://localhost:8000]"
if ([string]::IsNullOrWhiteSpace($backendUrl)) {
    $backendUrl = "http://localhost:8000"
}

# Create .env file
@"
# Grok API Keys (comma-separated if multiple)
GROK_API_KEYS=$grokKeys

# Backend URL
BACKEND_URL=$backendUrl
"@ | Out-File -FilePath .env -Encoding utf8

Write-Host ""
Write-Host "✅ .env file created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "You can now run: docker-compose up -d" -ForegroundColor Cyan
