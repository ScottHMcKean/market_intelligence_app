"""Market Intelligence Streamlit App with OSC Branding."""

import streamlit as st
from typing import Optional
import time

from src.config import (
    DatabricksConfig,
    DatabaseConfig,
    AppConfig,
    OSC_COLORS,
    OSC_FONTS,
)
from src.databricks_client import (
    get_workspace_client,
    call_endpoint,
    call_endpoint_async,
    check_query_status,
    get_user_info,
    format_response,
)
from src.database import (
    init_database,
    create_conversation,
    add_message,
    update_message,
    get_conversation_messages,
    get_message_by_query_id,
    get_user_conversations,
)


# Note: Page config will be set in main() after loading app_config


def apply_osc_branding():
    """Apply Ontario Securities Commission branding."""
    st.markdown(
        f"""
        <style>
        /* Main color scheme */
        :root {{
            --primary-color: {OSC_COLORS['primary']};
            --secondary-color: {OSC_COLORS['secondary']};
            --background-color: {OSC_COLORS['background']};
            --text-color: {OSC_COLORS['text']};
        }}
        
        /* Header styling */
        .main-header {{
            background-color: {OSC_COLORS['primary']};
            color: {OSC_COLORS['white']};
            padding: 1.5rem;
            border-radius: 0.5rem;
            margin-bottom: 2rem;
            font-family: {OSC_FONTS['primary']};
        }}
        
        .main-header h1 {{
            color: {OSC_COLORS['white']};
            margin: 0;
            font-size: 2rem;
        }}
        
        .main-header p {{
            color: {OSC_COLORS['white']};
            margin: 0.5rem 0 0 0;
            opacity: 0.9;
        }}
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {{
            background-color: {OSC_COLORS['background']};
        }}
        
        /* Button styling */
        .stButton>button {{
            background-color: {OSC_COLORS['primary']};
            color: {OSC_COLORS['white']};
            border: none;
            border-radius: 0.25rem;
            padding: 0.5rem 1rem;
            font-family: {OSC_FONTS['primary']};
            font-weight: 500;
        }}
        
        .stButton>button:hover {{
            background-color: {OSC_COLORS['secondary']};
        }}
        
        /* Chat message styling */
        .chat-message {{
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
            font-family: {OSC_FONTS['primary']};
        }}
        
        .user-message {{
            background-color: {OSC_COLORS['secondary']};
            color: {OSC_COLORS['white']};
            margin-left: 2rem;
        }}
        
        .assistant-message {{
            background-color: {OSC_COLORS['white']};
            color: {OSC_COLORS['text']};
            border: 1px solid {OSC_COLORS['primary']};
            margin-right: 2rem;
        }}
        
        /* Input styling */
        .stTextInput>div>div>input {{
            border-color: {OSC_COLORS['primary']};
        }}
        
        /* Status indicators */
        .status-pending {{
            color: {OSC_COLORS['accent']};
        }}
        
        .status-complete {{
            color: #28A745;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def initialize_session_state():
    """Initialize Streamlit session state."""
    if "initialized" not in st.session_state:
        st.session_state.initialized = True
        st.session_state.client = None
        st.session_state.user_info = None
        st.session_state.conversation_id = None
        st.session_state.messages = []
        st.session_state.db_enabled = False


def check_database_connection(db_config: DatabaseConfig) -> bool:
    """Check if database connection is available."""
    if not db_config.host or not db_config.user:
        return False

    try:
        from src.database import get_connection

        with get_connection(db_config):
            return True
    except Exception as e:
        st.warning(f"Database connection not available: {e}")
        return False


def render_header(user_info: Optional[dict]):
    """Render the application header."""
    st.markdown(
        f"""
        <div class="main-header">
            <h1>📊 OSC Market Intelligence</h1>
            <p>Ontario Securities Commission - AI-Powered Market Analysis</p>
            {f"<p style='font-size: 0.9rem;'>Logged in as: {user_info['display_name']}</p>" if user_info else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_message(role: str, content: str, status: Optional[str] = None):
    """Render a chat message."""
    css_class = "user-message" if role == "user" else "assistant-message"
    status_indicator = ""

    if status == "pending":
        status_indicator = '<span class="status-pending">⏳ Processing...</span><br>'
    elif status == "complete":
        status_indicator = '<span class="status-complete">✓ Complete</span><br>'

    st.markdown(
        f"""
        <div class="chat-message {css_class}">
            {status_indicator}
            <strong>{"You" if role == "user" else "Assistant"}:</strong><br>
            {content}
        </div>
        """,
        unsafe_allow_html=True,
    )


def main():
    """Main application."""
    # Load configurations first
    app_config = AppConfig.from_config()
    db_config = DatabaseConfig.from_config()
    databricks_config = DatabricksConfig.from_config()

    # Set page config using app config
    st.set_page_config(
        page_title=app_config.title,
        page_icon="📊",
        layout=app_config.layout,
        initial_sidebar_state="expanded",
    )

    # Apply branding
    apply_osc_branding()

    # Initialize session state
    initialize_session_state()

    # Initialize Databricks client
    try:
        if st.session_state.client is None:
            st.session_state.client = get_workspace_client()
            st.session_state.user_info = get_user_info(st.session_state.client)
    except Exception as e:
        st.error(f"Failed to authenticate with Databricks: {e}")
        st.info("Please ensure your Databricks credentials are configured correctly.")
        st.stop()

    # Check database connection
    if not st.session_state.db_enabled:
        st.session_state.db_enabled = check_database_connection(db_config)
        if st.session_state.db_enabled:
            init_database(db_config)

    # Render header
    render_header(st.session_state.user_info)

    # Sidebar
    with st.sidebar:
        st.header("Settings")

        # Conversation management
        if st.session_state.db_enabled:
            st.subheader("Conversations")

            if st.button("➕ New Conversation"):
                st.session_state.conversation_id = create_conversation(
                    db_config, st.session_state.user_info["user_id"]
                )
                st.session_state.messages = []
                st.rerun()

            # Load existing conversations
            if st.session_state.conversation_id:
                st.info(f"Conversation ID: {st.session_state.conversation_id}")

                if st.button("🔄 Refresh Messages"):
                    messages = get_conversation_messages(
                        db_config, st.session_state.conversation_id
                    )
                    st.session_state.messages = messages
                    st.rerun()
        else:
            st.warning("Database not configured. Conversation history disabled.")

        st.divider()

        # Query options
        st.subheader("Query Options")
        use_async = st.checkbox(
            "Enable async mode for long queries", value=app_config.async_queries_enabled
        )

        st.divider()

        # About
        st.subheader("About")
        st.markdown(
            """
            This application provides AI-powered market intelligence 
            analysis powered by Databricks.
            
            **Features:**
            - 🔐 Secure Databricks authentication
            - 💬 Conversation history
            - ⚡ Async query support
            - 📊 Market intelligence insights
            """
        )

    # Main chat interface
    st.header("Ask a Question")

    # Display existing messages
    if st.session_state.db_enabled and st.session_state.conversation_id:
        if not st.session_state.messages:
            st.session_state.messages = get_conversation_messages(
                db_config, st.session_state.conversation_id
            )

    for msg in st.session_state.messages:
        render_message("user", msg["question"])
        if msg["answer"]:
            render_message("assistant", msg["answer"], msg.get("status"))
        elif msg.get("status") == "pending":
            render_message("assistant", "Processing your query...", "pending")

    # Input form
    with st.form(key="question_form", clear_on_submit=True):
        user_question = st.text_area(
            "Enter your question:",
            placeholder="e.g., What are the latest market trends in Canadian securities?",
            height=100,
        )
        submit_button = st.form_submit_button(
            "Submit Question", use_container_width=True
        )

    if submit_button and user_question:
        # Create conversation if needed
        if st.session_state.db_enabled and not st.session_state.conversation_id:
            st.session_state.conversation_id = create_conversation(
                db_config, st.session_state.user_info["user_id"]
            )

        # Add message to UI
        render_message("user", user_question)

        # Process question
        with st.spinner("Processing your question..."):
            try:
                if use_async:
                    # Async query
                    query_id = call_endpoint_async(
                        databricks_config,
                        user_question,
                    )

                    # Save to database
                    if st.session_state.db_enabled:
                        message_id = add_message(
                            db_config,
                            st.session_state.conversation_id,
                            st.session_state.user_info["user_id"],
                            user_question,
                            status="pending",
                            query_id=query_id,
                        )

                    render_message(
                        "assistant",
                        f"Query submitted (ID: {query_id}). Check back later for results.",
                        "pending",
                    )
                    st.info(
                        "Your query is being processed. Use the 'Refresh Messages' button to check for updates."
                    )

                else:
                    # Synchronous query
                    response = call_endpoint(
                        databricks_config,
                        user_question,
                    )

                    answer = format_response(response)

                    # Save to database
                    if st.session_state.db_enabled:
                        message_id = add_message(
                            db_config,
                            st.session_state.conversation_id,
                            st.session_state.user_info["user_id"],
                            user_question,
                            answer=answer,
                            status="complete",
                        )

                    render_message("assistant", answer, "complete")

                # Reload messages
                if st.session_state.db_enabled and st.session_state.conversation_id:
                    st.session_state.messages = get_conversation_messages(
                        db_config, st.session_state.conversation_id
                    )

                st.rerun()

            except Exception as e:
                st.error(f"Error processing question: {e}")
                st.info("Please check your configuration and try again.")


if __name__ == "__main__":
    main()
