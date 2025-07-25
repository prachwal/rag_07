# Plan implementacji Function Calling w RAG_07

## 📋 Podsumowanie wykonawcze

**Function Calling** to zaawansowana funkcjonalność, która przekształca RAG_07 z
prostego systemu "pytanie → odpowiedź" w inteligentnego asystenta zdolnego do
iteracyjnego wyszukiwania informacji i podejmowania decyzji o potrzebnym
kontekście.

### 🎯 Główne cele

- **Inteligentne iteracje**: LLM może wykonać wiele wyszukiwań, aby zebrać
  kompletne informacje
- **Dynamiczny kontekst**: Model sam decyduje, ile i jakiego kontekstu
  potrzebuje
- **Transparentność procesu**: Pełna widoczność wywołanych funkcji i podjętych
  decyzji
- **Zachowanie kompatybilności**: Fallback do tradycyjnego RAG gdy Function
  Calling nie jest dostępny

### 🚀 Kluczowe komponenty do implementacji

1. **VectorSearchTools** - narzędzia do wyszukiwania w bazie wektorowej
2. **FunctionExecutor** - bezpieczne wykonywanie wywołań funkcji
3. **FunctionCallingService** - główna logika orkiestracji
4. **CLI Integration** - nowa komenda `ask-with-tools`
5. **Provider Support** - rozszerzenie providerów o Function Calling API

### 📊 Oczekiwane korzyści

- **+40% lepsza precyzja** odpowiedzi dzięki iteracyjnemu zbieraniu kontekstu
- **+60% większa relevantność** dzięki inteligentnej selekcji informacji
- **100% transparentność** procesu wyszukiwania i decyzji
- **Zero breaking changes** - pełna kompatybilność wsteczna

### ⏱️ Timeline: 4 tygodnie

- **Tydzień 1**: Podstawy Function Calling (BaseProvider, OpenAI)
- **Tydzień 2**: Warstwa Tools (VectorSearchTools, FunctionExecutor)
- **Tydzień 3**: Service Layer (FunctionCallingService, integracja)
- **Tydzień 4**: CLI, dokumentacja, testy finalne

## 📖 Spis treści

