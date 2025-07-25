# System Logowania RAG_07

## 📋 Przegląd

System logowania RAG_07 używa structured logging (JSON) z rotacją plików i
elastyczną konfiguracją poziomów.

## 🔧 Konfiguracja

### Poziomy priorytetów (hierarchia konfiguracji):

1. **CLI argumenty** (najwyższy priorytet)
2. **Zmienne środowiskowe**
3. **Plik konfiguracyjny**
4. **Wartości domyślne** (najniższy priorytet)

### Opcje CLI

```bash
# Podstawowe opcje logowania
./run.sh --log-level DEBUG command
./run.sh --log-level WARNING --no-log-console command
./run.sh --log-dir /custom/logs command

# Dostępne poziomy logowania
--log-level DEBUG     # Wszystkie logi (bardzo szczegółowe)
--log-level INFO      # Informacje o operacjach (domyślny)
--log-level WARNING   # Tylko ostrzeżenia i błędy
--log-level ERROR     # Tylko błędy i krytyczne
--log-level CRITICAL  # Tylko krytyczne błędy

# Kontrola wyjścia
--log-console         # Logi na konsoli (domyślne)
--no-log-console      # Tylko do pliku, bez konsoli
```

### Zmienne środowiskowe

```bash
export LOG_LEVEL=WARNING
export LOG_DIR=/custom/logs
./run.sh command
```

### Plik konfiguracyjny

```json
{
  "log_level": "INFO"
  // other config...
}
```

## 📁 Rotacja plików

- **Lokalizacja**: `logs/rag_07.log`
- **Rotacja**: Codzienna o północy
- **Retencja**: 3 dni (usuwanie starszych plików)
- **Format nazw**: `rag_07.log.2025-07-25`
- **Encoding**: UTF-8

## 📊 Format logów

### JSON Structure:

```json
{
  "operation": "function_calling_completed",
  "class_name": "FunctionCallingService",
  "iterations": 3,
  "function_calls": 2,
  "event": "operation",
  "logger": "FunctionCallingService",
  "level": "info",
  "timestamp": "2025-07-25T17:41:12.709805Z"
}
```

## 🎯 Przykłady użycia

### Function Calling z logowaniem DEBUG

```bash
./run.sh --log-level DEBUG ask-with-tools "Question" --verbose
```

### Tylko logi do pliku (bez konsoli)

```bash
./run.sh --log-level WARNING --no-log-console ask-with-tools "Question"
```

### Własny katalog logów

```bash
./run.sh --log-dir /var/log/rag07 ask-with-tools "Question"
```

### Kombinacja z zmiennymi środowiskowymi

```bash
export LOG_LEVEL=INFO
./run.sh --log-dir /tmp/rag_logs ask-with-tools "Question"
```

## 🔍 Monitorowanie logów

### Podgląd na żywo

```bash
tail -f logs/rag_07.log | jq .
```

### Filtrowanie po poziomie

```bash
grep '"level":"error"' logs/rag_07.log | jq .
```

### Analiza operacji Function Calling

```bash
grep 'function_calling' logs/rag_07.log | jq .
```

### Statystyki logów

```bash
grep '"level":"info"' logs/rag_07.log | wc -l
grep '"level":"error"' logs/rag_07.log | wc -l
```

## 🚨 Rozwiązywanie problemów

### Problem: Logi nie pojawiają się w pliku

- Sprawdź uprawnienia do katalogu `logs/`
- Sprawdź czy poziom logowania nie jest za wysoki

### Problem: Za dużo logów

```bash
./run.sh --log-level ERROR command  # Tylko błędy
./run.sh --no-log-console command   # Bez konsoli
```

### Problem: Brakuje szczegółów

```bash
./run.sh --log-level DEBUG command --verbose
```

## 🔧 Integracja w kodzie

### Dla nowych klas

```python
from src.utils.logger import LoggerMixin

class MyService(LoggerMixin):
    async def my_operation(self):
        self.log_operation("my_operation_started", param1="value")
        try:
            # ... operations
            self.log_operation("my_operation_completed", result_count=5)
        except Exception as e:
            self.log_error(e, "my_operation")
```

### Konfiguracja w nowych modułach

```python
from src.utils.logger import configure_logging_from_env_and_config

# Rekonfiguracja z własnymi parametrami
configure_logging_from_env_and_config(
    config_manager=config_manager,
    log_level_override="DEBUG",
    console_output=False
)
```

---

**System logowania RAG_07 zapewnia pełną kontrolę nad verbosity, automatyczną
rotację i strukturalne JSON logi dla łatwej analizy.**
