# RAG_07 Web Interface Documentation

## 🌐 Overview

RAG_07 provides a modern web interface consisting of:
- **FastAPI Backend**: RESTful API for RAG operations
- **Streamlit Frontend**: Interactive dashboard for users
- **Docker Support**: Production-ready containerization
- **Nginx Proxy**: Load balancing and SSL termination

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │    FastAPI      │    │   Application   │
│   Frontend      │───▶│    Backend      │───▶│    Services     │
│   (Port 8501)   │    │   (Port 8000)   │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         │              │     Redis       │              │
         └──────────────│  (Port 6379)    │──────────────┘
                        │   [Caching]     │
                        └─────────────────┘
                                 │
                        ┌─────────────────┐
                        │  Vector DBs     │
                        │ (FAISS/Chroma)  │
                        └─────────────────┘
```

## 🚀 Quick Start

### Local Development

1. **Setup Environment**
   ```bash
   ./setup.sh
   ```

2. **Configure API Keys**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Start Web System**
   ```bash
   ./run_web_system.sh
   ```

4. **Access Applications**
   - Streamlit Dashboard: http://localhost:8501
   - FastAPI Backend: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Docker Deployment

1. **Start with Docker Compose**
   ```bash
   ./docker_start.sh
   ```

2. **Production with Nginx**
   ```bash
   ./docker_start.sh --production
   ```

## 📡 FastAPI Backend

### API Endpoints

#### Health Check
```http
GET /api/health
```
Response:
```json
{
  "status": "healthy",
  "service": "RAG_07 API",
  "version": "1.0.0",
  "providers_status": {
    "llm_provider": "openai",
    "vector_provider": "faiss"
  }
}
```

#### Available Models
```http
GET /api/models
```
Response:
```json
{
  "providers": {
    "openai": ["gpt-4", "gpt-3.5-turbo"],
    "anthropic": ["claude-3.5-sonnet", "claude-3-haiku"]
  },
  "default_providers": {
    "llm": "openai",
    "vector": "faiss"
  }
}
```

#### Simple Query
```http
POST /api/query/simple
```
Request:
```json
{
  "query": "What is artificial intelligence?",
  "provider": "openai",
  "model": "gpt-4"
}
```
Response:
```json
{
  "result": "Artificial intelligence (AI) refers to...",
  "processing_time": 1.23,
  "provider_used": "openai",
  "model_used": "gpt-4"
}
```

#### RAG Query
```http
POST /api/query/rag
```
Request:
```json
{
  "question": "What are the main features of RAG_07?",
  "llm_provider": "openai",
  "vector_provider": "faiss",
  "collection": "default",
  "max_results": 5,
  "use_function_calling": true,
  "max_iterations": 5
}
```
Response:
```json
{
  "answer": "RAG_07 is a multi-provider system...",
  "sources_used": ["doc1.txt", "doc2.md"],
  "function_calls": [{"name": "search_vectors", "args": {...}}],
  "processing_time": 2.45,
  "iterations_used": 1,
  "metadata": {
    "function_calling_used": true,
    "context_count": 3
  }
}
```

#### Add Text to Vector Store
```http
POST /api/vectors/add
```
Request:
```json
{
  "text": "RAG_07 is a powerful system for...",
  "provider": "faiss",
  "collection": "default",
  "metadata": {"source": "manual_input"}
}
```
Response:
```json
{
  "document_id": "doc_12345",
  "collection": "default",
  "processing_time": 0.45
}
```

#### Search Vector Store
```http
POST /api/vectors/search
```
Request:
```json
{
  "query": "RAG system features",
  "provider": "faiss",
  "collection": "default",
  "limit": 5
}
```
Response:
```json
{
  "results": [
    "RAG_07 provides multi-provider support...",
    "The system includes vector databases..."
  ],
  "processing_time": 0.32,
  "collection": "default"
}
```

### Error Handling

All endpoints return standardized error responses:

```json
{
  "error": "ValidationError",
  "message": "Query cannot be empty",
  "details": {
    "field": "query",
    "code": "empty_value"
  }
}
```

HTTP Status Codes:
- `200`: Success
- `400`: Validation Error
- `500`: Internal Server Error

## 🎨 Streamlit Frontend

### Features

#### Main Interface
- **Chat Tab**: Interactive Q&A with RAG
- **Vector Search Tab**: Direct vector database search
- **Add Documents Tab**: Upload and add content

#### Configuration Sidebar
- Provider selection (LLM and Vector DB)
- Collection management
- Advanced settings (function calling, iterations)
- Session statistics

#### Chat Features
- Example questions for quick start
- Conversation history with export
- Real-time processing indicators
- Source citation display

#### Document Management
- Text input for manual content
- File upload support (.txt, .md, .py, .json)
- Vector database integration

### Configuration

Environment variables for Streamlit:
```bash
API_BASE_URL=http://localhost:8000
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

## 🐳 Docker Deployment

### Services

#### rag-api (FastAPI Backend)
```yaml
services:
  rag-api:
    build:
      dockerfile: docker/Dockerfile.api
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    volumes:
      - ./databases:/app/data
      - ./config:/app/config
```

#### rag-dashboard (Streamlit Frontend)
```yaml
  rag-dashboard:
    build:
      dockerfile: docker/Dockerfile.streamlit
    ports:
      - "8501:8501"
    environment:
      - API_BASE_URL=http://rag-api:8000
    depends_on:
      rag-api:
        condition: service_healthy
```

#### redis (Caching)
```yaml
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
```

