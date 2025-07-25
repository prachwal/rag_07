"""
CLI module for RAG_07 application.
Handles command-line interface and argument parsing.
"""

import asyncio
from pathlib import Path
from typing import Optional

import click

from src.config.config_manager import ConfigManager
from src.services.application_service import ApplicationService
from src.utils.logger import get_logger

logger = get_logger(__name__)


@click.group()
@click.option('--config', '-c', help='Path to configuration file')
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.pass_context
def cli(ctx: click.Context, config: Optional[str], debug: bool) -> None:
    """RAG_07 - Multi-provider LLM application with RAG and vector database support."""
    ctx.ensure_object(dict)

    # Initialize configuration
    config_path = Path(config) if config else None
    ctx.obj['config_manager'] = ConfigManager(config_path)
    ctx.obj['debug'] = debug

    if debug:
        logger.info('Debug mode enabled')


@cli.command()
@click.option(
    '--provider', '-p', help='LLM provider to use (openai, anthropic, google)'
)
@click.option('--model', '-m', help='Model name to use')
@click.argument('query', required=True)
@click.pass_context
def query(
    ctx: click.Context, provider: Optional[str], model: Optional[str], query: str
) -> None:
    """Send a query to the LLM provider."""

    async def _query():
        config_manager = ctx.obj['config_manager']
        app_service = ApplicationService(config_manager)

        result = await app_service.process_query(
            query=query, provider=provider, model=model
        )
        click.echo(result)

    asyncio.run(_query())


@cli.command()
@click.option(
    '--provider', '-p', help='Vector database provider (faiss, chroma, pinecone)'
)
@click.option('--collection', '-col', help='Collection name')
@click.argument('text', required=True)
@click.pass_context
def embed(
    ctx: click.Context, provider: Optional[str], collection: Optional[str], text: str
) -> None:
    """Add text to vector database."""

    async def _embed():
        config_manager = ctx.obj['config_manager']
        app_service = ApplicationService(config_manager)

        result = await app_service.add_to_vector_store(
            text=text, provider=provider, collection=collection
        )
        click.echo(f'Added to vector store: {result}')

    asyncio.run(_embed())


@cli.command()
@click.option(
    '--provider', '-p', help='Vector database provider (faiss, chroma, pinecone)'
)
@click.option('--collection', '-col', help='Collection name')
@click.option('--limit', '-l', type=int, default=5, help='Number of results to return')
@click.argument('query', required=True)
@click.pass_context
def search(
    ctx: click.Context,
    provider: Optional[str],
    collection: Optional[str],
    limit: int,
    query: str,
) -> None:
    """Search in vector database."""

    async def _search():
        config_manager = ctx.obj['config_manager']
        app_service = ApplicationService(config_manager)

        results = await app_service.search_vector_store(
            query=query, provider=provider, collection=collection, limit=limit
        )

        for i, result in enumerate(results, 1):
            click.echo(f'{i}. {result}')

    asyncio.run(_search())


@cli.command()
@click.option('--provider', '-p', help='LLM provider to use')
@click.option('--vector-provider', '-vp', help='Vector database provider')
@click.option('--collection', '-col', help='Collection name for context')
@click.option(
    '--context-limit', '-cl', type=int, default=3, help='Number of context items'
)
@click.argument('question', required=True)
@click.pass_context
def rag(
    ctx: click.Context,
    provider: Optional[str],
    vector_provider: Optional[str],
    collection: Optional[str],
    context_limit: int,
    question: str,
) -> None:
    """Ask a question using RAG (Retrieval-Augmented Generation)."""

    async def _rag():
        config_manager = ctx.obj['config_manager']
        app_service = ApplicationService(config_manager)

        answer = await app_service.rag_query(
            question=question,
            llm_provider=provider,
            vector_provider=vector_provider,
            collection=collection,
            context_limit=context_limit,
        )
        click.echo(answer)

    asyncio.run(_rag())


