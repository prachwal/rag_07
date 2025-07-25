# Dokumentacja zarządzania kolekcjami wektorowymi w RAG_07

## Spis treści

1. [Przegląd systemu](#przegląd-systemu)
2. [Tworzenie kolekcji](#tworzenie-kolekcji)
3. [Dodawanie dokumentów](#dodawanie-dokumentów)
4. [Odpytywanie kolekcji](#odpytywanie-kolekcji)
5. [Zarządzanie kolekcjami](#zarządzanie-kolekcjami)
6. [Automatyzacja](#automatyzacja)
7. [Najlepsze praktyki](#najlepsze-praktyki)
8. [Rozwiązywanie problemów](#rozwiązywanie-problemów)

## Przegląd systemu

RAG_07 obsługuje wiele providerów baz wektorowych:

- **FAISS** (lokalny, wydajny)
- **Chroma** (lokalny, łatwy w użyciu)
- **Pinecone** (chmurowy)

### Architektura

```
📦 RAG_07
├── 🗄️ Vector Databases
│   ├── FAISS (databases/faiss_index/)
│   ├── Chroma (databases/chroma_db/)
│   └── Pinecone (chmura)
├── 🤖 LLM Providers
│   ├── OpenAI, Anthropic, Google
│   └── Ollama, OpenRouter, LMStudio
└── 🔧 Function Calling
    ├── VectorSearchTools
    └── FunctionExecutor
```

## Tworzenie kolekcji

### Automatyczne tworzenie

Kolekcje są tworzone automatycznie przy pierwszym dodawaniu dokumentu:

```bash
# Tworzy kolekcję "default" (jeśli nie istnieje) i dodaje dokument
./run.sh embed --collection default "Twój pierwszy dokument"

# Tworzy kolekcję "projekty" z dokumentem
./run.sh embed --collection projekty "Dokumentacja projektu X"
```

### Ręczne sprawdzenie kolekcji

```bash
# Lista wszystkich kolekcji
./run.sh list-collections

# Informacje o konkretnej kolekcji
./run.sh collection-info nazwa_kolekcji

# Status konfiguracji
./run.sh config-status
```

### Przykład wyjścia

```
Collections in faiss:
  • default (48 vectors)
  • knowledge (4 vectors)
  • snippets (10 vectors)
  • documents (2 vectors)
```

## Dodawanie dokumentów

### 1. Podstawowe dodawanie tekstu

```bash
# Dodanie prostego tekstu do kolekcji default
./run.sh embed --collection default "To jest przykładowy tekst dokumentu"

# Dodanie do konkretnej kolekcji
./run.sh embed --collection technical_docs "Dokumentacja techniczna API"

# Określenie providera bazy wektorowej
./run.sh embed --provider faiss --collection docs "Tekst dla FAISS"
./run.sh embed --provider chroma --collection docs "Tekst dla Chroma"
```

### 2. Dodawanie plików

```bash
# Dodanie całego pliku
./run.sh embed --collection docs "$(cat README.md)"

# Dodanie wielu plików
./run.sh embed --collection docs "$(cat docs/api.md)"
./run.sh embed --collection docs "$(cat docs/user_guide.md)"
```

### 3. Dodawanie strukturalnych dokumentów

```bash
# Dokumentacja z metadanymi
./run.sh embed --collection docs "
Dokument: Instrukcja obsługi API
Typ: Dokumentacja techniczna
Wersja: 1.0

Zawartość:
API RAG_07 pozwala na...
"

# Kod z opisem
./run.sh embed --collection code_examples "
Przykład kodu: Tworzenie klienta API

\`\`\`python
from rag_07 import Client
client = Client(api_key='your_key')
\`\`\`

Ten kod pokazuje jak...
"
```

### 4. Automatyczne przetwarzanie

System automatycznie:

- **Czyści tekst** (usuwa nadmiarowe białe znaki)
- **Dzieli na chunki** (domyślnie 1000 znaków z 200 znaków overlap)
- **Generuje embeddingi** (używając modelu text-embedding-ada-002)
- **Zapisuje do bazy wektorowej**

```bash
# Przykład logu przetwarzania
{"operation": "cleaned_text", "original_length": 7675, "cleaned_length": 6541}
{"operation": "chunked_text", "chunks_count": 9, "chunk_size": 1000, "overlap": 200}
{"operation": "generated_embedding", "text_length": 938, "embedding_dimension": 1536}
{"operation": "added_vectors", "collection": "default", "count": 9, "total_vectors": 48}
```

## Odpytywanie kolekcji

### 1. Podstawowe wyszukiwanie

```bash
# Wyszukiwanie w domyślnej kolekcji
./run.sh search "machine learning" --limit 5

# Wyszukiwanie w konkretnej kolekcji
./run.sh search "API documentation" --collection docs --limit 10

# Określenie providera
./run.sh search "Python examples" --provider faiss --collection code
```

### 2. RAG (Retrieval-Augmented Generation)

```bash
# Podstawowe zapytanie RAG
./run.sh rag "How to use the API?"

# Szczegółowe parametry
./run.sh rag "Explain machine learning concepts" \
  --provider openai \
  --vector-provider faiss \
  --collection docs \
  --context-limit 5
```

### 3. Zaawansowane Function Calling

```bash
# Podstawowe function calling
./run.sh ask-with-tools "What are the main features of RAG_07?"

# Z szczegółowym logowaniem
./run.sh ask-with-tools "How to configure multiple LLM providers?" --verbose

# Dostosowane parametry
./run.sh ask-with-tools "Explain the architecture" \
  --provider anthropic \
  --vector-provider faiss \
  --collection docs \
  --max-iterations 10 \
  --verbose
```

### 4. Przykład Function Calling z logami

```bash
./run.sh ask-with-tools "What CLI commands are available?" --verbose
```

**Wyjście:**

```
🤖 Processing question with function calling...
📋 Question: What CLI commands are available?
🔧 Max iterations: 5
⚙️  LLM Provider: default
🗄️  Vector Provider: default
==================================================

🤖 Answer:
RAG_07 provides the following CLI commands:

1. **query** - Send queries directly to LLM providers
2. **embed** - Add text to vector databases
3. **search** - Search in vector databases
4. **rag** - Ask questions using RAG with context
5. **ask-with-tools** - Advanced function calling approach
6. **list-providers** - Show available LLM and vector providers
7. **list-models** - Show available models for providers
8. **config-status** - Display configuration status
9. **list-collections** - List all vector database collections
10. **collection-info** - Get detailed information about collections

🔧 Function calls made (1):
  1. search_documents(query=CLI commands available)

📚 Sources used:
  - Search: CLI commands available

📊 Statistics:
  - Iterations used: 2
  - Function calls: 1
```

## Zarządzanie kolekcjami

### Sprawdzanie stanu

```bash
# Lista wszystkich kolekcji
./run.sh list-collections

# Szczegóły kolekcji
./run.sh collection-info default
./run.sh collection-info technical_docs

# Status całego systemu
./run.sh config-status
```

### Przykład wyjścia

```bash
Collection: default
Provider: faiss
Vector count: 48
Dimension: 1536
```

### Usuwanie (przez skrypty)

```bash
# Usunięcie lokalnych baz (ostrożnie!)
rm -rf databases/faiss_index/default.*
rm -rf databases/chroma_db/default/
```

## Automatyzacja

### 1. Skrypt indeksowania dokumentacji

```bash
# Uruchomienie gotowego skryptu
./scripts/index_documentation.sh

# Lub Python script
python scripts/index_documentation.py
```

### 2. Tworzenie własnych skryptów

**Przykład skryptu bash:**

```bash
#!/bin/bash
# populate_knowledge.sh

echo "📚 Dodawanie bazy wiedzy..."

# Dokumentacja produktu
./run.sh embed --collection product_docs "$(cat docs/product_overview.md)"
./run.sh embed --collection product_docs "$(cat docs/features.md)"

# Instrukcje użytkownika
./run.sh embed --collection user_guides "$(cat guides/getting_started.md)"
./run.sh embed --collection user_guides "$(cat guides/advanced_usage.md)"

# FAQ
./run.sh embed --collection faq "$(cat support/faq.md)"

echo "✅ Baza wiedzy zaktualizowana"
./run.sh list-collections
```

**Przykład skryptu Python:**

```python
#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

# Setup path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from config.config_manager import ConfigManager
from services.application_service import ApplicationService

async def populate_database():
    config_manager = ConfigManager()
    app_service = ApplicationService(config_manager)

    documents = [
        ("product_docs", "docs/api_reference.md"),
        ("user_guides", "guides/quickstart.md"),
        ("examples", "examples/code_samples.md"),
    ]

    for collection, file_path in documents:
        if Path(file_path).exists():
            content = Path(file_path).read_text()
            result = await app_service.add_to_vector_store(
                text=content,
                collection=collection
            )
            print(f"✅ Added {file_path} to {collection}: {result}")

if __name__ == "__main__":
    asyncio.run(populate_database())
```

### 3. Automatyzacja CI/CD

**Przykład GitHub Actions:**

```yaml
# .github/workflows/update_knowledge_base.yml
name: Update Knowledge Base

on:
  push:
    paths:
      - 'docs/**'
      - 'guides/**'

jobs:
  update-kb:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          python -m pip install -r requirements.txt

      - name: Update knowledge base
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          ./scripts/index_documentation.sh
```

## Najlepsze praktyki

### 1. Organizacja kolekcji

```bash
# Logiczne grupowanie
- docs_api        # Dokumentacja API
- docs_user       # Instrukcje użytkownika
- examples_code   # Przykłady kodu
- faq_support     # FAQ i wsparcie
- knowledge_base  # Ogólna baza wiedzy
```

### 2. Nazewnictwo

```bash
# Dobre nazwy
./run.sh embed --collection api_v2_docs "..."
./run.sh embed --collection user_guides_2024 "..."

# Unikaj
./run.sh embed --collection temp "..."
./run.sh embed --collection test123 "..."
```

### 3. Struktura dokumentów

```bash
# Dodawaj kontekst
./run.sh embed --collection docs "
Dokument: User Guide - Getting Started
Sekcja: Account Setup
Ostatnia aktualizacja: 2024-01-15

Zawartość dokumentu:
To create an account...
"
```

### 4. Monitoring

```bash
# Regularne sprawdzanie
./run.sh list-collections
./run.sh collection-info important_docs

# Test działania
./run.sh ask-with-tools "Test query" --verbose
```

## Rozwiązywanie problemów

### Problem 1: Kolekcja nie istnieje

```
Error: Collection default does not exist
```

**Rozwiązanie:**

```bash
# Sprawdź dostępne kolekcje
./run.sh list-collections

# Utwórz kolekcję dodając dokument
./run.sh embed --collection default "Pierwszy dokument"

# Lub użyj istniejącej kolekcji
./run.sh ask-with-tools "query" --collection existing_collection
```

### Problem 2: Brak wyników wyszukiwania

```bash
# Sprawdź zawartość kolekcji
./run.sh collection-info nazwa_kolekcji

# Test prostego wyszukiwania
./run.sh search "test" --collection nazwa_kolekcji --limit 10

# Sprawdź czy embeddingi są generowane
./run.sh embed --collection test "test document" --verbose
```

### Problem 3: Błędy API

```
Error: OpenAI API error
```

**Rozwiązanie:**

```bash
# Sprawdź konfigurację
./run.sh config-status

# Sprawdź klucze API w .env
cat .env | grep API_KEY

# Test prostego zapytania
./run.sh query "test" --provider openai
```

### Problem 4: Brak miejsca/wydajność

```bash
# Sprawdź rozmiar baz
du -sh databases/

# Wyczyść cache
./run.sh clear-cache --all

# Opcjonalnie usuń stare kolekcje
rm -rf databases/faiss_index/old_collection.*
```

## Przykłady kompletnych workflow

### 1. Setup nowego projektu

```bash
# 1. Sprawdź status
./run.sh config-status

# 2. Dodaj dokumentację
./run.sh embed --collection project_docs "$(cat README.md)"
./run.sh embed --collection project_docs "$(cat docs/architecture.md)"

# 3. Sprawdź wynik
./run.sh list-collections
./run.sh collection-info project_docs

# 4. Test
./run.sh ask-with-tools "What is this project about?" --verbose
```

### 2. Aktualizacja dokumentacji

```bash
# 1. Backup (opcjonalnie)
cp -r databases/faiss_index databases/faiss_index.backup

# 2. Dodaj nowe dokumenty
./run.sh embed --collection docs "$(cat new_feature.md)"

# 3. Sprawdź aktualizację
./run.sh collection-info docs

# 4. Test nowych informacji
./run.sh ask-with-tools "Tell me about new features" --verbose
```

### 3. Migracja między providerami

```bash
# 1. Export z FAISS (przez zapytania)
./run.sh search "all content" --provider faiss --limit 1000 > export.txt

# 2. Import do Chroma
./run.sh embed --provider chroma --collection migrated "$(cat export.txt)"

# 3. Porównanie
./run.sh collection-info migrated --provider faiss
./run.sh collection-info migrated --provider chroma
```

## Monitoring i metryki

### Logi strukturalne

System generuje szczegółowe logi JSON:

```json
{"operation": "added_vectors", "collection": "docs", "count": 5, "total_vectors": 50}
{"operation": "search_documents_completed", "results_found": 3, "collection": "docs"}
{"operation": "function_calling_completed", "iterations": 2, "function_calls": 1}
```

### Metryki do śledzenia

- Liczba kolekcji
- Liczba wektorów na kolekcję
- Czas odpowiedzi zapytań
- Skuteczność Function Calling
- Użycie API (koszty)

---

**📝 Dokumentacja została utworzona:** `docs/collections_management.md`

**🔧 Dostępne komendy:**

- `./run.sh --help` - Pełna lista komend
- `./run.sh ask-with-tools "How to use collections?" --verbose` - Interaktywna
  pomoc
- `./scripts/index_documentation.sh` - Automatyczne indeksowanie
