# RAG_07 - Multi-provider LLM Application with RAG Support

**Uniwersalna aplikacja LLM z interfejsem web** dla systemów RAG
(Retrieval-Augmented Generation), wieloma providerami i bazami wektorowymi.

## 🚀 Funkcjonalności

- **Multi-provider LLM**: OpenAI, Anthropic, Google, Ollama, OpenRouter, LM Studio
- **Vector Databases**: FAISS, Chroma, Pinecone (extensible architecture)
- **RAG System**: Retrieval-Augmented Generation z automatycznym chunkowaniem
- **Function Calling**: Zaawansowane iteracyjne odpytywanie z LLM
- **Web Interface**:
  - 🎨 **Streamlit Dashboard** - Interaktywny interfejs użytkownika
  - 📡 **FastAPI Backend** - RESTful API z dokumentacją
  - 🐳 **Docker Support** - Production-ready deployment
- **Collection Management**: Zarządzanie kolekcjami wektorowymi
- **Command Line Interface**: Intuitive CLI z pełną obsługą argumentów
- **Async Architecture**: Wszystkie operacje asynchroniczne z retry/timeout
- **Advanced Logging System**: JSON structured logging z rotacją plików
- **Configuration Management**: Centralized config z .env i JSON/YAML
- **Type Safety**: Pełne typowanie z mypy validation
- **Testing**: Comprehensive test suite z mockowaniem API

## 🌐 Web Interface

### Quick Start
```bash
# Uruchom cały system web
./run_web_system.sh

# Lub z Docker
./docker_start.sh
```

### Dostęp do aplikacji
- 🎨 **Streamlit Dashboard**: http://localhost:8501
- 📡 **FastAPI Backend**: http://localhost:8000
- 📋 **API Documentation**: http://localhost:8000/docs

## 📁 Struktura projektu (zgodnie z instrukcjami)

```
src/
├── main.py                 # Punkt wejściowy (tylko uruchamianie)
├── cli.py                  # Obsługa CLI
├── exceptions.py           # Dedykowane wyjątki
├── web/                   # Web interface
│   ├── api_server.py      # FastAPI backend
│   ├── streamlit_app.py   # Streamlit frontend
│   └── models.py          # Pydantic models dla API
├── services/              # Logika biznesowa
│   └── application_service.py
├── utils/                 # Funkcje pomocnicze
│   └── logger.py          # Structured logging
├── models/                # Modele danych
├── providers/             # Adaptery dla różnych API
│   ├── base.py           # Base interfaces + Factory
│   ├── llm/              # LLM providers
│   │   └── openai_provider.py
│   ├── vector/           # Vector DB providers
│   │   └── faiss_provider.py
│   └── text/             # Text processors
│       └── basic_processor.py
└── config/               # Konfiguracje
    └── config_manager.py  # Centralized config management

tests/                    # Testy jednostkowe (CLI + Web)
examples/                 # Przykładowe dane (gitignored)
databases/               # Lokalne bazy danych (gitignored)
config/                  # Pliki konfiguracyjne
docker/                  # Docker configuration
```

## 🛠 Skonfigurowane narzędzia formatowania

### Python

- **Black** - formatter kodu Python (line-length: 88)
- **isort** - sortowanie importów zgodnie z profilem Black
- **Pylint** - linting kodu Python
- **mypy** - sprawdzanie typów (opcjonalnie)
- **Ruff** - bardzo szybki linter/formatter

### TypeScript/JavaScript

- **Prettier** - formatter kodu JS/TS
- **ESLint** - linting z regułami TypeScript
- **TypeScript** - kompilator i sprawdzanie typów

## ⚡ Szybki start

### Option 1: Web Interface (Recommended)

```bash
# 1. Setup środowiska
./setup.sh

# 2. Konfiguracja API keys
cp .env .env.local
# Edytuj .env.local ze swoimi kluczami API

# 3. Uruchom web system
./run_web_system.sh
```

Dostęp do aplikacji:
- **Dashboard**: http://localhost:8501
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs

### Option 2: Docker Deployment

```bash
# 1. Konfiguracja
cp .env .env.local
# Edytuj .env.local

# 2. Start z Docker
./docker_start.sh

# 3. Production z nginx
./docker_start.sh --production
```