@cli.command()
@click.pass_context
def config_status(ctx: click.Context) -> None:
    """Show current configuration status."""
    config_manager = ctx.obj['config_manager']
    status = config_manager.get_status()

    click.echo('Configuration Status:')
    click.echo(f'Config file: {status.get("config_file", "default")}')
    click.echo(f'Available LLM providers: {", ".join(status.get("llm_providers", []))}')
    click.echo(
        f'Available vector DB providers: {", ".join(status.get("vector_providers", []))}'
    )
    click.echo(f'Default LLM provider: {status.get("default_llm_provider", "none")}')
    click.echo(
        f'Default vector DB provider: {status.get("default_vector_provider", "none")}'
    )


@cli.command()
@click.option(
    '--provider-type', type=click.Choice(['llm', 'vector', 'all']), default='all'
)
@click.pass_context
def list_providers(ctx: click.Context, provider_type: str) -> None:
    """List available providers."""
    config_manager = ctx.obj['config_manager']

    if provider_type in ['llm', 'all']:
        llm_providers = config_manager.get_available_llm_providers()
        click.echo('Available LLM Providers:')
        for provider in llm_providers:
            click.echo(f'  • {provider}')

    if provider_type in ['vector', 'all']:
        vector_providers = config_manager.get_available_vector_providers()
        click.echo('Available Vector DB Providers:')
        for provider in vector_providers:
            click.echo(f'  • {provider}')


@cli.command()
@click.option('--provider', '-p', help='Vector database provider')
@click.pass_context
def list_collections(ctx: click.Context, provider: Optional[str]) -> None:
    """List all collections in vector database."""

    async def _list_collections():
        try:
            config_manager: ConfigManager = ctx.obj['config_manager']

            provider_name = provider or config_manager.config.default_vector_provider

            from src.providers.base import ProviderFactory

            factory = ProviderFactory(config_manager)
            vector_provider = await factory.create_vector_provider(provider_name)

            if hasattr(vector_provider, 'list_collections'):
                collections = await vector_provider.list_collections()

                if collections:
                    click.echo(f'Collections in {provider_name}:')
                    for collection in collections:
                        try:
                            info = await vector_provider.get_collection_info(collection)
                            count = info.get('count', 0)
                            click.echo(f'  • {collection} ({count} vectors)')
                        except Exception:
                            click.echo(f'  • {collection}')
                else:
                    click.echo(f'No collections found in {provider_name}')
            else:
                click.echo(
                    f'Provider {provider_name} does not support listing collections'
                )

            await vector_provider.cleanup()

        except Exception as e:
            logger.error(f'Failed to list collections: {e}')
            raise click.ClickException(f'Error: {e}')

    import asyncio

    asyncio.run(_list_collections())


@cli.command()
@click.argument('collection_name')
@click.option('--provider', '-p', help='Vector database provider')
@click.pass_context
def collection_info(
    ctx: click.Context, collection_name: str, provider: Optional[str]
) -> None:
    """Get information about a collection."""

    async def _collection_info():
        try:
            config_manager: ConfigManager = ctx.obj['config_manager']

            provider_name = provider or config_manager.config.default_vector_provider

            from src.providers.base import ProviderFactory

            factory = ProviderFactory(config_manager)
            vector_provider = await factory.create_vector_provider(provider_name)

            info = await vector_provider.get_collection_info(collection_name)

            click.echo(f'Collection: {collection_name}')
            click.echo(f'Provider: {provider_name}')
            click.echo(f'Vector count: {info.get("count", 0)}')
            click.echo(f'Dimension: {info.get("dimension", "N/A")}')

            await vector_provider.cleanup()

        except Exception as e:
            logger.error(f'Failed to get collection info: {e}')
            raise click.ClickException(f'Error: {e}')

    import asyncio

    asyncio.run(_collection_info())


def main() -> None:
    """Main entry point for CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        logger.info('Application interrupted by user')
    except Exception as e:
        logger.error(f'Unexpected error: {e}')
        raise


if __name__ == '__main__':
    main()
