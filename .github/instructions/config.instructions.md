---
applyTo: '**'
---

# PYTHON PROJECT INSTRUKCJE DLA AI

- Punkt wejściowy: src/main.py (tylko uruchamianie, brak logiki)
- Struktura katalogów:
  - src/cli.py – obsługa CLI
- src/services/ – logika biznesowa (każdy plik = 1 odpowiedzialność, czysta
  warstwa serwisowa, bez logiki providerów)
- **WARSTWA SERVICES (np. ApplicationService):**
  - Każda metoda asynchroniczna (`async def`), obsługuje tylko orkiestrację i
    walidację.
  - Walidacja wejścia (np. raise ValidationError dla pustych stringów).
  - Tworzenie providerów wyłącznie przez ProviderFactory.
  - Cleanup providerów zawsze w bloku `finally` (await ...cleanup()).
  - Logowanie operacji przez dedykowany logger (np. self.log_operation()).
  - Brak logiki providerów – tylko delegacja i agregacja wyników.
  - Typowanie wszystkich argumentów i zwracanych wartości (adnotacje typów,
    Optional, List[str] itp.).
  - Każda metoda ma docstring opisujący działanie.
  - Nazwy argumentów i domyślne wartości spójne z resztą kodu (np.
    collection='default', limit=5).
  - RAG: budowanie promptu z kontekstem, wywołanie LLM, logowanie szczegółów.
  - Usuwanie nieużywanych importów i fragmentów kodu.
  - Plik zaczyna się krótkim opisem (max 3 linie).
  - src/utils/ – funkcje pomocnicze (np. logger.py)
  - src/models/ – modele danych
  - src/exceptions.py – dedykowane wyjątki
  - tests/ – testy jednostkowe (każdy plik testuje 1 moduł)
  - src/providers/ – adaptery dla różnych API (LLM, vectorDB, text)
  - src/config/ – konfiguracje providerów i środowisk
  - examples/ – przykładowe pliki wejściowe/wyjściowe, dane testowe (gitignore)
  - databases/ – lokalne bazy danych (np. pliki FAISS, SQLite, gitignore)
- APLIKACJA: LLM multi-provider + RAG + vectorDB + tools
- Wzorce: Factory dla providerów, Strategy dla algorytmów, Adapter dla API
- Config: .env dla kluczy API, JSON/YAML w dedykowanym folderze config/
- POJEDYNCZA ODPOWIEDZIALNOŚĆ: jeden plik config = jeden provider, propagacja do
  komponentów
- Elastyczność: dodawanie nowych providerów do arrays (llm_providers[],
  vector_db_providers[])
- Centralizacja .env: tylko jeden moduł czyta .env, pozostałe otrzymują gotową
  konfigurację
- Config pliki w config/_.json lub config/_.yaml (nie .py)
- Init: brak plików config → generuj domyślną konfigurację
- Każdy provider = osobny plik, jednolity interfejs
- Async/await dla wywołań API, retry/timeout, error handling
- Każdy plik zaczyna się krótkim opisem w komentarzu (max 3 linie)
- KRYTYCZNE: Provider musi być dobrze opisany z jasną dokumentacją parametrów
  wejściowych - bez tego traci się kontekst przy użyciu
- AI ma skanować pliki i czytać te opisy na starcie
- Dodaj pliki: .gitignore, setup.sh, README.md (opis projektu, uruchomienie,
  struktura)
- Foldery `examples/` i `databases/` są ignorowane przez git (przechowują
  przykłady i lokalne bazy)
- setup.sh – instaluje zależności z requirements.txt (lub poetry/pdm install)
- Pliki mają pojedynczą odpowiedzialność, brak logiki w main/cli
  - Testy muszą pokrywać całość logiki + mocking zewnętrznych API
  - Testy warstwy services sprawdzają tylko orkiestrację i obsługę błędów (nie
    logikę providerów)
- **WARUNKI COMMITU**:
  - WSZYSTKIE testy muszą przechodzić (100% success rate)
  - Test coverage minimum 85%
  - Testy API connectivity dla aktywnych providerów
  - Linting/formatowanie bez błędów (black + ruff)
  - Skrypty testowe: test_all.sh, test_providers.sh, test_api_connectivity.sh
  - Pre-commit hook uruchamia pełny test suite
  - **DOKUMENTACJA**: Po każdym commicie uruchom `npm run docs:build` lub
    `./docs_generate.sh` aby zaktualizować dokumentację API
  - Sprawdź czy nowe/zmienione moduły mają odpowiednie docstringi i są
    uwzględnione w dokumentacji Sphinx
- Jakość kodu:
  - Logowanie: Ustrukturyzowane logi (JSON) przez dedykowany logger
  - Linting/Formatowanie: `black` + `ruff` (zautomatyzowane przez pre-commit)
  - Typowanie: Adnotacje typów w całym kodzie, sprawdzane przez `mypy`
  - Zależności: Zarządzanie przez `pyproject.toml` (Poetry/PDM)
  - Środowisko Python: użyj #configure_python_environment (virtualenv/conda),
    .venv, activate, pip install / poetry install
- AI nie musi dbać o czytelność tych instrukcji