### Option 3: Command Line

```bash
# 1. Setup środowiska
./setup.sh

# 2. Konfiguracja
cp .env .env.local
# Dodaj swoje klucze API do .env.local

# 3. Pierwsza komenda
python src/main.py config-status
python src/main.py --help
```

## 📋 Dostępne komendy CLI

### Podstawowe operacje

```bash
# Query do LLM (z kontrolą logowania)
./run.sh query "What is Python?"
./run.sh --log-level WARNING query -p openai -m gpt-4 "Explain machine learning"

# Dodaj tekst do vector store
./run.sh embed "Python is a programming language"
./run.sh --no-log-console embed -p faiss -col documents "Your text here"

# Wyszukaj w vector store
./run.sh search "programming language"
./run.sh --log-level DEBUG search -p faiss -col documents -l 10 "machine learning"

# RAG query (z kontekstem)
./run.sh rag "What is Python used for?"
./run.sh --log-dir /custom/logs rag -p openai -vp faiss -cl 5 "Explain AI"

# Function Calling (zaawansowane)
./run.sh ask-with-tools "What are the main features of this system?" --verbose
./run.sh --log-level ERROR ask-with-tools "Question" --verbose  # Minimize logs
```

### Zarządzanie kolekcjami

```bash
# Lista kolekcji
./run.sh list-collections

# Informacje o kolekcji
./run.sh collection-info nazwa_kolekcji

# Automatyczne indeksowanie dokumentacji
./scripts/index_documentation.sh

# Demonstracja możliwości
./scripts/collections_demo.sh
```

### Zarządzanie systemem

```bash
# Status konfiguracji
./run.sh config-status

# Lista dostępnych providerów
./run.sh list-providers
./run.sh list-providers --provider-type llm

# Lista dostępnych modeli
./run.sh list-models
./run.sh list-models --provider openai --format table
```

## 📚 Dokumentacja zarządzania kolekcjami

### Szybki start

```bash
# 1. Sprawdź status
./run.sh config-status

# 2. Utwórz kolekcję z dokumentami
./run.sh embed --collection docs "$(cat README.md)"

# 3. Przetestuj
./run.sh ask-with-tools "What is this project about?" --verbose
```

### Pełna dokumentacja

- **[Zarządzanie kolekcjami](docs/collections_management.md)** - Kompletny
  przewodnik
- **[Szybki start](docs/quick_start_collections.md)** - Praktyczny przewodnik
- **Demonstracja**: `./scripts/collections_demo.sh` - Interaktywny tutorial

## 🧪 Automatyczne formatowanie VS Code

### VS Code Tasks (Ctrl+Shift+P → "Tasks: Run Task")

- **Setup Environment** - uruchamia setup.sh
- **Format All** - isort + black
- **Lint (Pylint)** - sprawdzanie kodu
- **Type Check (MyPy)** - sprawdzanie typów
- **Run Tests** - pytest z coverage
- **Run Application** - uruchamia aplikację z --help

### Ręczne formatowanie

```bash
# Python
source .venv/bin/activate
black src/              # Formatowanie Black
isort src/              # Sortowanie importów
pylint src/             # Linting
mypy src/               # Type checking
pytest                  # Testy

# JavaScript/TypeScript (jeśli używasz)
npm run format          # Formatowanie Prettier
npm run lint            # ESLint z automatycznymi poprawkami
```

## 🔧 Dodawanie nowych providerów

### 1. LLM Provider

```python
# src/providers/llm/my_provider.py
from providers.base import LLMProvider

class MyProvider(LLMProvider):
    async def initialize(self) -> None:
        # Inicjalizacja

    async def generate_text(self, prompt: str, **kwargs) -> str:
        # Implementacja
```

### 2. Rejestracja w Factory

```python
# Automatyczna rejestracja w providers/base.py
# Dodaj import w _register_default_providers()
```

### 3. Konfiguracja

```json
// config/app_config.json
{
  "llm_providers": [
    {
      "name": "my_provider",
      "api_key_env": "MY_PROVIDER_API_KEY",
      "base_url": "https://api.myprovider.com",
      "default_model": "my-model",
      "available_models": ["my-model", "my-model-pro"]
    }
  ]
}
```

## 🔐 Zmienne środowiskowe (.env)

