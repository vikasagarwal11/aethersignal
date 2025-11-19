# AetherSignal - Server Status Check
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AetherSignal - Server Status Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$port = 8501
$url = "http://localhost:$port"

try {
    $response = Invoke-WebRequest -Uri $url -TimeoutSec 2 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ Server is RUNNING!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Local URL: $url" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Open in browser: $url" -ForegroundColor Cyan
    }
} catch {
    Write-Host "✗ Server is NOT running" -ForegroundColor Red
    Write-Host ""
    Write-Host "To start the server, run:" -ForegroundColor Yellow
    Write-Host "  start_server.bat" -ForegroundColor White
    Write-Host "  OR" -ForegroundColor White
    Write-Host "  scripts\start_server.bat" -ForegroundColor White
    Write-Host "  OR" -ForegroundColor White
    Write-Host "  streamlit run app.py --server.port=8501" -ForegroundColor White
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

