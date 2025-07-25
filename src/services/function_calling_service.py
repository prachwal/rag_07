"""
Function calling service for advanced RAG with iterative search.
Orchestrates LLM function calling with vector search tools.
"""

import json
from typing import Any, Dict, List, Optional

from src.config.config_manager import ConfigManager
from src.exceptions import ValidationError
from src.providers.base import LLMProvider, ProviderFactory, VectorDBProvider
from src.services.application_service import ApplicationService
from src.tools import FunctionExecutor, VectorSearchTools
from src.utils.logger import LoggerMixin


class FunctionCallingService(LoggerMixin):
    """Service for processing queries using LLM function calling."""

    def __init__(self, config_manager: ConfigManager):
        """Initialize function calling service.

        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.provider_factory = ProviderFactory(config_manager)

    async def process_question_with_tools(
        self,
        question: str,
        llm_provider_name: Optional[str] = None,
        llm_model_name: Optional[str] = None,
        vector_provider_name: Optional[str] = None,
        collection: Optional[str] = None,
        max_iterations: int = 5,
    ) -> Dict[str, Any]:
        """Process question using function calling approach.

        Args:
            question: User question to process
            llm_provider_name: LLM provider name (optional)
            vector_provider_name: Vector provider name (optional)
            collection: Collection name (optional)
            max_iterations: Maximum number of function calling iterations

        Returns:
            Dictionary with answer and function calling details
        """
        if not question.strip():
            raise ValidationError('Question cannot be empty')

        # Initialize providers
        llm_provider_name = (
            llm_provider_name or self.config_manager.config.default_llm_provider
        )
        vector_provider_name = (
            vector_provider_name or self.config_manager.config.default_vector_provider
        )

        llm_provider = await self.provider_factory.create_llm_provider(
            llm_provider_name
        )
        vector_provider = await self.provider_factory.create_vector_provider(
            vector_provider_name
        )

        try:
            # Check if provider supports function calling
            if not llm_provider.supports_function_calling():
                self.log_operation(
                    "function_calling_fallback",
                    llm_provider=llm_provider_name,
                    reason="no_function_calling_support",
                )
                # Fallback to traditional RAG
                return await self._fallback_to_traditional_rag(
                    question, llm_provider, vector_provider, collection, llm_model_name
                )

            # Setup tools
            tools = VectorSearchTools(vector_provider, llm_provider)
            executor = FunctionExecutor(tools)

            # Start conversation
            conversation = [
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": question},
            ]

            function_calls_log = []
            iteration = 0

            while iteration < max_iterations:
                iteration += 1

                self.log_operation(
                    "function_calling_iteration_started",
                    iteration=iteration,
                    max_iterations=max_iterations,
                )

                # Call LLM with functions
                response = await llm_provider.chat_completion_with_functions(
                    messages=conversation,
                    functions=tools.get_function_definitions(),
                    function_call="auto",
                    temperature=0.1,
                    model=llm_model_name,
                )

                message = response["choices"][0]["message"]

                # Add assistant message
                conversation.append(
                    {
                        "role": "assistant",
                        "content": message.get("content"),
                        "function_call": message.get("function_call"),
                    }
                )

                # Check for function call
                if message.get("function_call"):
                    function_call = message["function_call"]
                    function_name = function_call["name"]

                    try:
                        function_args = json.loads(function_call["arguments"])
                    except json.JSONDecodeError as e:
                        # Handle malformed JSON in function arguments
                        error_msg = f"Invalid JSON in function arguments: {e}"
                        self.log_operation(
                            "function_calling_json_error",
                            error=error_msg,
                            raw_arguments=function_call["arguments"],
                        )

                        # Add error to conversation
                        conversation.append(
                            {
                                "role": "function",
                                "name": function_name,
                                "content": json.dumps(
                                    {"status": "error", "message": error_msg}
                                ),
                            }
                        )
                        continue

                    # Log function call
                    function_calls_log.append(
                        {
                            "iteration": iteration,
                            "function": function_name,
                            "arguments": function_args,
                            "timestamp": self._get_timestamp(),
                        }
                    )

                    self.log_operation(
                        "function_called",
                        function_name=function_name,
                        iteration=iteration,
                        args_summary=self._summarize_args(function_args),
                    )

                    # Execute function
                    function_result = await executor.execute_function(
                        function_name, function_args
                    )

                    # Add function result to conversation
                    conversation.append(
                        {
                            "role": "function",
                            "name": function_name,
                            "content": json.dumps(
                                function_result, ensure_ascii=False, indent=2
                            ),
                        }
                    )

                else:
                    # No more function calls - we have final answer
                    self.log_operation(
                        "function_calling_completed",
                        total_iterations=iteration,
                        function_calls_made=len(function_calls_log),
                    )
                    break

            final_answer = message.get("content", "No answer generated")

            # Extract sources from function calls
            sources_used = self._extract_sources_from_calls(function_calls_log)

            # Log operation completion
            self.log_operation(
                "function_calling_service_completed",
                question_length=len(question),
                iterations_used=iteration,
                function_calls_count=len(function_calls_log),
                llm_provider=llm_provider_name,
                vector_provider=vector_provider_name,
                sources_count=len(sources_used),
            )

            return {
                "answer": final_answer,
                "function_calls": function_calls_log,
                "conversation_history": conversation,
                "iterations_used": iteration,
                "sources_used": sources_used,
                "metadata": {
                    "llm_provider": llm_provider_name,
                    "vector_provider": vector_provider_name,
                    "collection": collection or "default",
                    "max_iterations": max_iterations,
                    "function_calling_used": True,
                },
            }

        finally:
            await llm_provider.cleanup()
            await vector_provider.cleanup()

    def _get_system_prompt(self) -> str:
        """Get system prompt for function calling."""
        return """You are an intelligent assistant with access to a knowledge base through search functions.

