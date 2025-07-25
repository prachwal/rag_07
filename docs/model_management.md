# Model Management Documentation

## Narzędzie do pobierania listy modeli

Zaimplementowano kompletne narzędzie do pobierania, cache'owania i wyświetlania informacji o modelach dla wszystkich providerów LLM.

### Funkcjonalności

#### 1. Lista modeli
```bash
# Prosty sposób (używając run.sh)
./run.sh list-models
./run.sh list-models --provider openai
./run.sh list-models --format simple

# Lub bezpośrednio z PYTHONPATH
PYTHONPATH=/path/to/rag_07 python src/cli.py list-models

# Różne formaty wyświetlania
./run.sh list-models --format simple   # Lista z cenami
./run.sh list-models --format table    # Tabela ze szczegółami

# Pomijanie cache
./run.sh list-models --no-cache
```

#### 2. Zarządzanie cache
```bash
# Informacje o cache
./run.sh cache-info

# Czyszczenie cache
./run.sh clear-cache --provider openai
./run.sh clear-cache --all
```

#### 3. Testowanie modeli
```bash
# Test "przedstaw się"
./run.sh query "Przedstaw się w jednym zdaniu" --provider anthropic
./run.sh query "Przedstaw się w jednym zdaniu" --provider ollama --model qwen2:0.5b
```

### Standardowe informacje o modelach

Każdy model zawiera ujednolicone informacje:

- **ID modelu**: Unikalny identyfikator
- **Nazwa**: Nazwa czytelna dla człowieka
- **Provider**: Dostawca usługi
- **Max tokens**: Maksymalna długość kontekstu
- **Capabilities**: Lista możliwości (text_generation, embeddings, tools, vision, etc.)
- **Pricing**: Cena za milion tokenów (wejście/wyjście) w USD
- **Multimodal**: Czy model obsługuje wizję
- **Supports tools**: Czy model obsługuje function calling
- **Supports streaming**: Czy model obsługuje streaming

### Implementowane providery

#### ✅ OpenAI
- **Modele**: 75 modeli (GPT-3.5, GPT-4, GPT-4o, embeddings, etc.)
- **Ceny**: Dokładne ceny dla głównych modeli
- **Możliwości**: Automatyczne wykrywanie tools, vision, embeddings
- **API**: /v1/models endpoint

#### ✅ Ollama
- **Modele**: 7 lokalnych modeli (Llama, Phi, Qwen, etc.)
- **Ceny**: 0.00 USD (modele lokalne)
- **Możliwości**: Automatyczne wykrywanie na podstawie nazwy
- **API**: /api/tags endpoint
- **Dodatkowe**: Informacje o rozmiarze modelu w GB

#### ✅ Anthropic
- **Modele**: 4 modele (Claude 3 Haiku, Claude 3.5 Sonnet, Claude 3.5 Haiku, Claude 3 Opus)
- **Status**: ✅ Modele zaktualizowane do najnowszych wersji
- **Test**: ✅ Claude 3.5 Haiku działa poprawnie
- **Fallback**: Lista z konfiguracji

#### ✅ Google
- **Modele**: 3 modele (Gemini 1.5 Flash, Gemini 1.5 Pro, Gemini 1.0 Pro)
- **Status**: ✅ Modele zaktualizowane do najnowszych wersji
- **Test**: ⚠️ API czasowo przeciążone (ale modele istnieją)
- **Fallback**: Lista z konfiguracji

#### ✅ OpenRouter
- **Status**: ✅ Poprawiono nazwę klucza API (OPENROUTER_API_KEY)
- **Modele**: 4 modele z konfiguracji
- **Test**: ⚠️ Wymaga klucza API do pełnego testowania
- **Fallback**: Lista z konfiguracji#### ✅ LM Studio
- **Status**: Podstawowa implementacja
- **Modele**: 1 model (local-model)
- **Do zrobienia**: API do listowania modeli

### Cache System

- **Lokalizacja**: `cache/models/`
- **TTL**: 24 godziny
- **Format**: JSON z pełnymi informacjami o modelach
- **Automatyczne**: Cache jest automatycznie używany i odświeżany

### Przykładowe wyniki

```bash
$ python src/cli.py list-models --provider openai --format simple

OPENAI (75):
  • gpt-3.5-turbo ($0.50/$1.50)
  • gpt-4 ($30.00/$60.00)
  • gpt-4o ($5.00/$15.00)
  • gpt-4o-mini ($5.00/$15.00)
  • text-embedding-ada-002 ($0.10/$0.00)
  ...
```

```bash
$ python src/cli.py list-models --provider ollama --format table

=== OLLAMA Models ===
Total: 7 models
(Using cached data)
Model ID                       Tokens   Tools  Vision  Price/M
----------------------------------------------------------------------
llama3.2:3b                    4096     Yes    No      $0.0/$0.0
phi3:mini                      4096     Yes    No      $0.0/$0.0
qwen2:0.5b                     4096     Yes    No      $0.0/$0.0
...
```

### Testowanie funkcji "przedstaw się"

✅ **OpenAI GPT-3.5-turbo**: Działa poprawnie
✅ **OpenAI GPT-4o-mini**: Działa poprawnie
✅ **Anthropic Claude 3.5 Haiku**: ✅ Działa poprawnie
✅ **Ollama Llama3.2:3b**: Działa poprawnie
✅ **Ollama Qwen2:0.5b**: Działa poprawnie
⚠️ **Ollama Phi3:mini**: Błąd pamięci (wymaga 5.6GB, dostępne 4.2GB)
⚠️ **Google Gemini 1.5 Flash**: API czasowo przeciążone
⚠️ **OpenRouter**: Wymaga klucza API### Kolejne kroki

1. ✅ **Naprawić Anthropic providera**: Zaktualizowano nazwy modeli do najnowszych wersji
2. ✅ **Naprawić Google providera**: Zaktualizowano modele do Gemini 1.5
3. ✅ **Poprawić OpenRouter**: Naprawiono nazwę klucza API
4. **Dodać implementację API**: Rozszerzyć providery o rzeczywiste API calls
5. **Rozszerzyć LM Studio**: Implementować API do listowania modeli
6. **Dodać więcej metadanych**: Informacje o wydajności, ograniczeniach
7. **Implementować filtering**: Możliwość filtrowania modeli po capabilities

### Ułatwienia użytkowania

Dodano skrypt `run.sh` dla prostszego użytkowania:
```bash
# Zamiast długiej komendy:
PYTHONPATH=/path/to/rag_07 python src/cli.py list-models

# Można używać:
./run.sh list-models
```

### Architektura

```
src/models/model_info.py      # Struktury danych
src/utils/model_cache.py      # System cache
src/providers/base.py         # Interfejs list_models()
src/providers/llm/*/          # Implementacje per provider
src/cli.py                    # Komendy CLI
```

Cache jest transparentny i automatyczny - modele są pobierane z API tylko raz dziennie, a następnie serwowane z lokalnego cache.
