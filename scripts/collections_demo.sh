#!/bin/bash
"""
Interaktywny przewodnik po kolekcjach wektorowych RAG_07
Demonstracja: tworzenie kolekcji, dodawanie dokumentów, odpytywanie
"""

set -e

echo "🎯 RAG_07 Collection Management Demo"
echo "===================================="
echo ""

# Kolory dla lepszej czytelności
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funkcja pauzy
pause() {
    echo ""
    echo -e "${YELLOW}Naciśnij Enter aby kontynuować...${NC}"
    read -r
    echo ""
}

# Funkcja nagłówka
header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

# Funkcja wykonania komendy z komentarzem
run_command() {
    echo -e "${GREEN}Wykonuję:${NC} $1"
    echo -e "${YELLOW}$2${NC}"
    echo ""
    eval "$1"
    echo ""
}

# Start demonstracji
echo "Ten skrypt pokaze Ci jak:"
echo "✅ Sprawdzić status systemu"
echo "✅ Tworzyć i zarządzać kolekcjami"
echo "✅ Dodawać dokumenty"
echo "✅ Wyszukiwać i odpytywać"
echo "✅ Używać Function Calling"
echo ""
pause

# 1. Status systemu
header "1. SPRAWDZENIE STATUSU SYSTEMU"

run_command "./run.sh config-status" \
"Sprawdzamy konfigurację i dostępnych providerów"
pause

run_command "./run.sh list-collections" \
"Lista istniejących kolekcji w bazie wektorowej"
pause

# 2. Tworzenie przykładowej kolekcji
header "2. TWORZENIE KOLEKCJI I DODAWANIE DOKUMENTÓW"

echo "Utworzę przykładową kolekcję 'demo' z dokumentami:"

run_command './run.sh embed --collection demo "
Dokument: RAG_07 Overview
Typ: Dokumentacja główna

RAG_07 to zaawansowana aplikacja CLI do pracy z systemami LLM.
Główne funkcjonalności:
- Multi-provider LLM support (OpenAI, Anthropic, Google)
- Vector databases (FAISS, Chroma, Pinecone)
- RAG (Retrieval-Augmented Generation)
- Function Calling dla zaawansowanych interakcji
- Strukturalne logowanie i monitoring
"' \
"Dodaję główną dokumentację do kolekcji 'demo'"
pause

run_command './run.sh embed --collection demo "
Dokument: CLI Commands Reference
Typ: Instrukcja użytkownika

Dostępne komendy CLI:
- query: Zapytania do LLM
- embed: Dodawanie tekstu do bazy wektorowej
- search: Wyszukiwanie w bazie wektorowej
- rag: Zapytania RAG z kontekstem
- ask-with-tools: Zaawansowane Function Calling
- list-providers: Lista dostępnych providerów
- list-models: Lista dostępnych modeli
- config-status: Status konfiguracji
- list-collections: Lista kolekcji
- collection-info: Informacje o kolekcji
"' \
"Dodaję dokumentację komend CLI"
pause

run_command './run.sh embed --collection demo "
Dokument: Configuration Guide
Typ: Przewodnik konfiguracji

Konfiguracja RAG_07:
1. Plik config/app_config.json - główna konfiguracja
2. Plik .env - klucze API dla providerów
3. Zmienne środowiskowe:
   - OPENAI_API_KEY
   - ANTHROPIC_API_KEY
   - GOOGLE_API_KEY
   - PINECONE_API_KEY

Domyślni providerzy:
- LLM: OpenAI (gpt-3.5-turbo)
- Vector DB: FAISS
- Text processor: Basic
"' \
"Dodaję przewodnik konfiguracji"
pause

# 3. Sprawdzanie kolekcji
header "3. SPRAWDZENIE UTWORZONEJ KOLEKCJI"

run_command "./run.sh list-collections" \
"Sprawdzamy czy kolekcja 'demo' została utworzona"
pause

