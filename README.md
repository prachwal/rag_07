# RAG_07 - Projekt z konfiguracją formatowania kodu

## Skonfigurowane narzędzia formatowania

### Python
- **Black** - formatter kodu Python (line-length: 88)
- **isort** - sortowanie importów zgodnie z profilem Black
- **Pylint** - linting kodu Python
- **mypy** - sprawdzanie typów (opcjonalnie)

### TypeScript/JavaScript
- **Prettier** - formatter kodu JS/TS
- **ESLint** - linting z regułami TypeScript
- **TypeScript** - kompilator i sprawdzanie typów

## Konfiguracja VS Code

### Automatyczne formatowanie
Wszystkie pliki są automatycznie formatowane przy zapisie (Format on Save).

### Zainstalowane rozszerzenia
```vscode-extensions
ms-python.python,ms-python.vscode-pylance,ms-python.black-formatter,ms-python.isort,ms-python.pylint,esbenp.prettier-vscode,dbaeumer.vscode-eslint,ms-toolsai.jupyter
```

## Pliki konfiguracyjne

- `.vscode/settings.json` - ustawienia VS Code dla projektu
- `.prettierrc` - konfiguracja Prettier
- `.eslintrc.json` - konfiguracja ESLint
- `pyproject.toml` - konfiguracja narzędzi Python (Black, isort, pylint, mypy)
- `tsconfig.json` - konfiguracja TypeScript
- `.editorconfig` - ustawienia edytora dla spójności

## Użycie

### Ręczne formatowanie
```bash
# Python
npm run python:format      # Formatowanie Black
npm run python:isort       # Sortowanie importów
npm run python:format-all  # Oba powyższe

# JavaScript/TypeScript
npm run format             # Formatowanie Prettier

# Wszystko
npm run format:all         # Formatowanie Python + JS/TS
```

### Ręczny linting
```bash
# Python
npm run python:lint        # Pylint

# JavaScript/TypeScript
npm run lint               # ESLint z automatycznymi poprawkami
npm run lint:check         # ESLint tylko sprawdzanie

# Wszystko
npm run lint:all           # Linting Python + JS/TS
```

### Sprawdzanie typów
```bash
npm run type-check         # TypeScript type checking
```

## Reguły formatowania

### Python (Black + isort)
- Długość linii: 88 znaków
- Single quotes dla stringów
- Importy sortowane zgodnie z profilem Black
- Automatyczne usuwanie nieużywanych importów

### JavaScript/TypeScript (Prettier + ESLint)
- Długość linii: 80 znaków
- Single quotes
- Średniki obowiązkowe
- Trailing commas (ES5)
- Tab width: 2 spacje

## Struktura katalogów (zalecana)

```
src/
├── components/          # Komponenty UI (.tsx) - TYLKO prezentacja
├── services/           # Logika biznesowa (.ts) - API, operacje
├── hooks/              # Custom hooks (.ts) - logika stanu
├── utils/              # Funkcje pomocnicze (.ts) - pure functions
├── types/              # Definicje typów TypeScript
└── assets/             # Zasoby statyczne
```

## Automatyzacja w VS Code

- **Format on Save** - automatyczne formatowanie przy zapisie
- **Fix on Save** - automatyczne poprawki ESLint przy zapisie
- **Organize Imports** - automatyczne sortowanie importów przy zapisie
- **Trim Whitespace** - usuwanie zbędnych spacji
- **Insert Final Newline** - dodawanie pustej linii na końcu pliku

## Integracja z Git

Pliki `.gitignore` i `.prettierignore` są skonfigurowane dla projektu mieszanego Python + TypeScript/JavaScript.

## Customizacja

Aby dostosować reguły formatowania:

1. **Python**: Edytuj sekcje `[tool.black]`, `[tool.isort]`, `[tool.pylint]` w `pyproject.toml`
2. **JavaScript/TypeScript**: Edytuj `.prettierrc` i `.eslintrc.json`
3. **VS Code**: Edytuj `.vscode/settings.json`