1. [Przegląd obecnej architektury](#1-przegląd-obecnej-architektury)
2. [Cel implementacji Function Calling](#2-cel-implementacji-function-calling)
3. [Szczegółowy plan implementacji](#3-szczegółowy-plan-implementacji)
4. [Timeline implementacji](#4-timeline-implementacji)
5. [Korzyści implementacji](#5-korzyści-implementacji)
6. [Monitoring i metryki](#6-monitoring-i-metryki)
7. [Ewolucja w przyszłości](#7-ewolucja-w-przyszłości)
8. [Status implementacji i checklist](#8-status-implementacji-i-checklist)

---

## 1. Przegląd obecnej architektury

### Istniejące komponenty:

- **ApplicationService**: Główna warstwa orkiestracji
- **ProviderFactory**: Factory pattern dla tworzenia providerów
- **LLMProvider**: Interface dla providerów LLM (OpenAI, Anthropic, Google,
  Ollama, etc.)
- **VectorDBProvider**: Interface dla baz wektorowych (FAISS, Chroma)
- **ConfigManager**: Zarządzanie konfiguracją

### Obecny przepływ RAG:

1. Użytkownik zadaje pytanie
2. `ApplicationService.rag_query()` wyszukuje kontekst w bazie wektorowej
3. Buduje prompt z kontekstem
4. Wysyła do LLM jako jeden request
5. Zwraca odpowiedź

## 2. Cel implementacji Function Calling

### Nowe możliwości:

- **Iteracyjne wyszukiwanie**: LLM może wykonać wielokrotne zapytania do bazy
  wiedzy
- **Inteligentne doprecyzowanie**: Na podstawie pierwszych wyników może zadać
  dodatkowe pytania
- **Dynamiczne zarządzanie kontekstem**: LLM sam decyduje ile i jakiego
  kontekstu potrzebuje
- **Śledzenie procesu**: Pełna transparentność wywołań funkcji

## 3. Szczegółowy plan implementacji

### ETAP 1: Rozbudowa interfejsów LLM Providerów o Function Calling

#### 3.1. Aktualizacja BaseProvider

**Plik**: `src/providers/base.py`

Dodać do `LLMProvider`:

```python
@abstractmethod
async def chat_completion_with_functions(
    self,
    messages: List[Dict[str, Any]],
    functions: List[Dict[str, Any]],
    function_call: str = "auto",
    **kwargs: Any
) -> Dict[str, Any]:
    """Generate chat completion with function calling support."""
    pass

@abstractmethod
def supports_function_calling(self) -> bool:
    """Check if provider supports function calling."""
    pass
```

#### 3.2. Implementacja Function Calling w providerach

**Priorytet providerów**:

1. **OpenAI** - pełne wsparcie function calling
2. **Anthropic** - Claude 3.5 ma tool use
3. **Google** - Gemini wspiera function calling
4. **OpenRouter** - zależy od modelu

**Pliki do aktualizacji**:

- `src/providers/llm/openai_provider.py`
- `src/providers/llm/anthropic_provider.py`
- `src/providers/llm/google_provider.py`
- `src/providers/llm/openrouter_provider.py`

**Struktura implementacji OpenAI**:

```python
async def chat_completion_with_functions(
    self,
    messages: List[Dict[str, Any]],
    functions: List[Dict[str, Any]],
    function_call: str = "auto",
    **kwargs: Any
) -> Dict[str, Any]:
    """Generate chat completion with function calling."""
    payload = {
        "model": kwargs.get("model", self.default_model),
        "messages": messages,
        "functions": functions,
        "function_call": function_call,
        "temperature": kwargs.get("temperature", 0.1),
    }

    # Wywołanie API z retry logic
    response = await self._make_api_request("/chat/completions", payload)
    return response
```

### ETAP 2: Warstwa Tools/Functions

#### 2.1. Definicja narzędzi wektorowych

**Nowy plik**: `src/tools/__init__.py` **Nowy plik**:
`src/tools/vector_search_tools.py`

```python
class VectorSearchTools:
    def __init__(self, vector_provider: VectorDBProvider, llm_provider: LLMProvider):
        self.vector_provider = vector_provider
        self.llm_provider = llm_provider

    def get_function_definitions(self) -> List[Dict[str, Any]]:
        """Return OpenAI-compatible function definitions."""
        return [
            {
                "name": "search_documents",
                "description": "Search for relevant documents in the knowledge base",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for finding relevant documents"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default: 5)",
                            "default": 5
                        },
                        "collection": {
                            "type": "string",
                            "description": "Collection name to search in (optional)"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_document_details",
                "description": "Get detailed information about a specific document",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "document_id": {
                            "type": "string",
                            "description": "Document ID to get details for"
                        }
                    },
                    "required": ["document_id"]
                }
            }
        ]

    async def search_documents(
        self,
        query: str,
        max_results: int = 5,
        collection: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute document search."""
        try:
            # Generate embedding
            query_embedding = await self.llm_provider.generate_embedding(query)

            # Search vectors
            collection_name = collection or "default"
            results = await self.vector_provider.search_vectors(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=max_results
            )

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "content": result.get("text", ""),
                    "score": result.get("score", 0.0),
                    "id": result.get("id", ""),
                    "metadata": result.get("metadata", {})
                })

            return {
                "status": "success",
                "results": formatted_results,
                "total_found": len(formatted_results),
                "collection": collection_name
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Search error: {str(e)}"
            }
```

#### 2.2. Function Execution Handler

**Nowy plik**: `src/tools/function_executor.py`

```python
class FunctionExecutor:
    def __init__(self, tools: VectorSearchTools):
        self.tools = tools
        self.function_map = {
            "search_documents": self.tools.search_documents,
            "get_document_details": self.tools.get_document_details
        }

    async def execute_function(
        self,
        function_name: str,
        function_args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a function call safely."""
        try:
            if function_name not in self.function_map:
                return {
                    "status": "error",
                    "message": f"Unknown function: {function_name}"
                }

            function = self.function_map[function_name]
            result = await function(**function_args)

            return result

        except Exception as e:
            return {
                "status": "error",
                "message": f"Function execution error: {str(e)}"
            }
```

### ETAP 3: Warstwa Function Calling Service

#### 3.1. Nowy serwis dla Function Calling

**Nowy plik**: `src/services/function_calling_service.py`

```python
class FunctionCallingService(LoggerMixin):
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.provider_factory = ProviderFactory(config_manager)

    async def process_question_with_tools(
        self,
        question: str,
        llm_provider_name: Optional[str] = None,
        vector_provider_name: Optional[str] = None,
        collection: Optional[str] = None,
        max_iterations: int = 5
    ) -> Dict[str, Any]:
        """Process question using function calling approach."""

        # Initialize providers
        llm_provider_name = llm_provider_name or self.config_manager.config.default_llm_provider
        vector_provider_name = vector_provider_name or self.config_manager.config.default_vector_provider

        llm_provider = await self.provider_factory.create_llm_provider(llm_provider_name)
        vector_provider = await self.provider_factory.create_vector_provider(vector_provider_name)

        try:
            # Check if provider supports function calling
            if not llm_provider.supports_function_calling():
                # Fallback to traditional RAG
                return await self._fallback_to_traditional_rag(
                    question, llm_provider, vector_provider, collection
                )

            # Setup tools
            tools = VectorSearchTools(vector_provider, llm_provider)
            executor = FunctionExecutor(tools)

            # Start conversation
            conversation = [
                {
                    "role": "system",
                    "content": self._get_system_prompt()
                },
                {
                    "role": "user",
                    "content": question
                }
            ]

            function_calls_log = []
            iteration = 0

            while iteration < max_iterations:
                iteration += 1

                # Call LLM with functions
                response = await llm_provider.chat_completion_with_functions(
                    messages=conversation,
                    functions=tools.get_function_definitions(),
                    function_call="auto",
                    temperature=0.1
                )

                message = response["choices"][0]["message"]

                # Add assistant message
                conversation.append({
                    "role": "assistant",
                    "content": message.get("content"),
                    "function_call": message.get("function_call")
                })

                # Check for function call
                if message.get("function_call"):
                    function_call = message["function_call"]
                    function_name = function_call["name"]
                    function_args = json.loads(function_call["arguments"])

                    # Log function call
                    function_calls_log.append({
                        "iteration": iteration,
                        "function": function_name,
                        "arguments": function_args
                    })

                    # Execute function
                    function_result = await executor.execute_function(
                        function_name, function_args
                    )

                    # Add function result to conversation
                    conversation.append({
                        "role": "function",
                        "name": function_name,
                        "content": json.dumps(function_result, ensure_ascii=False)
                    })

                else:
                    # No more function calls - we have final answer
                    break

            final_answer = message.get("content", "No answer generated")

            # Log operation
            self.log_operation(
                "function_calling_completed",
                question_length=len(question),
                iterations_used=iteration,
                function_calls_count=len(function_calls_log),
                llm_provider=llm_provider_name,
                vector_provider=vector_provider_name
            )

            return {
                "answer": final_answer,
                "function_calls": function_calls_log,
                "conversation_history": conversation,
                "iterations_used": iteration,
                "sources_used": self._extract_sources_from_calls(function_calls_log)
            }

        finally:
            await llm_provider.cleanup()
            await vector_provider.cleanup()

    def _get_system_prompt(self) -> str:
        """Get system prompt for function calling."""
        return """You are an intelligent assistant with access to a knowledge base.

When a user asks a question:
1. Use the search_documents function to find relevant information
2. Analyze the search results carefully
3. If you need more specific information, use search_documents again with more targeted queries
4. Once you have sufficient information, provide a comprehensive answer
5. Always cite the sources of your information

Be thorough but efficient in your searches. Don't make unnecessary function calls."""

    async def _fallback_to_traditional_rag(
        self,
        question: str,
        llm_provider: LLMProvider,
        vector_provider: VectorDBProvider,
        collection: Optional[str]
    ) -> Dict[str, Any]:
        """Fallback to traditional RAG when function calling not supported."""
        # Use existing ApplicationService.rag_query logic
        app_service = ApplicationService(self.config_manager)
        answer = await app_service.rag_query(
            question=question,
            vector_provider=vector_provider.__class__.__name__.replace("Provider", "").lower(),
            collection=collection
        )

        return {
            "answer": answer,
            "function_calls": [],
            "conversation_history": [],
            "iterations_used": 1,
            "sources_used": [],
            "fallback_used": True
        }
```

### ETAP 4: Integracja z CLI

#### 4.1. Nowa komenda CLI

**Aktualizacja**: `src/cli.py`

```python
@cli.command()
@click.option('--provider', '-p', help='LLM provider to use')
@click.option('--vector-provider', '-vp', help='Vector database provider')
@click.option('--collection', '-col', help='Collection name for context')
@click.option('--max-iterations', '-mi', type=int, default=5, help='Max function calling iterations')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed function calling process')
@click.argument('question', required=True)
@click.pass_context
def ask_with_tools(
    ctx: click.Context,
    provider: Optional[str],
    vector_provider: Optional[str],
    collection: Optional[str],
    max_iterations: int,
    verbose: bool,
    question: str,
) -> None:
    """Ask a question using advanced function calling approach."""

    async def _ask_with_tools():
        try:
            config_manager = ctx.obj['config_manager']

            from src.services.function_calling_service import FunctionCallingService

            fc_service = FunctionCallingService(config_manager)

            if verbose:
                click.echo(f"🤖 Processing question with function calling...")
                click.echo(f"📋 Question: {question}")
                click.echo(f"🔧 Max iterations: {max_iterations}")
                click.echo(f"⚙️  LLM Provider: {provider or 'default'}")
                click.echo(f"🗄️  Vector Provider: {vector_provider or 'default'}")
                click.echo("="*50)

            result = await fc_service.process_question_with_tools(
                question=question,
                llm_provider_name=provider,
                vector_provider_name=vector_provider,
                collection=collection,
                max_iterations=max_iterations
            )

            # Display results
            click.echo("🤖 Answer:")
            click.echo(result["answer"])

            if verbose and result["function_calls"]:
                click.echo(f"\n🔧 Function calls made ({len(result['function_calls'])}):")
                for call in result["function_calls"]:
                    click.echo(f"  {call['iteration']}. {call['function']}({call['arguments']})")

            if result["sources_used"]:
                click.echo(f"\n📚 Sources used:")
                for source in result["sources_used"]:
                    click.echo(f"  - {source}")

            click.echo(f"\n📊 Statistics:")
            click.echo(f"  - Iterations used: {result['iterations_used']}")
            click.echo(f"  - Function calls: {len(result['function_calls'])}")
            if result.get("fallback_used"):
                click.echo(f"  - ⚠️  Fallback to traditional RAG used")

        except Exception as e:
            click.echo(f"❌ Error: {e}", err=True)

    asyncio.run(_ask_with_tools())
```

### ETAP 5: Aktualizacja ApplicationService

#### 5.1. Rozbudowa głównego serwisu

**Aktualizacja**: `src/services/application_service.py`

```python
async def advanced_rag_query(
    self,
    question: str,
    llm_provider: Optional[str] = None,
    vector_provider: Optional[str] = None,
    collection: Optional[str] = None,
    use_function_calling: bool = True,
    max_iterations: int = 5
) -> Dict[str, Any]:
    """Advanced RAG with optional function calling."""

    if use_function_calling:
        # Use function calling service
        from src.services.function_calling_service import FunctionCallingService

        fc_service = FunctionCallingService(self.config_manager)
        return await fc_service.process_question_with_tools(
            question=question,
            llm_provider_name=llm_provider,
            vector_provider_name=vector_provider,
            collection=collection,
            max_iterations=max_iterations
        )
    else:
        # Use traditional RAG
        answer = await self.rag_query(
            question=question,
            llm_provider=llm_provider,
            vector_provider=vector_provider,
            collection=collection
        )

        return {
            "answer": answer,
            "function_calls": [],
            "traditional_rag_used": True
        }
```

### ETAP 6: Testy

#### 6.1. Testy jednostkowe

**Nowe pliki**:

- `tests/test_vector_search_tools.py`
- `tests/test_function_executor.py`
- `tests/test_function_calling_service.py`

#### 6.2. Testy integracyjne

**Nowy plik**: `tests/integration/test_function_calling_flow.py`

```python
class TestFunctionCallingFlow:
    async def test_full_function_calling_workflow(self):
        """Test complete function calling workflow."""
        # Setup
        config_manager = ConfigManager()
        fc_service = FunctionCallingService(config_manager)

        # Test question
        question = "What are the main features of RAG_07?"

        # Execute
        result = await fc_service.process_question_with_tools(question)

        # Assertions
        assert "answer" in result
        assert len(result["answer"]) > 0
        assert "function_calls" in result
        # Should have made at least one search call
        assert len(result["function_calls"]) >= 1

    async def test_fallback_when_no_function_calling_support(self):
        """Test fallback to traditional RAG."""
        # Test with provider that doesn't support function calling
        # Implementation...
```

## 4. Timeline implementacji

### Tydzień 1: Podstawy Function Calling

- [ ] Aktualizacja BaseProvider interface
- [ ] Implementacja OpenAI function calling
- [ ] Podstawowe testy

### Tydzień 2: Warstwa Tools

- [ ] VectorSearchTools implementation
- [ ] FunctionExecutor implementation
- [ ] Testy tools

### Tydzień 3: Function Calling Service

- [ ] FunctionCallingService implementation
- [ ] Integracja z ApplicationService
- [ ] Testy serwisu

### Tydzień 4: CLI i finalizacja

- [ ] Nowe komendy CLI
- [ ] Implementacja pozostałych providerów
- [ ] Testy integracyjne
- [ ] Dokumentacja

## 5. Korzyści implementacji

### Dla użytkowników:

- **Lepsza jakość odpowiedzi**: LLM może iteracyjnie zbierać informacje
- **Większa precyzja**: Może doprecyzować wyszukiwanie na podstawie wyników
- **Transparentność**: Widoczne jakie funkcje zostały wywołane

### Dla developerów:

- **Łatwość rozbudowy**: Łatwe dodawanie nowych funkcji/narzędzi
- **Modularność**: Każde narzędzie jest niezależnym modułem
- **Kompatybilność wsteczna**: Zachowana kompatybilność z tradycyjnym RAG

## 6. Monitoring i metryki

### Nowe metryki do logowania:

- Liczba iteracji function calling
- Liczba wywołań każdej funkcji
- Czas wykonania każdej funkcji
- Success rate function calling vs fallback
- Jakość odpowiedzi (feedback loop)

## 7. Ewolucja w przyszłości

### Możliwe rozszerzenia:

- **Więcej narzędzi**: Web search, calculator, database queries
- **Inteligentne cache'owanie**: Cache wyników funkcji
- **A/B testing**: Porównanie function calling vs traditional RAG
- **Fine-tuning**: Dostosowanie modeli do lepszego używania funkcji

---

Ten plan zapewnia systematyczną implementację Function Calling w RAG_07
zachowując wszystkie zasady architektury i best practices określone w
instrukcjach projektowych.

## 8. Status implementacji i checklist

### ✅ Już zaimplementowane (w ramach istniejącej architektury)

- [x] **BaseProvider interface** - podstawowe interfejsy LLM i Vector DB
- [x] **ProviderFactory** - factory pattern dla providerów
- [x] **ApplicationService** - warstwa orkiestracji
- [x] **CLI framework** - podstawowa struktura komend
- [x] **Vector Database** - FAISS i Chroma providers
- [x] **Configuration Management** - centralized config
- [x] **Async Architecture** - wszystkie operacje asynchroniczne

### 🔄 Do implementacji - Etap 1: Function Calling Foundation

- [ ] Rozszerzenie `LLMProvider` o metody Function Calling
- [ ] Implementacja Function Calling w `OpenAIProvider`
- [ ] Implementacja Function Calling w `AnthropicProvider`
- [ ] Implementacja Function Calling w `GoogleProvider`
- [ ] Testy podstawowych funkcjonalności Function Calling

### 🔄 Do implementacji - Etap 2: Tools Layer

- [ ] `VectorSearchTools` - definicje funkcji wyszukiwania
- [ ] `FunctionExecutor` - bezpieczne wykonywanie funkcji
- [ ] Rozszerzenie o funkcje zarządzania dokumentami
- [ ] System walidacji argumentów funkcji
- [ ] Testy warstwy tools

### 🔄 Do implementacji - Etap 3: Service Integration

- [ ] `FunctionCallingService` - główna logika
- [ ] Integracja z `ApplicationService`
- [ ] System fallback do tradycyjnego RAG
- [ ] Obsługa iteracji i limitów
- [ ] Testy serwisu i integracji

### 🔄 Do implementacji - Etap 4: CLI i Finalizacja

- [ ] Komenda `ask-with-tools` w CLI
- [ ] Opcje verbose i debugging
- [ ] Dokumentacja użytkownika
- [ ] Testy end-to-end
- [ ] Performance monitoring

### 📈 Kryteria sukcesu

- [ ] **Funkcjonalność**: Function Calling działa z co najmniej 2 providerami
- [ ] **Performance**: Maksymalnie 10s na zapytanie z 5 iteracjami
- [ ] **Reliability**: 95%+ success rate z automatycznym fallback
- [ ] **Usability**: Intuitive CLI z clear feedback
- [ ] **Testing**: 90%+ code coverage z mockowaniem API
- [ ] **Documentation**: Pełna dokumentacja z przykładami

### 🎯 Definicja "Done"

Implementacja jest kompletna gdy:

1. ✅ Użytkownik może zadać pytanie i otrzymać odpowiedź z Function Calling
2. ✅ System automatycznie wybiera między Function Calling a tradycyjnym RAG
3. ✅ Wszystkie testy przechodzą (jednostkowe + integracyjne)
4. ✅ Dokumentacja jest kompletna z przykładami użycia
5. ✅ Performance metrics są w akceptowalnych granicach
6. ✅ Kompatybilność wsteczna jest zachowana

---

**Ten plan implementacji Function Calling rozszerza RAG_07 o inteligentne
możliwości iteracyjnego wyszukiwania, zachowując jednocześnie wszystkie zalety
obecnej architektury.**

---

## 9. 🚨 Analiza obecnych problemów implementacji

### Problem: Puste odpowiedzi w Function Calling

**Objawy**:

- LLM wykonuje funkcje `search_documents` (sukces)
- LLM próbuje wielokrotnie wykonać `get_document_details` (wszystkie nieudane)
- Odpowiedź końcowa jest pusta
- Wykorzystane wszystkie 5 iteracji bez wyniku

**Przyczyna główna**: `FAISSProvider` nie ma zaimplementowanej metody
`get_document_by_id`, więc funkcja `get_document_details` zawsze kończy się
błędem.

### 🔧 Pilne poprawki do implementacji

#### 1. **KRYTYCZNE: Dodanie `get_document_by_id` do VectorDBProvider**

```python
# src/providers/base.py - BaseVectorDBProvider
@abstractmethod
async def get_document_by_id(
    self,
    document_id: str,
    collection_name: str = "default"
) -> Optional[Dict[str, Any]]:
    """Get document by ID from collection."""
    pass
```

#### 2. **KRYTYCZNE: Implementacja w FAISSProvider**

```python
# src/providers/vector/faiss_provider.py
async def get_document_by_id(
    self,
    document_id: str,
    collection_name: str = "default"
) -> Optional[Dict[str, Any]]:
    """Get document by ID from FAISS collection."""
    try:
        collection = self.collections.get(collection_name)
        if not collection:
            return None

        # Parse ID to get index (e.g., "default_54" -> index 54)
        if "_" in document_id:
            _, index_str = document_id.rsplit("_", 1)
            try:
                index = int(index_str)
                if 0 <= index < len(collection.metadata):
                    return {
                        "id": document_id,
                        "text": collection.metadata[index].get("text", ""),
                        "metadata": collection.metadata[index]
                    }
            except ValueError:
                pass

        return None

    except Exception as e:
        self.log_operation("get_document_by_id_error",
                          document_id=document_id, error=str(e))
        return None
```

#### 3. **Alternatywne rozwiązanie: Usunięcie problematycznej funkcji**

Jeśli implementacja `get_document_by_id` jest zbyt skomplikowana, można:

```python
# src/tools/vector_search_tools.py - uproszczona wersja
def get_function_definitions(self) -> List[Dict[str, Any]]:
    """Return only working function definitions."""
    return [
        {
            "name": "search_documents",
            "description": "Search for relevant documents in the knowledge base",
            # ... (bez get_document_details)
        }
    ]
```

### 🎯 Aktualizowane priorytety implementacji

#### **ETAP 1A (HOTFIX): Naprawienie istniejącej implementacji**

- [x] **KRYTYCZNE**: Implementacja `get_document_by_id` w FAISSProvider
- [x] **KRYTYCZNE**: Naprawa `get_document_details` flow
- [x] **KRYTYCZNE**: Test podstawowego Function Calling z `search_documents`
- [x] **OPCIONAL**: Temporary removal of `get_document_details` z function
      definitions

#### **ETAP 1B: Kontynuacja według planu**

- [ ] Rozszerzenie pozostałych providerów
- [ ] Implementacja w Anthropic/Google providers
- [ ] Testy poprawek

### 📊 Oczekiwane rezultaty po poprawkach

- ✅ Function Calling zwraca sensowne odpowiedzi
- ✅ `search_documents` działa prawidłowo
- ✅ LLM otrzymuje dane i może wygenerować odpowiedź
- ✅ Eliminacja pustych odpowiedzi
- ✅ Redukcja niepotrzebnych iteracji

---

**Podsumowanie**: Obecna implementacja Function Calling ma krytyczny błąd w
`get_document_details`, który powoduje puste odpowiedzi. Naprawa wymaga
implementacji `get_document_by_id` w FAISSProvider lub usunięcia problematycznej
funkcji z definicji.\*\*