#### nginx (Production Proxy)
```yaml
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./docker/nginx.conf:/etc/nginx/nginx.conf:ro
    profiles:
      - production
```

### Deployment Commands

```bash
# Basic deployment
docker-compose up -d

# Development with nginx
docker-compose --profile development up -d

# Production with SSL
docker-compose --profile production up -d

# Build and start
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Update services
docker-compose pull && docker-compose up -d
```

## 🔧 Configuration

### Environment Variables

Create `.env` file:
```bash
# LLM Provider API Keys
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
GOOGLE_API_KEY=your-google-key
OPENROUTER_API_KEY=sk-or-your-openrouter-key

# Application Settings
LOG_LEVEL=INFO
DEBUG=false

# Database Settings
VECTOR_DB_TYPE=faiss
DEFAULT_COLLECTION=default

# Optional: Custom endpoints
OLLAMA_BASE_URL=http://localhost:11434
LMSTUDIO_BASE_URL=http://localhost:1234
```

### Nginx Configuration

For production deployment with custom domains:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://rag-dashboard:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support for Streamlit
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /api/ {
        proxy_pass http://rag-api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🧪 Testing

### Run Tests
```bash
# Test web components
./test_web_system.sh

# Run specific tests
python -m pytest tests/test_web_api.py -v
python -m pytest tests/test_web_streamlit.py -v

# Test with coverage
python -m pytest tests/test_web_*.py --cov=src.web --cov-report=html
```

### Integration Testing
```bash
# Start system and test endpoints
./run_web_system.sh &
sleep 10

# Test health
curl http://localhost:8000/api/health

# Test models
curl http://localhost:8000/api/models

# Test simple query
curl -X POST http://localhost:8000/api/query/simple \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'
```

## 📊 Monitoring

### Health Checks
- API Health: `http://localhost:8000/api/health`
- Streamlit Health: `http://localhost:8501/_stcore/health`
- Redis Health: `redis-cli ping`

### Logs
```bash
# View all logs
docker-compose logs -f

# Specific service logs
docker-compose logs -f rag-api
docker-compose logs -f rag-dashboard

# Local development logs
tail -f logs/rag_07.log
```

### Metrics
- Response times in API responses
- Session statistics in Streamlit
- Container resource usage via Docker stats

## 🔒 Security

### API Security
- CORS configuration for frontend integration
- Input validation with Pydantic models
- Error handling without information leakage
- Request timeouts and rate limiting (configurable)

### Production Security
- Environment variable for sensitive data
- Nginx proxy with SSL termination
- Network isolation with Docker networks
- Read-only file system where possible

### Best Practices
- Use secrets management for API keys
- Regular dependency updates
- Monitor for security vulnerabilities
- Implement proper authentication (custom extension)

## 🚀 Performance

### Optimization Tips
- Use Redis for caching frequent queries
- Configure appropriate timeouts
- Enable connection pooling
- Use production WSGI server (uvicorn)

### Scaling
- Run multiple API instances behind nginx
- Use Redis cluster for distributed caching
- Implement database connection pooling
- Add horizontal scaling with Docker Swarm/Kubernetes

## 🛠️ Troubleshooting

### Common Issues

1. **API Not Starting**
   ```bash
   # Check configuration
   python -m src.web.api_server --help

   # View detailed logs
   python -m src.web.api_server 2>&1 | tee api.log
   ```

2. **Streamlit Connection Error**
   ```bash
   # Check API availability
   curl http://localhost:8000/api/health

   # Update API_BASE_URL in environment
   export API_BASE_URL=http://your-api-host:8000
   ```

3. **Docker Build Issues**
   ```bash
   # Clean Docker cache
   docker system prune -a

   # Rebuild without cache
   docker-compose build --no-cache
   ```

4. **Provider Configuration**
   ```bash
   # Check configuration status
   python src/main.py config-status

   # Verify API keys
   python -c "import os; print(os.getenv('OPENAI_API_KEY', 'Not set'))"
   ```

### Debug Mode
```bash
# Start API in debug mode
DEBUG=true python -m src.web.api_server

# Start Streamlit in debug mode
streamlit run src/web/streamlit_app.py --logger.level=debug
```

## 📚 API Client Examples

### Python Client
```python
import requests

class RAG07Client:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url

    def ask_question(self, question, use_rag=True):
        if use_rag:
            response = requests.post(
                f"{self.base_url}/api/query/rag",
                json={"question": question}
            )
        else:
            response = requests.post(
                f"{self.base_url}/api/query/simple",
                json={"query": question}
            )
        return response.json()

# Usage
client = RAG07Client()
result = client.ask_question("What is RAG_07?")
print(result["answer"])
```

### JavaScript Client
```javascript
class RAG07Client {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }

    async askQuestion(question, useRag = true) {
        const endpoint = useRag ? '/api/query/rag' : '/api/query/simple';
        const payload = useRag ? { question } : { query: question };

        const response = await fetch(`${this.baseUrl}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        return response.json();
    }
}

// Usage
const client = new RAG07Client();
client.askQuestion('What is RAG_07?').then(result => {
    console.log(result.answer);
});
```

---

## 🎯 Next Steps

1. **Add Authentication**: Implement user authentication and authorization
2. **Real-time Features**: Add WebSocket support for streaming responses
3. **Advanced UI**: Enhance Streamlit interface with custom components
4. **Monitoring**: Add comprehensive metrics and alerting
5. **Deployment**: Configure CI/CD pipelines for automated deployment