```bash
# LLM API Keys
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
GOOGLE_API_KEY=your_google_key_here

# Logging Settings
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_DIR=logs                      # Custom log directory

# Application Settings
DEBUG=false
APP_NAME=rag_07

# Database Settings
DATABASE_PATH=databases/local.db
VECTOR_DB_PATH=databases/vector_store

# Provider Settings
DEFAULT_LLM_PROVIDER=openai
DEFAULT_VECTOR_DB_PROVIDER=faiss
```

## 🧪 Testowanie

```bash
# Uruchom wszystkie testy
pytest

# Z coverage
pytest --cov=src --cov-report=html

# Konkretny test
pytest tests/test_config_manager.py -v

# Test asynchroniczny
pytest tests/test_text_processor.py::TestBasicTextProcessor::test_chunk_text
```

## 📊 Wzorce projektowe zastosowane

- **Factory Pattern**: `ProviderFactory` dla tworzenia providerów
- **Strategy Pattern**: Wymienne algorytmy dla różnych providerów
- **Adapter Pattern**: Unified interface dla różnych API
- **Singleton Pattern**: `ConfigManager` jako centralny punkt konfiguracji
- **Template Method**: `BaseProvider` z wspólną strukturą
- **Dependency Injection**: Providers wstrzykiwane przez Factory

## 🔧 System logowania

### Hierarchia konfiguracji (priorytet malejący):

1. **CLI argumenty**: `--log-level DEBUG --no-log-console`
2. **Zmienne środowiskowe**: `LOG_LEVEL=WARNING LOG_DIR=/custom/logs`
3. **Plik konfiguracyjny**: `"log_level": "INFO"`
4. **Wartości domyślne**: `INFO` z konsolą i plikiem

### Opcje logowania:

```bash
# Kontrola poziomu
./run.sh --log-level DEBUG command      # Szczegółowe logi
./run.sh --log-level WARNING command    # Tylko ostrzeżenia+
./run.sh --log-level ERROR command      # Tylko błędy

# Kontrola wyjścia
./run.sh --no-log-console command       # Tylko do pliku
./run.sh --log-dir /custom/logs command # Własny katalog

# Kombinacje
export LOG_LEVEL=WARNING
./run.sh --log-dir /tmp/logs --no-log-console ask-with-tools "Question"
```

### Rotacja plików:

- **Lokalizacja**: `logs/rag_07.log`
- **Rotacja**: Codzienna o północy
- **Retencja**: 3 dni (automatyczne usuwanie)
- **Format**: JSON structured logs

📚 **Szczegółowa dokumentacja**: [System Logowania](docs/logging_system.md)

## 🎯 Cele architektoniczne

1. **Single Responsibility**: Każdy plik = jedna odpowiedzialność
2. **Elastyczność**: Łatwe dodawanie nowych providerów do arrays
3. **Centralizacja config**: Tylko ConfigManager czyta .env
4. **Async/await**: Wszystkie operacje API asynchroniczne
5. **Error Handling**: Dedicated exceptions + retry/timeout
6. **Observability**: Structured logging każdej operacji
7. **Type Safety**: Pełne typowanie + mypy validation

## 🚨 Ważne uwagi

- Foldery `examples/` i `databases/` są w .gitignore
- Tylko `ConfigManager` czyta .env, pozostałe otrzymują gotową konfigurację
- Każdy provider ma jednolity interfejs + jasną dokumentację parametrów
- Brak logiki w main.py/cli.py - tylko routing do services
- Testy pokrywają całość + mockowanie zewnętrznych API

## 🤝 Contributing

1. Dodaj testy dla nowej funkcjonalności
2. Uruchom `black src/ && isort src/` przed commitem
3. Sprawdź `pylint src/` i `mypy src/`
4. Dokumentuj parametry wejściowe providerów
5. Używaj structured logging w każdej operacji

## 📝 Zainstalowane rozszerzenia VS Code

```vscode-extensions
ms-python.python,ms-python.vscode-pylance,ms-python.black-formatter,ms-python.isort,ms-python.pylint,esbenp.prettier-vscode,dbaeumer.vscode-eslint,ms-toolsai.jupyter,github.copilot
```

---

✨ **Aplikacja gotowa do użycia i rozwijania!** ✨
