# Plan Implementacji RAG_07 - Rozszerzenie Funkcjonalności

## Aktualizacja z 25.07.2025

### Status Aktualny
- ✅ Podstawowa architektura RAG z Factory pattern
- ✅ Providery: OpenAI, Anthropic, FAISS, Basic Text Processor
- ✅ CLI z komendami: query, embed, search, rag, config-status, list-providers
- ✅ Testy jednostkowe (9/9 przechodzą)
- ✅ Strukturyzowane logowanie z structlog
- ✅ Konfiguracja JSON z wieloma providerami

### Zadania do Realizacji

## 1. Rozszerzenie Providerów (Faza 1)

### 1.1 Nowe LLM Providery
- [ ] **Google Gemini Provider** (`src/providers/llm/google_provider.py`)
  - Model: gemini-pro, gemini-pro-vision
  - API: Google Generative AI
  - Testy: `tests/test_google_provider.py`

- [ ] **OpenRouter Provider** (`src/providers/llm/openrouter_provider.py`)
  - Agregator różnych modeli (Claude, GPT, inne)
  - API: OpenRouter
  - Testy: `tests/test_openrouter_provider.py`

- [ ] **Ollama Provider** (`src/providers/llm/ollama_provider.py`)
  - Lokalne modele LLM
  - API: http://192.168.1.11:11434
  - Testy: `tests/test_ollama_provider.py`

- [ ] **LM Studio Provider** (`src/providers/llm/lmstudio_provider.py`)
  - Lokalne modele przez LM Studio
  - API: http://192.168.1.11:1234
  - Testy: `tests/test_lmstudio_provider.py`

### 1.2 Rozszerzenie Vector DB Providerów
- [ ] **Chroma Provider** (`src/providers/vector/chroma_provider.py`)
  - Implementacja kompletnej funkcjonalności
  - Kolekcje, metadata, persistence
  - Testy: `tests/test_chroma_provider.py`

- [ ] **Podgląd zawartości baz** (dla wszystkich providerów)
  - Metody: `list_collections()`, `get_collection_info()`, `browse_vectors()`
  - CLI komendy: `list-collections`, `browse-collection`

### 1.3 Nowe Text Processor Providery
- [ ] **Advanced Text Processor** (`src/providers/text/advanced_processor.py`)
  - Semantic chunking
  - PDF, DOCX, HTML parsing
  - Testy: `tests/test_advanced_processor.py`

## 2. System Kolekcji i Baz Danych (Faza 2)

### 2.1 Mechanizm Kolekcji
- [ ] **Collection Manager** (`src/services/collection_service.py`)
  - Zarządzanie kolekcjami across providers
  - Metadata, versioning, backup
  - Testy: `tests/test_collection_service.py`

### 2.2 Inicjalizacja Baz Plikowych
- [ ] **Database Initializer** (`src/services/database_service.py`)
  - Auto-setup lokalnych baz (FAISS, Chroma, SQLite)
  - Migration system
  - Testy: `tests/test_database_service.py`

### 2.3 CLI Rozszerzenia
- [ ] Nowe komendy:
  - `create-collection <name> --provider <provider>`
  - `list-collections --provider <provider>`
  - `delete-collection <name> --provider <provider>`
  - `collection-info <name> --provider <provider>`
  - `import-data <file> --collection <name>`
  - `export-data <collection> --output <file>`

## 3. Testy API i Funkcjonalności (Faza 3)

### 3.1 Testy Połączenia API
- [ ] **API Health Checks** (`tests/test_api_connections.py`)
  - Test dostępności wszystkich API
  - Validacja kluczy API
  - Network connectivity tests

### 3.2 Integration Tests
- [ ] **End-to-End Tests** (`tests/integration/`)
  - Pełne workflow RAG
  - Multi-provider scenarios
  - Performance tests

### 3.3 Skrypty Testowe
- [ ] **test_all.sh** - Uruchomienie wszystkich testów
- [ ] **test_providers.sh** - Test wszystkich providerów
- [ ] **test_api_connectivity.sh** - Test połączeń API
- [ ] **test_performance.sh** - Testy wydajności
- [ ] **pre_commit_tests.sh** - Warunki przed commitem

## 4. Aktualizacja Konfiguracji (Faza 4)

### 4.1 Config Manager Enhancement
- [ ] Wsparcie dla nowych providerów w `config_manager.py`
- [ ] Walidacja konfiguracji per-provider
- [ ] Dynamic provider loading

### 4.2 Provider Factory Updates
- [ ] Rejestracja nowych providerów w Factory
- [ ] Auto-discovery mechanizm
- [ ] Provider health monitoring

## 5. Dokumentacja i Monitoring (Faza 5)

### 5.1 Dokumentacja
- [ ] **USAGE.md** - Przykłady użycia
- [ ] **PROVIDERS.md** - Dokumentacja providerów
- [ ] **API.md** - Dokumentacja API
- [ ] Aktualizacja README.md

### 5.2 Monitoring i Logging
- [ ] Provider-specific metrics
- [ ] Performance monitoring
- [ ] Error tracking enhancement

## 6. Aktualizacja config.instructions.md

### Nowe Wymagania
- [ ] Dodanie warunku przejścia testów przed commitem
- [ ] Definicja test coverage requirements
- [ ] API connectivity test requirements

## Harmonogram Realizacji

### Tydzień 1 (25.07 - 31.07)
- Implementacja Google i OpenRouter providerów
- Testy API connectivity
- Podstawowe skrypty testowe

### Tydzień 2 (01.08 - 07.08)
- Ollama i LM Studio providery
- System kolekcji
- Rozszerzenie CLI

### Tydzień 3 (08.08 - 14.08)
- Chroma provider
- Advanced text processor
- Integration tests

### Tydzień 4 (15.08 - 21.08)
- Dokumentacja
- Performance optimization
- Final testing

## Kryteria Sukcesu

### Techniczne
- [ ] Wszystkie testy przechodzą (100% success rate)
- [ ] Test coverage > 90%
- [ ] Wszystkie API connections działają
- [ ] Performance benchmarks spełnione

### Funkcjonalne
- [ ] Wszystkie providery z config.json działają
- [ ] CLI obsługuje wszystkie operacje
- [ ] System kolekcji jest funkcjonalny
- [ ] Monitoring i logging działa

### Jakościowe
- [ ] Kod spełnia standardy linting
- [ ] Dokumentacja jest kompletna
- [ ] Skrypty testowe są zautomatyzowane
- [ ] Git workflow z testami działa

## Uwagi Implementacyjne

1. **Zasada pojedynczej odpowiedzialności** - każdy provider w osobnym pliku
2. **Factory pattern** - centralna rejestracja providerów
3. **Async/await** - wszystkie API calls
4. **Error handling** - structured exceptions per provider type
5. **Logging** - structured JSON logs z provider context
6. **Testing** - unit tests + integration tests + API tests
7. **Configuration** - JSON-based, extensible, validated