When a user asks a question:
1. Use the search_documents function to find relevant information
2. Analyze the search results carefully
3. If you need more specific information, use search_documents again with more targeted queries
4. You can also use get_document_details to get more context about specific documents
5. Once you have sufficient information, provide a comprehensive answer
6. Always cite the sources of your information using the document IDs or sources

Guidelines:
- Be thorough but efficient in your searches
- Don't make unnecessary function calls
- Use descriptive and specific search queries
- Combine information from multiple sources when relevant
- Provide clear citations for your sources"""

    async def _fallback_to_traditional_rag(
        self,
        question: str,
        llm_provider: LLMProvider,
        vector_provider: VectorDBProvider,
        collection: Optional[str],
        llm_model_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fallback to traditional RAG when function calling not supported.

        Args:
            question: User question
            llm_provider: LLM provider instance
            vector_provider: Vector provider instance
            collection: Collection name

        Returns:
            Traditional RAG result formatted as function calling result
        """
        # Use existing ApplicationService.rag_query logic
        app_service = ApplicationService(self.config_manager)

        # Map provider instances to names for rag_query
        vector_provider_name = vector_provider.__class__.__name__.replace(
            "Provider", ""
        ).lower()
        llm_provider_name = llm_provider.__class__.__name__.replace(
            "Provider", ""
        ).lower()

        answer = await app_service.rag_query(
            question=question,
            llm_provider=llm_provider_name,
            llm_model=llm_model_name,
            vector_provider=vector_provider_name,
            collection=collection,
        )

        self.log_operation(
            "traditional_rag_fallback_used",
            llm_provider=llm_provider_name,
            vector_provider=vector_provider_name,
        )

        return {
            "answer": answer,
            "function_calls": [],
            "conversation_history": [],
            "iterations_used": 1,
            "sources_used": [],
            "metadata": {
                "llm_provider": llm_provider_name,
                "vector_provider": vector_provider_name,
                "collection": collection or "default",
                "fallback_used": True,
                "function_calling_used": False,
            },
        }

    def _extract_sources_from_calls(
        self, function_calls_log: List[Dict[str, Any]]
    ) -> List[str]:
        """Extract source information from function calls.

        Args:
            function_calls_log: List of function call records

        Returns:
            List of unique sources found
        """
        sources = set()

        for call in function_calls_log:
            if call["function"] == "search_documents":
                # Extract query as source indicator
                query = call["arguments"].get("query", "")
                if query:
                    sources.add(f"Search: {query}")

        return list(sources)

    def _summarize_args(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of function arguments for logging.

        Args:
            args: Function arguments

        Returns:
            Summarized arguments for logging
        """
        summary = {}
        for key, value in args.items():
            if isinstance(value, str) and len(value) > 50:
                summary[key] = value[:50] + "..."
            else:
                summary[key] = value
        return summary

    def _get_timestamp(self) -> str:
        """Get current timestamp string.

        Returns:
            ISO format timestamp
        """
        from datetime import datetime

        return datetime.now().isoformat()