run_command "./run.sh collection-info demo" \
"Szczegółowe informacje o kolekcji 'demo'"
pause

# 4. Proste wyszukiwanie
header "4. PODSTAWOWE WYSZUKIWANIE"

run_command "./run.sh search 'CLI commands' --collection demo --limit 3" \
"Wyszukuję dokumenty o komendach CLI"
pause

run_command "./run.sh search 'configuration' --collection demo --limit 2" \
"Wyszukuję dokumenty o konfiguracji"
pause

# 5. RAG queries
header "5. RAG - ZAPYTANIA Z KONTEKSTEM"

run_command "./run.sh rag 'What CLI commands are available?' --collection demo" \
"Zapytanie RAG o dostępne komendy"
pause

run_command "./run.sh rag 'How to configure RAG_07?' --collection demo" \
"Zapytanie RAG o konfigurację"
pause

# 6. Function Calling - najzaawansowane
header "6. FUNCTION CALLING - ZAAWANSOWANE ODPYTYWANIE"

echo -e "${GREEN}Function Calling to najzaawansowana funkcjonalność RAG_07.${NC}"
echo "LLM może wykonać wielokrotne wyszukiwania i budować kompleksowe odpowiedzi."
echo ""
pause

run_command "./run.sh ask-with-tools 'What are the main features of RAG_07?' --collection demo --verbose" \
"Demonstracja Function Calling z szczegółowymi logami"
pause

run_command "./run.sh ask-with-tools 'How do I get started with RAG_07?' --collection demo --verbose" \
"Pytanie o rozpoczęcie pracy z systemem"
pause

# 7. Zarządzanie wieloma kolekcjami
header "7. PRACA Z WIELOMA KOLEKCJAMI"

echo "Utworzę dodatkową kolekcję dla przykładów kodu:"

