# Szybki przewodnik: Kolekcje wektorowe w RAG_07

## 🚀 Quick Start - 5 minut do działającego systemu

### 1. Sprawdź status systemu

```bash
./run.sh config-status
./run.sh list-collections
```

### 2. Utwórz pierwszą kolekcję z dokumentacją

```bash
# Automatyczne indeksowanie dokumentacji projektu
./scripts/index_documentation.sh

# Lub ręcznie:
./run.sh embed --collection default "$(cat README.md)"
```

### 3. Przetestuj wyszukiwanie

```bash
# Proste wyszukiwanie
./run.sh search "main features" --collection default --limit 5

# Inteligentne odpytywanie z Function Calling
./run.sh ask-with-tools "What are the main features of RAG_07?" --verbose
```

## 📚 Podstawowe komendy

### Zarządzanie kolekcjami

```bash
# Lista kolekcji
./run.sh list-collections

# Informacje o kolekcji
./run.sh collection-info nazwa_kolekcji

# Status konfiguracji
./run.sh config-status
```

### Dodawanie dokumentów

```bash
# Dodaj tekst
./run.sh embed --collection docs "Twój dokument tutaj"

# Dodaj plik
./run.sh embed --collection docs "$(cat plik.md)"

# Określ provider
./run.sh embed --provider faiss --collection docs "Tekst"
```

### Wyszukiwanie i odpytywanie

```bash
# Proste wyszukiwanie
./run.sh search "szukany tekst" --collection docs --limit 10

# RAG z kontekstem
./run.sh rag "Pytanie z kontekstem?" --collection docs

# Function Calling (najlepsze)
./run.sh ask-with-tools "Złożone pytanie?" --verbose
```

## 🎯 Najczęstsze przypadki użycia

### Przypadek 1: Dokumentacja produktu

```bash
# Utwórz kolekcję dla dokumentacji
./run.sh embed --collection product_docs "$(cat docs/overview.md)"
./run.sh embed --collection product_docs "$(cat docs/api.md)"
./run.sh embed --collection product_docs "$(cat docs/examples.md)"

# Odpytaj
./run.sh ask-with-tools "How to use the API?" --collection product_docs --verbose
```

### Przypadek 2: Baza wiedzy FAQ

```bash
# Dodaj FAQ
./run.sh embed --collection faq "
Q: How to install the application?
A: Run ./setup.sh to install all dependencies and setup the environment.

Q: What are the system requirements?
A: Python 3.8+, 4GB RAM, and API keys for LLM providers.
"

# Odpytaj FAQ
./run.sh ask-with-tools "How to install?" --collection faq
```

### Przypadek 3: Przykłady kodu

```bash
# Dodaj przykłady
./run.sh embed --collection code_examples "
Example: Basic query
\`\`\`bash
./run.sh query 'Hello world'
\`\`\`

Example: RAG query
\`\`\`bash
./run.sh rag 'Explain this concept' --collection docs
\`\`\`
"

# Szukaj przykładów
./run.sh ask-with-tools "Show me how to make a query" --collection code_examples --verbose
```

## ⚡ Skrypty automatyzacji

### Tworzenie skryptu populacji

Utwórz `scripts/populate_kb.sh`:

```bash
#!/bin/bash
echo "📚 Populowanie bazy wiedzy..."

# Dokumentacja
./run.sh embed --collection docs "$(cat README.md)"
./run.sh embed --collection docs "$(cat CHANGELOG.md)"

# FAQ
./run.sh embed --collection faq "$(cat support/faq.md)"

# Przykłady
find examples/ -name "*.md" -exec ./run.sh embed --collection examples "$(cat {})" \;

echo "✅ Gotowe!"
./run.sh list-collections
```

### Skrypt aktualizacji

Utwórz `scripts/update_kb.sh`:

```bash
#!/bin/bash
echo "🔄 Aktualizacja bazy wiedzy..."

# Sprawdź zmiany w git
if git diff --quiet HEAD~1 docs/; then
    echo "Brak zmian w dokumentacji"
    exit 0
fi

# Aktualizuj zmienione pliki
git diff --name-only HEAD~1 docs/ | while read file; do
    if [[ -f "$file" ]]; then
        echo "Aktualizuję: $file"
        ./run.sh embed --collection docs "$(cat "$file")"
    fi
done

echo "✅ Aktualizacja zakończona"
```

## 🔍 Debugowanie

### Problem: "Collection does not exist"

```bash
# Sprawdź dostępne kolekcje
./run.sh list-collections

# Utwórz kolekcję
./run.sh embed --collection nowa_kolekcja "Pierwszy dokument"
```

### Problem: Brak wyników wyszukiwania

```bash
# Sprawdź zawartość kolekcji
./run.sh collection-info nazwa_kolekcji

# Test z prostym zapytaniem
./run.sh search "test" --collection nazwa_kolekcji --limit 1
```

### Problem: Błędy API

```bash
# Sprawdź konfigurację
./run.sh config-status

# Sprawdź klucze w .env
grep API_KEY .env
```

## 📊 Monitoring

### Sprawdzenie rozmiaru baz

```bash
du -sh databases/
ls -la databases/faiss_index/
```

### Sprawdzenie logów

```bash
tail -f logs/application.log
grep "error" logs/application.log
```

### Test wydajności

```bash
time ./run.sh ask-with-tools "Test query" --verbose
```

## 🎉 Przykład kompletnego workflow

```bash
# 1. Setup
./setup.sh
source .venv/bin/activate

# 2. Sprawdź status
./run.sh config-status

# 3. Indeksuj dokumentację
./scripts/index_documentation.sh

# 4. Sprawdź rezultat
./run.sh list-collections
./run.sh collection-info default

# 5. Test
./run.sh ask-with-tools "What is RAG_07?" --verbose

# 6. Dodaj własną treść
./run.sh embed --collection my_docs "Moja własna dokumentacja"

# 7. Test własnej treści
./run.sh ask-with-tools "Tell me about my documentation" --collection my_docs --verbose
```

## 🔗 Przydatne linki

- **Pełna dokumentacja:**
  [docs/collections_management.md](collections_management.md)
- **Konfiguracja:** [config/app_config.json](../config/app_config.json)
- **Skrypty:** [scripts/](../scripts/)
- **Logi:** [logs/](../logs/)

---

**💡 Wskazówka:** Użyj `./run.sh ask-with-tools "How to..." --verbose` aby
uzyskać interaktywną pomoc!
