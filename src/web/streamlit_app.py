"""
Streamlit frontend for RAG_07.
Provides interactive web interface for RAG operations and model management.
"""

import json
import time
from typing import Dict, List, Optional

import requests
import streamlit as st

# Configuration
API_BASE_URL = "http://localhost:8000"


class RAGAPIClient:
    """Client for RAG_07 FastAPI backend."""

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url

    def health_check(self) -> Optional[Dict]:
        """Check API health status."""
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException:
            return None

    def get_available_models(self) -> Optional[Dict]:
        """Get available models from API."""
        try:
            response = requests.get(f"{self.base_url}/api/models", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException:
            return None

    def simple_query(
        self,
        query: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Optional[Dict]:
        """Send simple query to API."""
        try:
            payload = {"query": query}
            if provider:
                payload["provider"] = provider
            if model:
                payload["model"] = model

            response = requests.post(
                f"{self.base_url}/api/query/simple",
                json=payload,
                timeout=60,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {e}")
            return None

    def rag_query(
        self,
        question: str,
        llm_provider: Optional[str] = None,
        llm_model: Optional[str] = None,
        vector_provider: Optional[str] = None,
        collection: str = "default",
        max_results: int = 5,
        use_function_calling: bool = True,
        max_iterations: int = 5,
    ) -> Optional[Dict]:
        """Send RAG query to API."""
        try:
            payload = {
                "question": question,
                "collection": collection,
                "max_results": max_results,
                "use_function_calling": use_function_calling,
                "max_iterations": max_iterations,
            }
            if llm_provider:
                payload["llm_provider"] = llm_provider
            if llm_model:
                payload["llm_model"] = llm_model
            if vector_provider:
                payload["vector_provider"] = vector_provider

            response = requests.post(
                f"{self.base_url}/api/query/rag",
                json=payload,
                timeout=120,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {e}")
            return None

    def add_text(
        self,
        text: str,
        provider: Optional[str] = None,
        collection: str = "default",
    ) -> Optional[Dict]:
        """Add text to vector database."""
        try:
            payload = {"text": text, "collection": collection}
            if provider:
                payload["provider"] = provider

            response = requests.post(
                f"{self.base_url}/api/vectors/add",
                json=payload,
                timeout=60,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {e}")
            return None

    def search_vectors(
        self,
        query: str,
        provider: Optional[str] = None,
        collection: str = "default",
        limit: int = 5,
    ) -> Optional[Dict]:
        """Search in vector database."""
        try:
            payload = {
                "query": query,
                "collection": collection,
                "limit": limit,
            }
            if provider:
                payload["provider"] = provider

            response = requests.post(
                f"{self.base_url}/api/vectors/search",
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {e}")
            return None


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if "api_client" not in st.session_state:
        st.session_state.api_client = RAGAPIClient()

    if "query_count" not in st.session_state:
        st.session_state.query_count = 0

    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []


def render_sidebar():
    """Render sidebar with configuration and status."""
    with st.sidebar:
        st.header("⚙️ Configuration")

        # API Health Check
        api_client = st.session_state.api_client
        health = api_client.health_check()

        if health:
            st.success("✅ API Connected")
            if "providers_status" in health:
                st.write("**Default Providers:**")
                for key, value in health["providers_status"].items():
                    st.write(f"- {key}: `{value}`")
        else:
            st.error("❌ API Unavailable")
            st.error(f"Make sure the API is running at {API_BASE_URL}")
            st.stop()

        st.markdown("---")

        # Model Selection
        st.subheader("🤖 Model Selection")
        models_data = api_client.get_available_models()

        if models_data and "providers" in models_data:
            providers = models_data["providers"]

            # LLM Provider selection
            llm_providers = list(providers.keys())
            selected_llm = st.selectbox(
                "LLM Provider:",
                options=["auto"] + llm_providers,
                help="Choose LLM provider or 'auto' for default",
            )

            # Model selection based on provider
            selected_model = None
            if selected_llm != "auto" and selected_llm in providers:
                available_models = providers[selected_llm]
                if available_models:
                    selected_model = st.selectbox(
                        f"Model for {selected_llm}:",
                        options=["auto"] + available_models,
                        help=f"Choose specific model for {selected_llm}",
                    )
                    if selected_model == "auto":
                        selected_model = None

            # Vector Provider selection
            vector_providers = ["faiss", "chroma"]
            selected_vector = st.selectbox(
                "Vector Provider:",
                options=["auto"] + vector_providers,
                help="Choose vector DB provider or 'auto' for default",
            )

            # Collection selection
            collection = st.text_input(
                "Collection:", value="default", help="Vector database collection"
            )

            # Advanced settings
            with st.expander("🔧 Advanced Settings"):
                max_results = st.slider("Max Context Results:", 1, 20, 5)
                use_function_calling = st.checkbox("Use Function Calling", value=True)
                max_iterations = st.slider("Max Iterations:", 1, 10, 5)

                # Model-specific settings
                if selected_llm != "auto":
                    st.markdown("**Model Settings:**")
                    temperature = st.slider("Temperature:", 0.0, 2.0, 0.7, 0.1)
                    max_tokens = st.number_input(
                        "Max Tokens:", min_value=1, max_value=4000, value=1000
                    )
                else:
                    temperature = 0.7
                    max_tokens = 1000

        else:
            st.error("Failed to load models")
            selected_llm = "auto"
            selected_vector = "auto"
            collection = "default"
            max_results = 5
            use_function_calling = True
            max_iterations = 5

        st.markdown("---")

        # Statistics
        st.subheader("📊 Session Statistics")
        st.metric("Queries in Session", st.session_state.query_count)
        st.metric("Conversation History", len(st.session_state.conversation_history))

        return {
            "llm_provider": selected_llm if selected_llm != "auto" else None,
            "selected_model": selected_model,
            "vector_provider": selected_vector if selected_vector != "auto" else None,
            "collection": collection,
            "max_results": max_results,
            "use_function_calling": use_function_calling,
            "max_iterations": max_iterations,
            "temperature": temperature if 'temperature' in locals() else 0.7,
            "max_tokens": max_tokens if 'max_tokens' in locals() else 1000,
        }


def render_main_interface(config: Dict):
    """Render main interface."""
    st.title("🤖 RAG_07 - Intelligent Document Assistant")
    st.markdown("---")

    # Tab selection
    tab1, tab2, tab3 = st.tabs(["💬 Chat", "🔍 Vector Search", "📁 Add Documents"])

    with tab1:
        render_chat_tab(config)

    with tab2:
        render_vector_search_tab(config)

    with tab3:
        render_add_documents_tab(config)


def render_chat_tab(config: Dict):
    """Render chat interface."""
    st.header("💬 Ask Questions")

    # Example questions
    st.markdown("**Example Questions:**")
    example_questions = [
        "What are the main features of RAG_07?",
        "How does the system architecture work?",
        "What LLM models are supported?",
        "How to configure vector databases?",
    ]

    cols = st.columns(2)
    for i, example in enumerate(example_questions):
        with cols[i % 2]:
            if st.button(example, key=f"example_{i}"):
                process_question(example, config)

    # Question input
    question = st.text_area(
        "Your Question:",
        height=100,
        placeholder="e.g., What are the main functions of RAG_07?",
        key="question_input",
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("🚀 Send Question", type="primary", use_container_width=True):
            if question.strip():
                process_question(question, config)
            else:
                st.warning("Please enter a question!")

    with col2:
        query_type = st.selectbox("Query Type:", ["RAG", "Simple"])

    # Display conversation history
    if st.session_state.conversation_history:
        st.markdown("---")
        st.subheader("📝 Conversation History")

        for i, entry in enumerate(reversed(st.session_state.conversation_history)):
            with st.expander(
                f"Q{len(st.session_state.conversation_history) - i}: {entry['question'][:50]}..."
            ):
                st.markdown(f"**Question:** {entry['question']}")
                st.markdown(f"**Answer:** {entry['answer']}")

                if entry.get("sources_used"):
                    st.markdown("**Sources Used:**")
                    for j, source in enumerate(entry["sources_used"], 1):
                        st.markdown(f"{j}. {source}")

                if entry.get("function_calls"):
                    st.markdown("**Function Calls:**")
                    st.json(entry["function_calls"])

                # Export option
                export_data = {
                    "question": entry["question"],
                    "answer": entry["answer"],
                    "sources": entry.get("sources_used", []),
                    "timestamp": entry.get("timestamp", ""),
                }
                st.download_button(
                    "📥 Export",
                    json.dumps(export_data, indent=2, ensure_ascii=False),
                    file_name=f"rag_response_{i}.json",
                    mime="application/json",
                    key=f"export_{i}",
                )


def process_question(question: str, config: Dict):
    """Process a question and display results."""
    api_client = st.session_state.api_client

    with st.spinner("🔍 Processing your question..."):
        if config.get("query_type", "RAG") == "RAG":
            result = api_client.rag_query(
                question=question,
                llm_provider=config["llm_provider"],
                llm_model=config["selected_model"],
                vector_provider=config["vector_provider"],
                collection=config["collection"],
                max_results=config["max_results"],
                use_function_calling=config["use_function_calling"],
                max_iterations=config["max_iterations"],
            )
        else:
            result = api_client.simple_query(
                query=question,
                provider=config["llm_provider"],
                model=config["selected_model"],
            )

        if result:
            st.session_state.query_count += 1

            # Add to conversation history
            history_entry = {
                "question": question,
                "answer": result.get("answer", result.get("result", "")),
                "sources_used": result.get("sources_used", []),
                "function_calls": result.get("function_calls", []),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "processing_time": result.get("processing_time", 0),
            }
            st.session_state.conversation_history.append(history_entry)

            # Display result
            st.success("✅ Question processed successfully!")
            st.markdown(f"**Answer:** {history_entry['answer']}")

            if history_entry["sources_used"]:
                st.markdown("**Sources Used:**")
                for i, source in enumerate(history_entry["sources_used"], 1):
                    st.markdown(f"{i}. {source}")

            st.info(f"⏱️ Processing time: {history_entry['processing_time']:.2f}s")


def render_vector_search_tab(config: Dict):
    """Render vector search interface."""
    st.header("🔍 Vector Database Search")

    search_query = st.text_input("Search Query:", placeholder="Enter search terms...")

    col1, col2 = st.columns([2, 1])
    with col1:
        limit = st.slider("Max Results:", 1, 20, 5)
    with col2:
        if st.button("🔍 Search", type="primary"):
            if search_query.strip():
                api_client = st.session_state.api_client
                with st.spinner("Searching vector database..."):
                    result = api_client.search_vectors(
                        query=search_query,
                        provider=config["vector_provider"],
                        collection=config["collection"],
                        limit=limit,
                    )

                    if result:
                        st.success(f"Found {len(result['results'])} results")
                        for i, text in enumerate(result["results"], 1):
                            st.markdown(f"**Result {i}:**")
                            st.text(text)
                            st.markdown("---")
            else:
                st.warning("Please enter a search query!")


def render_add_documents_tab(config: Dict):
    """Render document addition interface."""
    st.header("📁 Add Documents to Vector Database")

    # Text input
    text_input = st.text_area(
        "Text to Add:",
        height=200,
        placeholder="Paste or type the text you want to add to the vector database...",
    )

    # File upload
    uploaded_file = st.file_uploader(
        "Or Upload Text File:", type=["txt", "md", "py", "json"]
    )

    if uploaded_file is not None:
        text_content = uploaded_file.read().decode("utf-8")
        st.text_area("File Content:", value=text_content, height=200, disabled=True)
        text_to_add = text_content
    else:
        text_to_add = text_input

    if st.button("📤 Add to Vector Database", type="primary"):
        if text_to_add.strip():
            api_client = st.session_state.api_client
            with st.spinner("Adding text to vector database..."):
                result = api_client.add_text(
                    text=text_to_add,
                    provider=config["vector_provider"],
                    collection=config["collection"],
                )

                if result:
                    st.success(
                        f"✅ Text added successfully! Document ID: {result['document_id']}"
                    )
                    st.info(f"Collection: {result['collection']}")
                    st.info(f"Processing time: {result['processing_time']:.2f}s")
        else:
            st.warning("Please enter text to add!")


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="RAG_07 Dashboard",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Initialize session state
    initialize_session_state()

    # Render sidebar and get configuration
    config = render_sidebar()

    # Render main interface
    render_main_interface(config)

    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col2:
        st.markdown(
            "<div style='text-align: center; color: #666;'>"
            f"RAG_07 v1.0.0 | Generated on {time.strftime('%Y-%m-%d %H:%M:%S')}"
            "</div>",
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()
