# RAG_07 - Multi-provider LLM Application with RAG Support

**Uniwersalna baza aplikacji command line** dla systemów LLM z obsługą RAG (Retrieval-Augmented Generation), wieloma providerami i bazami wektorowymi.

## 🚀 Funkcjonalności

- **Multi-provider LLM**: OpenAI, Anthropic, Google (łatwe dodawanie nowych)
- **Vector Databases**: FAISS, Chroma, Pinecone (extensible architecture)
- **RAG System**: Retrieval-Augmented Generation z automatycznym chunkowaniem tekstu
- **Command Line Interface**: Intuitive CLI z pełną obsługą argumentów
- **Async Architecture**: Wszystkie operacje asynchroniczne z retry/timeout
- **Structured Logging**: JSON logging z pełnym śledzeniem operacji
- **Configuration Management**: Centralized config z .env i JSON/YAML
- **Type Safety**: Pełne typowanie z mypy validation
- **Testing**: Comprehensive test suite z mockowaniem API

## 📁 Struktura projektu (zgodnie z instrukcjami)

```
src/
├── main.py                 # Punkt wejściowy (tylko uruchamianie)
├── cli.py                  # Obsługa CLI
├── exceptions.py           # Dedykowane wyjątki
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

tests/                    # Testy jednostkowe
examples/                 # Przykładowe dane (gitignored)
databases/               # Lokalne bazy danych (gitignored)
config/                  # Pliki konfiguracyjne
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

### 1. Setup środowiska
```bash
# Uruchom setup script
./setup.sh

# Lub ręcznie:
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Konfiguracja
```bash
# Edytuj .env z kluczami API
cp .env .env.local
# Dodaj swoje klucze API do .env.local
```

### 3. Pierwsza komenda
```bash
# Sprawdź status konfiguracji
python src/main.py config-status

# Pokaż pomoc
python src/main.py --help
```

## 📋 Dostępne komendy CLI

### Podstawowe operacje
```bash
# Query do LLM
python src/main.py query "What is Python?"
python src/main.py query -p openai -m gpt-4 "Explain machine learning"

# Dodaj tekst do vector store
python src/main.py embed "Python is a programming language"
python src/main.py embed -p faiss -col documents "Your text here"

# Wyszukaj w vector store
python src/main.py search "programming language"
python src/main.py search -p faiss -col documents -l 10 "machine learning"

# RAG query (z kontekstem)
python src/main.py rag "What is Python used for?"
python src/main.py rag -p openai -vp faiss -cl 5 "Explain AI"
```

### Zarządzanie
```bash
# Status konfiguracji
python src/main.py config-status

# Lista dostępnych providerów
python src/main.py list-providers
python src/main.py list-providers --provider-type llm
```

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

# Application Settings
LOG_LEVEL=INFO
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
