# Build and Test Script for MCP-Based API Documentation System
# PowerShell script for Windows

Write-Host "🚀 Building and Testing MCP-Based API Documentation System" -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Cyan

# Check if Docker is running
Write-Host "🔍 Checking Docker status..." -ForegroundColor Yellow
try {
    docker version | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Stop existing containers
Write-Host "🛑 Stopping existing containers..." -ForegroundColor Yellow
docker-compose down

# Remove old images
Write-Host "🧹 Cleaning up old images..." -ForegroundColor Yellow
docker system prune -f

# Build the backend
Write-Host "🔨 Building backend Docker image..." -ForegroundColor Yellow
docker-compose build backend

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Backend build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Backend built successfully" -ForegroundColor Green

# Start the services
Write-Host "🚀 Starting services..." -ForegroundColor Yellow
docker-compose up -d postgres redis elasticsearch

# Wait for services to be healthy
Write-Host "⏳ Waiting for services to be healthy..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Start the backend
Write-Host "🤖 Starting backend..." -ForegroundColor Yellow
docker-compose up -d backend

# Wait for backend to be ready
Write-Host "⏳ Waiting for backend to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 20

# Test the backend
Write-Host "🧪 Testing backend..." -ForegroundColor Yellow

# Test health endpoint
Write-Host "🔍 Testing health endpoint..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
    Write-Host "✅ Health check passed: $($response.status)" -ForegroundColor Green
} catch {
    Write-Host "❌ Health check failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test root endpoint
Write-Host "🔍 Testing root endpoint..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/" -Method Get
    Write-Host "✅ Root endpoint working: $($response.name)" -ForegroundColor Green
} catch {
    Write-Host "❌ Root endpoint failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test AI status endpoint
Write-Host "🔍 Testing AI status endpoint..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/ai/status" -Method Get
    Write-Host "✅ AI status working: $($response.total_conversations) conversations" -ForegroundColor Green
} catch {
    Write-Host "❌ AI status failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test AI query endpoint
Write-Host "🔍 Testing AI query endpoint..." -ForegroundColor Cyan
try {
    $body = @{
        query = "How do I search for API endpoints?"
        context = @{}
        session_id = "test-session-123"
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "http://localhost:8000/ai/query" -Method Post -Body $body -ContentType "application/json"
    Write-Host "✅ AI query working: Intent detected: $($response.intent.type)" -ForegroundColor Green
} catch {
    Write-Host "❌ AI query failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Show running containers
Write-Host "📊 Container Status:" -ForegroundColor Cyan
docker-compose ps

Write-Host "`n🎉 Testing completed!" -ForegroundColor Green
Write-Host "📖 API Documentation available at: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "🔍 Health check available at: http://localhost:8000/health" -ForegroundColor Cyan
Write-Host "🤖 AI endpoints available at: http://localhost:8000/ai/*" -ForegroundColor Cyan

Write-Host "`n💡 To stop services, run: docker-compose down" -ForegroundColor Yellow
Write-Host "💡 To view logs, run: docker-compose logs -f backend" -ForegroundColor Yellow