run_command './run.sh embed --collection code_examples "
Example: Basic Query
\`\`\`bash
./run.sh query \"Hello, how are you?\"
\`\`\`

Example: RAG Query with Context
\`\`\`bash
./run.sh rag \"Explain machine learning\" --collection knowledge --context-limit 5
\`\`\`

Example: Function Calling
\`\`\`bash
./run.sh ask-with-tools \"What is the best approach for...\" --verbose
\`\`\`
"' \
"Dodaję przykłady kodu do osobnej kolekcji"
pause

run_command "./run.sh list-collections" \
"Sprawdzamy wszystkie kolekcje"
pause

run_command "./run.sh ask-with-tools 'Show me code examples for RAG queries' --collection code_examples --verbose" \
"Wyszukuję przykłady kodu w dedykowanej kolekcji"
pause

# 8. Porównanie kolekcji
header "8. PORÓWNANIE RÓŻNYCH KOLEKCJI"

echo "Sprawdźmy jak różne kolekcje odpowiadają na to samo pytanie:"
echo ""

echo -e "${YELLOW}Pytanie do kolekcji 'demo':${NC}"
run_command "./run.sh ask-with-tools 'How to use RAG_07?' --collection demo" \
"Odpowiedź z dokumentacji głównej"

echo -e "${YELLOW}Pytanie do kolekcji 'code_examples':${NC}"
run_command "./run.sh ask-with-tools 'How to use RAG_07?' --collection code_examples" \
"Odpowiedź z przykładów kodu"

echo -e "${YELLOW}Pytanie do domyślnej kolekcji (pełna dokumentacja):${NC}"
run_command "./run.sh ask-with-tools 'How to use RAG_07?' --verbose" \
"Odpowiedź z pełnej dokumentacji projektu"
pause

# 9. Najlepsze praktyki
header "9. NAJLEPSZE PRAKTYKI"

echo -e "${GREEN}✅ Organizacja kolekcji:${NC}"
echo "  • Używaj opisowych nazw (docs_api, user_guides, faq)"
echo "  • Grupuj logicznie powiązane dokumenty"
echo "  • Oddzielaj różne typy treści"
echo ""

echo -e "${GREEN}✅ Dodawanie dokumentów:${NC}"
echo "  • Dodawaj kontekst i metadane"
echo "  • Używaj strukturalnych opisów"
echo "  • Regularnie aktualizuj treść"
echo ""

echo -e "${GREEN}✅ Odpytywanie:${NC}"
echo "  • Użyj Function Calling dla złożonych pytań"
echo "  • RAG dla prostych zapytań z kontekstem"
echo "  • search dla szybkiego wyszukiwania"
echo ""

echo -e "${GREEN}✅ Monitoring:${NC}"
echo "  • Regularnie sprawdzaj ./run.sh list-collections"
echo "  • Monitoruj logi z --verbose"
echo "  • Testuj różne typy zapytań"
echo ""
pause

# 10. Automatyzacja
header "10. AUTOMATYZACJA"

echo "RAG_07 oferuje gotowe skrypty automatyzacji:"
echo ""

echo -e "${GREEN}Dostępne skrypty:${NC}"
echo "  • ./scripts/index_documentation.sh - Automatyczne indeksowanie dokumentacji"
echo "  • ./scripts/index_documentation.py - Python script do zaawansowanego indeksowania"
echo ""

echo -e "${YELLOW}Przykład własnego skryptu automatyzacji:${NC}"
cat << 'EOF'
#!/bin/bash
# auto_populate.sh
echo "🤖 Automatyczne populowanie bazy wiedzy..."

# Dokumentacja
./run.sh embed --collection docs "$(cat README.md)"
./run.sh embed --collection docs "$(cat CHANGELOG.md)"

# FAQ
./run.sh embed --collection faq "$(cat support/faq.md)"

# Przykłady
find examples/ -name "*.md" -exec ./run.sh embed --collection examples "$(cat {})" \;

echo "✅ Gotowe!"
./run.sh list-collections
EOF
echo ""
pause

# Podsumowanie
header "🎉 PODSUMOWANIE DEMONSTRACJI"

echo -e "${GREEN}Co zostało zademonstrowane:${NC}"
echo "✅ Sprawdzanie statusu systemu"
echo "✅ Tworzenie kolekcji przez dodawanie dokumentów"
echo "✅ Dodawanie strukturalnych dokumentów z metadanymi"
echo "✅ Podstawowe wyszukiwanie w kolekcjach"
echo "✅ RAG queries z kontekstem"
echo "✅ Zaawansowane Function Calling"
echo "✅ Praca z wieloma kolekcjami"
echo "✅ Porównywanie odpowiedzi z różnych kolekcji"
echo "✅ Najlepsze praktyki"
echo "✅ Opcje automatyzacji"
echo ""

echo -e "${GREEN}Utworzone kolekcje:${NC}"
run_command "./run.sh list-collections" \
"Finalna lista wszystkich kolekcji"

echo -e "${GREEN}Następne kroki:${NC}"
echo "1. Przeczytaj pełną dokumentację: docs/collections_management.md"
echo "2. Przejrzyj szybki przewodnik: docs/quick_start_collections.md"
echo "3. Eksperymentuj z własnymi dokumentami"
echo "4. Utwórz skrypty automatyzacji dla swoich potrzeb"
echo "5. Użyj Function Calling do odpytywania: ./run.sh ask-with-tools 'Twoje pytanie' --verbose"
echo ""

echo -e "${BLUE}🚀 RAG_07 jest gotowy do użycia!${NC}"
echo ""

# Opcjonalne czyszczenie
echo -e "${YELLOW}Czy chcesz usunąć demo kolekcje? (y/N)${NC}"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "Usuwanie demonstracyjnych kolekcji..."
    rm -f databases/faiss_index/demo.*
    rm -f databases/faiss_index/code_examples.*
    echo "✅ Demonstracyjne kolekcje zostały usunięte"
else
    echo "Kolekcje demonstracyjne zostały zachowane"
fi

echo ""
echo "🎯 Dziękuję za uwagę! Miłego korzystania z RAG_07!"
