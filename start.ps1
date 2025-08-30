#!/usr/bin/env pwsh
# Latest API Buddy - Startup Script
# This script starts all services and performs basic health checks

Write-Host "🚀 Starting Latest API Buddy..." -ForegroundColor Cyan
Write-Host "=" * 60

# Start all services
Write-Host "📦 Starting Docker services..." -ForegroundColor Yellow
docker compose -f docker-compose.clean.yml up -d

# Wait for services to start
Write-Host "⏳ Waiting for services to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Health checks
Write-Host "🔍 Performing health checks..." -ForegroundColor Yellow

try {
    $health = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing | ConvertFrom-Json
    Write-Host "✅ Backend: $($health.status)" -ForegroundColor Green
    Write-Host "   Database: $($health.database)" -ForegroundColor Gray
    Write-Host "   Services:" -ForegroundColor Gray
    $health.services.PSObject.Properties | ForEach-Object {
        Write-Host "     $($_.Name): $($_.Value)" -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ Backend health check failed" -ForegroundColor Red
}

try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Frontend: Running" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Frontend check failed" -ForegroundColor Red
}

try {
    $providers = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/providers/" -UseBasicParsing | ConvertFrom-Json
    Write-Host "✅ API Providers: $($providers.Length) loaded" -ForegroundColor Green
} catch {
    Write-Host "❌ Providers check failed" -ForegroundColor Red
}

Write-Host ""
Write-Host "=" * 60
Write-Host "🎉 Latest API Buddy is ready!" -ForegroundColor Green
Write-Host "🌐 Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host "🔧 Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "📖 API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "❤️  Health Check: http://localhost:8000/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔍 Try searching for: 'create issue', 'kubernetes pods', 'datadog metrics'" -ForegroundColor Magenta
Write-Host "=" * 60 