"""
Application service layer for RAG_07.
Orchestrates operations between providers and handles business logic.
"""

from typing import Any, Dict, List, Optional

from src.config.config_manager import ConfigManager
from src.exceptions import ValidationError
from src.providers.base import ProviderFactory
from src.utils.logger import LoggerMixin


class ApplicationService(LoggerMixin):
    """Main application service for RAG operations."""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.provider_factory = ProviderFactory(config_manager)

    async def process_query(
        self, query: str, provider: Optional[str] = None, model: Optional[str] = None
    ) -> str:
        """Process a direct LLM query."""
        if not query.strip():
            raise ValidationError('Query cannot be empty')

        provider_name = provider or self.config_manager.config.default_llm_provider
        llm_provider = await self.provider_factory.create_llm_provider(provider_name)

        try:
            result = await llm_provider.generate_text(query, model=model)
            self.log_operation(
                'processed_query',
                provider=provider_name,
                query_length=len(query),
                response_length=len(result),
            )
            return result
        finally:
            await llm_provider.cleanup()

    async def add_to_vector_store(
        self,
        text: str,
        provider: Optional[str] = None,
        collection: Optional[str] = None,
    ) -> str:
        """Add text to vector database."""
        if not text.strip():
            raise ValidationError('Text cannot be empty')

        # Get providers
        vector_provider_name = (
            provider or self.config_manager.config.default_vector_provider
        )
        llm_provider_name = self.config_manager.config.default_llm_provider

        vector_provider = await self.provider_factory.create_vector_provider(
            vector_provider_name
        )
        llm_provider = await self.provider_factory.create_llm_provider(
            llm_provider_name
        )
        text_processor = await self.provider_factory.create_text_processor()

        try:
            # Process text
            chunks = await text_processor.chunk_text(text)
            collection_name = collection or 'default'

            # Generate embeddings
            embeddings = []
            for chunk in chunks:
                embedding = await llm_provider.generate_embedding(chunk)
                embeddings.append(embedding)

            # Add to vector store
            ids = await vector_provider.add_vectors(
                collection_name=collection_name, vectors=embeddings, texts=chunks
            )

            result = f'Added {len(chunks)} chunks to collection {collection_name}'
            self.log_operation(
                'added_to_vector_store',
                provider=vector_provider_name,
                collection=collection_name,
                chunks_count=len(chunks),
                ids=ids,
            )

            return result

        finally:
            await vector_provider.cleanup()
            await llm_provider.cleanup()
            await text_processor.cleanup()

    async def search_vector_store(
        self,
        query: str,
        provider: Optional[str] = None,
        collection: Optional[str] = None,
        limit: int = 5,
    ) -> List[str]:
        """Search in vector database."""
        if not query.strip():
            raise ValidationError('Query cannot be empty')

        # Get providers
        vector_provider_name = (
            provider or self.config_manager.config.default_vector_provider
        )
        llm_provider_name = self.config_manager.config.default_llm_provider

        vector_provider = await self.provider_factory.create_vector_provider(
            vector_provider_name
        )
        llm_provider = await self.provider_factory.create_llm_provider(
            llm_provider_name
        )

        try:
            # Generate query embedding
            query_embedding = await llm_provider.generate_embedding(query)

            # Search vector store
            collection_name = collection or 'default'
            results = await vector_provider.search_vectors(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=limit,
            )

            # Extract texts
            texts = [result['text'] for result in results]

            self.log_operation(
                'searched_vector_store',
                provider=vector_provider_name,
                collection=collection_name,
                query_length=len(query),
                results_count=len(texts),
            )

            return texts

        finally:
            await vector_provider.cleanup()
            await llm_provider.cleanup()

    async def rag_query(
        self,
        question: str,
        llm_provider: Optional[str] = None,
        vector_provider: Optional[str] = None,
        collection: Optional[str] = None,
        context_limit: int = 3,
    ) -> str:
        """Answer question using RAG (Retrieval-Augmented Generation)."""
        if not question.strip():
            raise ValidationError('Question cannot be empty')

        # Get context from vector store
        context_texts = await self.search_vector_store(
            query=question,
            provider=vector_provider,
            collection=collection,
            limit=context_limit,
        )

        # Build prompt with context
        if context_texts:
            context = '\n\n'.join(
                f'Context {i+1}: {text}' for i, text in enumerate(context_texts)
            )
            prompt = f"""Based on the following context, answer the question.

{context}

Question: {question}

Answer:"""
        else:
            prompt = f"""Question: {question}

Answer:"""

        # Generate answer
        answer = await self.process_query(query=prompt, provider=llm_provider)

        self.log_operation(
            'rag_query_completed',
            question_length=len(question),
            context_count=len(context_texts),
            answer_length=len(answer),
        )

        return answer

    async def advanced_rag_query(
        self,
        question: str,
        llm_provider: Optional[str] = None,
        vector_provider: Optional[str] = None,
        collection: Optional[str] = None,
        use_function_calling: bool = True,
        max_iterations: int = 5,
    ) -> Dict[str, Any]:
        """Advanced RAG with optional function calling.

        Args:
            question: User question
            llm_provider: LLM provider name (optional)
            vector_provider: Vector provider name (optional)
            collection: Collection name (optional)
            use_function_calling: Whether to use function calling
                (default: True)
            max_iterations: Maximum function calling iterations

        Returns:
            Dictionary with answer and metadata
        """
        if use_function_calling:
            # Use function calling service
            from src.services.function_calling_service import FunctionCallingService

            fc_service = FunctionCallingService(self.config_manager)
            return await fc_service.process_question_with_tools(
                question=question,
                llm_provider_name=llm_provider,
                vector_provider_name=vector_provider,
                collection=collection,
                max_iterations=max_iterations,
            )
        else:
            # Use traditional RAG
            answer = await self.rag_query(
                question=question,
                llm_provider=llm_provider,
                vector_provider=vector_provider,
                collection=collection,
            )

            return {
                "answer": answer,
                "function_calls": [],
                "conversation_history": [],
                "iterations_used": 1,
                "sources_used": [],
                "metadata": {
                    "traditional_rag_used": True,
                    "function_calling_used": False,
                },
            }
