# 🛠️ Manual Docker Build Guide

If the automated scripts are hanging, use these manual steps:

## 🔍 **Step 1: Verify Docker is Running**

1. Open Docker Desktop
2. Wait for it to fully start (green status)
3. Open a new PowerShell window

## 🧹 **Step 2: Clean Up**

```powershell
# Stop all containers
docker-compose down

# Remove old images
docker system prune -f

# Remove specific images if needed
docker rmi $(docker images -q latest_api_project_backend) -f
```

## 🔨 **Step 3: Build Step by Step**

```powershell
# Build only the backend (this should work)
docker-compose build --no-cache backend

# If successful, start services one by one
docker-compose up -d postgres
docker-compose up -d redis  
docker-compose up -d elasticsearch

# Wait for services to be healthy, then start backend
docker-compose up -d backend
```

## 🧪 **Step 4: Test the Build**

```powershell
# Check if containers are running
docker-compose ps

# Check backend logs
docker-compose logs backend

# Test the API
curl http://localhost:8000/health
```

## 🚨 **If Build Still Hangs**

1. **Check Docker Desktop**: Make sure it's running and healthy
2. **Restart Docker**: Sometimes a restart fixes hanging issues
3. **Check Resources**: Ensure Docker has enough memory/CPU
4. **Use Docker Desktop UI**: Build through the Docker Desktop interface instead

## 💡 **Alternative: Build Without Docker Compose**

```powershell
# Build directly with Docker
cd backend
docker build -t mcp-backend .

# Run the container
docker run -p 8000:8000 mcp-backend
```

## 📞 **Still Having Issues?**

- Check Docker Desktop logs
- Ensure Windows Defender isn't blocking Docker
- Try running PowerShell as Administrator
- Check if antivirus is interfering with Docker
