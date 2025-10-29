"""Market Intelligence Streamlit App with OSC Branding."""

import os
import streamlit as st
from typing import Optional
from datetime import datetime

# Set MLflow tracking URI before any other imports
if "MLFLOW_TRACKING_URI" not in os.environ:
    os.environ["MLFLOW_TRACKING_URI"] = "databricks://aws"

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
    get_user_info,
    format_response,
)
from src.database import (
    init_database,
    create_conversation,
    add_message,
    get_conversation_messages,
    get_connection,
    update_conversation_trace,
)


# Note: Page config will be set in main() after loading app_config


def apply_osc_branding():
    """Apply Ontario Securities Commission branding."""
    st.markdown(
        f"""
        <style>
        /* Import Open Sans font */
        @import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700&display=swap');
        
        /* Main color scheme */
        :root {{
            --primary-color: {OSC_COLORS['primary']};
            --secondary-color: {OSC_COLORS['secondary']};
            --background-color: {OSC_COLORS['background']};
            --text-color: {OSC_COLORS['text']};
        }}
        
        /* Global font */
        html, body, [class*="css"] {{
            font-family: {OSC_FONTS['primary']};
            font-size: 14px;
        }}
        
        /* Reduce sidebar font size */
        [data-testid="stSidebar"] {{
            font-size: 13px;
        }}
        
        /* Header styling with logo */
        .main-header {{
            background-color: {OSC_COLORS['primary']};
            color: {OSC_COLORS['white']};
            padding: 1rem 2rem;
            border-radius: 0;
            margin-bottom: 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .main-header h1 {{
            color: {OSC_COLORS['white']};
            margin: 0;
            font-size: 1.8rem;
            font-weight: 600;
        }}
        
        .welcome-user {{
            color: {OSC_COLORS['white']};
            font-size: 0.85rem;
            margin-top: 0.25rem;
            opacity: 0.9;
        }}
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {{
            background-color: {OSC_COLORS['white']};
            border-right: 1px solid {OSC_COLORS['border']};
        }}
        
        [data-testid="stSidebar"] h2 {{
            color: {OSC_COLORS['primary']};
            font-weight: 600;
            font-size: 1.1rem;
            margin-top: 1rem;
        }}
        
        [data-testid="stSidebar"] h3 {{
            color: {OSC_COLORS['text']};
            font-size: 0.9rem;
            font-weight: 600;
            margin-top: 1rem;
            margin-bottom: 0.5rem;
        }}
        
        [data-testid="stSidebar"] .element-container {{
            margin-bottom: 0.5rem;
        }}
        
        /* Button styling */
        .stButton>button {{
            background-color: {OSC_COLORS['primary']} !important;
            color: {OSC_COLORS['white']} !important;
            border: none !important;
            border-radius: 0.25rem;
            padding: 0.5rem 1.5rem;
            font-family: {OSC_FONTS['primary']};
            font-weight: 600;
            transition: all 0.3s ease;
        }}
        
        .stButton>button:hover {{
            background-color: {OSC_COLORS['secondary']} !important;
            transform: translateY(-1px);
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        /* Chat message styling */
        .chat-message {{
            padding: 1rem;
            border-radius: 4px;
            margin-bottom: 1rem;
            font-family: {OSC_FONTS['primary']};
            font-size: 14px;
            line-height: 1.6;
        }}
        
        .user-message {{
            background-color: {OSC_COLORS['background']};
            color: {OSC_COLORS['text']};
            border-left: 3px solid {OSC_COLORS['primary']};
        }}
        
        .assistant-message {{
            background-color: {OSC_COLORS['white']};
            color: {OSC_COLORS['text']};
            border: 1px solid {OSC_COLORS['border']};
        }}
        
        .message-label {{
            font-weight: 600;
            color: {OSC_COLORS['primary']};
            margin-bottom: 0.5rem;
            font-size: 13px;
        }}
        
        /* Input styling */
        .stTextInput>div>div>input, .stTextArea>div>div>textarea {{
            border-color: {OSC_COLORS['primary']};
            font-family: {OSC_FONTS['primary']};
        }}
        
        /* Status indicators */
        .status-pending {{
            color: {OSC_COLORS['accent']};
            font-weight: 600;
        }}
        
        .status-complete {{
            color: #28A745;
            font-weight: 600;
        }}
        
        /* Conversation history item */
        .conversation-item {{
            padding: 0.8rem;
            margin: 0.5rem 0;
            border-radius: 0.25rem;
            border: 1px solid {OSC_COLORS['border']};
            background-color: {OSC_COLORS['white']};
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        
        .conversation-item:hover {{
            border-color: {OSC_COLORS['primary']};
            background-color: {OSC_COLORS['background']};
        }}
        
        .conversation-item.active {{
            border-color: {OSC_COLORS['primary']};
            background-color: {OSC_COLORS['primary']};
            color: {OSC_COLORS['white']};
        }}
        
        /* OSC Logo styling */
        .osc-logo {{
            max-width: 150px;
            margin-bottom: 1rem;
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
        st.session_state.conversations_cache = None
        st.session_state.conversations_last_fetch = None


def check_database_connection(db_config: DatabaseConfig) -> bool:
    """Check if database connection is available."""
    if not db_config.instance_name:
        return False

    try:
        from src.database import get_connection

        with get_connection(db_config):
            return True
    except Exception as e:
        st.warning(f"Database connection not available: {e}")
        return False


def render_header(user_info: Optional[dict]):
    """Render the application header with OSC branding."""
    display_name = user_info.get("display_name", "User") if user_info else "User"

    st.markdown(
        f"""
        <div class="main-header" style="padding: 1rem 2rem;">
            <h1 style="margin-bottom: 0.25rem;">Market Surveillance Analyst</h1>
            <div class="welcome-user" style="margin-top: 0.25rem;">Welcome, {display_name}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_message(role: str, content: str, status: Optional[str] = None):
    """Render a chat message with clean styling."""
    if role == "user":
        # User messages - right-aligned with light background
        st.markdown(
            f"""
            <div style="
                background-color: #F0F7FA;
                border-left: 3px solid #2e6378;
                padding: 1rem;
                margin: 0.5rem 0;
                border-radius: 0.5rem;
            ">
                <div style="font-weight: 600; color: #2e6378; margin-bottom: 0.5rem; font-size: 0.9rem;">You</div>
                <div style="color: #333; line-height: 1.6;">{content}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        # Assistant messages - left-aligned with white background
        status_indicator = ""
        if status == "pending":
            status_indicator = '<div style="color: #E31837; font-size: 0.85rem; margin-bottom: 0.5rem;">● Processing...</div>'
        elif status == "complete":
            status_indicator = '<div style="color: #28A745; font-size: 0.85rem; margin-bottom: 0.5rem;">✓ Complete</div>'

        st.markdown(
            f"""
            <div style="
                background-color: #FFFFFF;
                border-left: 3px solid #2A7DE1;
                padding: 1rem;
                margin: 0.5rem 0;
                border-radius: 0.5rem;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            ">
                {status_indicator}
                <div style="font-weight: 600; color: #2A7DE1; margin-bottom: 0.5rem; font-size: 0.9rem;">Assistant</div>
                <div style="color: #333; line-height: 1.6; white-space: pre-wrap;">{content}</div>
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
        page_icon="https://www.databricks.com/favicon.ico",
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
        # OSC Logo at top
        st.image("Ontario_Securities_Commission_logo.svg.png", width=200)

        st.markdown(
            f"""
            <div style="border-bottom: 2px solid {OSC_COLORS['primary']}; margin: 1rem 0 1.5rem 0;"></div>
            """,
            unsafe_allow_html=True,
        )

        # Conversation management
        if st.session_state.db_enabled:

            if st.button("New Conversation", use_container_width=True):
                st.session_state.conversation_id = create_conversation(
                    db_config, st.session_state.user_info["user_id"]
                )
                st.session_state.messages = []
                st.session_state.conversations_cache = None  # Invalidate cache
                st.rerun()

            # Display conversation history
            st.markdown(
                f"""<div style="color: {OSC_COLORS['text']}; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin: 1rem 0 0.5rem 0; opacity: 0.7;">Your Conversations</div>""",
                unsafe_allow_html=True,
            )
            try:
                import time

                # Cache conversations for 5 seconds to reduce DB queries
                current_time = time.time()
                if (
                    st.session_state.conversations_cache is None
                    or st.session_state.conversations_last_fetch is None
                    or (current_time - st.session_state.conversations_last_fetch) > 5
                ):
                    with get_connection(db_config) as conn:
                        cursor = conn.cursor()

                        user_id = st.session_state.user_info["user_id"]

                        cursor.execute(
                            """
                            SELECT 
                                c.id,
                                c.created_at,
                                COUNT(m.id) as message_count,
                                MAX(m.created_at) as last_message_at
                            FROM conversations c
                            LEFT JOIN messages m ON c.id = m.conversation_id
                            WHERE c.user_id = %s
                            GROUP BY c.id, c.created_at
                            ORDER BY MAX(COALESCE(m.created_at, c.created_at)) DESC
                            LIMIT 5
                            """,
                            (user_id,),
                        )

                        st.session_state.conversations_cache = cursor.fetchall()
                        st.session_state.conversations_last_fetch = current_time
                        cursor.close()

                conversations = st.session_state.conversations_cache

                if conversations:
                    for conv in conversations:
                        conv_id, created_at, msg_count, last_msg = conv
                        is_active = conv_id == st.session_state.conversation_id

                        # Format the date
                        date_str = created_at.strftime("%b %d, %Y %H:%M")

                        # Create button for each conversation
                        button_label = f"{date_str} ({msg_count} msgs)"
                        if is_active:
                            button_label = f"● {button_label}"

                        if st.button(button_label, key=f"conv_{conv_id}", use_container_width=True):
                            st.session_state.conversation_id = conv_id
                            st.session_state.messages = get_conversation_messages(
                                db_config, conv_id
                            )
                            st.rerun()
                else:
                    st.info("No conversations yet. Start a new one!")

            except Exception as e:
                st.warning(f"Could not load conversation history: {e}")

            if st.session_state.conversation_id:
                st.divider()

                # Get conversation trace ID from database
                try:
                    with get_connection(db_config) as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "SELECT mlflow_trace_id FROM conversations WHERE id = %s",
                            (st.session_state.conversation_id,),
                        )
                        result = cursor.fetchone()
                        conv_trace_id = result[0] if result and result[0] else None
                        cursor.close()

                    st.caption(f"**Conversation ID:** #{st.session_state.conversation_id}")
                    if conv_trace_id:
                        # Format trace ID nicely
                        trace_short = (
                            conv_trace_id[:20] + "..." if len(conv_trace_id) > 20 else conv_trace_id
                        )
                        st.caption(f"**Trace ID:** {trace_short}")
                except Exception as e:
                    st.caption(f"**Conversation ID:** #{st.session_state.conversation_id}")

                if st.button("Refresh Messages", use_container_width=True):
                    messages = get_conversation_messages(
                        db_config, st.session_state.conversation_id
                    )
                    st.session_state.messages = messages
                    st.rerun()
        else:
            st.info("Enable database to track conversation history")

        st.divider()

        # About section with Databricks branding
        st.markdown(
            """
            <div style="text-align: center; padding: 0.5rem 0;">
                <p style="font-size: 0.85rem; color: #666; margin-bottom: 1rem;">AI-powered market intelligence</p>
                <p style="font-size: 0.75rem; color: #666; margin-bottom: 0.5rem;">Powered by</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.image("primary-lockup-full-color-rgb-4000x634.png", width="stretch")

    # Main chat interface
    # Display existing messages
    if st.session_state.db_enabled and st.session_state.conversation_id:
        if not st.session_state.messages:
            st.session_state.messages = get_conversation_messages(
                db_config, st.session_state.conversation_id
            )

    for msg in st.session_state.messages:
        with st.chat_message("user"):
            st.write(msg["question"])
        if msg["answer"]:
            with st.chat_message("assistant"):
                st.write(msg["answer"])
        elif msg.get("status") == "pending":
            with st.chat_message("assistant"):
                st.write("Processing your query...")

    # Input form - show above feedback for easy follow-up questions
    with st.form(key="question_form", clear_on_submit=True):
        user_question = st.text_area(
            "Enter your question:",
            placeholder="e.g., What are the latest market trends in Canadian securities?",
            height=100,
        )
        submit_button = st.form_submit_button("Submit Question", use_container_width=True)

    # PDF Download buttons
    if st.session_state.messages and len(st.session_state.messages) > 0:
        st.markdown("---")
        col_pdf1, col_pdf2 = st.columns(2)

        with col_pdf1:
            if st.button("📄 Download Latest Message as Report", use_container_width=True):
                from src.pdf_generator import create_pdf_report

                last_msg = st.session_state.messages[-1]
                user_name = (
                    st.session_state.user_info.get("display_name", "Unknown User")
                    if st.session_state.user_info
                    else "Unknown User"
                )

                # Get conversation trace ID from database
                conv_trace_id = None
                try:
                    with get_connection(db_config) as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "SELECT mlflow_trace_id FROM conversations WHERE id = %s",
                            (st.session_state.conversation_id,),
                        )
                        result = cursor.fetchone()
                        conv_trace_id = (
                            result[0] if result and result[0] else last_msg.get("trace_id")
                        )
                        cursor.close()
                except:
                    conv_trace_id = last_msg.get("trace_id")

                pdf_buffer = create_pdf_report(
                    title="Market Surveillance Analyst",
                    conversation_id=st.session_state.conversation_id,
                    trace_id=conv_trace_id,
                    messages=[last_msg],
                    user_name=user_name,
                    report_type="latest",
                )

                st.download_button(
                    label="💾 Save PDF",
                    data=pdf_buffer,
                    file_name=f"market_intelligence_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

        with col_pdf2:
            if st.button("📑 Download Conversation History", use_container_width=True):
                from src.pdf_generator import create_pdf_report

                user_name = (
                    st.session_state.user_info.get("display_name", "Unknown User")
                    if st.session_state.user_info
                    else "Unknown User"
                )

                # Get conversation trace ID from database
                conv_trace_id = None
                try:
                    with get_connection(db_config) as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "SELECT mlflow_trace_id FROM conversations WHERE id = %s",
                            (st.session_state.conversation_id,),
                        )
                        result = cursor.fetchone()
                        conv_trace_id = result[0] if result and result[0] else None
                        cursor.close()
                except:
                    pass

                pdf_buffer = create_pdf_report(
                    title="Market Surveillance Analyst - Conversation History",
                    conversation_id=st.session_state.conversation_id,
                    trace_id=conv_trace_id,
                    messages=st.session_state.messages,
                    user_name=user_name,
                    report_type="full",
                )

                st.download_button(
                    label="💾 Save PDF",
                    data=pdf_buffer,
                    file_name=f"conversation_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

    # Show feedback for the most recent message (if any)
    if st.session_state.messages and len(st.session_state.messages) > 0:
        last_msg = st.session_state.messages[-1]
        if last_msg.get("answer"):  # Only show feedback if there's an answer
            st.markdown("---")
            st.markdown(
                """
                📊 See additional information in the [Market Intelligence Dashboard](https://e2-demo-field-eng.cloud.databricks.com/dashboardsv3/01f0b015398919bba5ae041ac051000b/published?o=1444828305810485)
                """
            )

            # Add feedback section
            st.markdown("---")
            st.markdown("**Feedback**")

            # Initialize feedback state for this response
            feedback_key = (
                f"feedback_{st.session_state.conversation_id}_{len(st.session_state.messages)}"
            )
            if feedback_key not in st.session_state:
                st.session_state[feedback_key] = {
                    "satisfied": None,
                    "review_flagged": False,
                }

            col1, col2, col3 = st.columns([1, 1, 3])

            # Get trace ID - use local trace_id since agent traces aren't in MLflow experiment
            trace_id = (
                st.session_state.get("last_trace_id")
                if hasattr(st.session_state, "last_trace_id")
                else None
            )

            if trace_id:
                print(f"📋 Using trace_id for feedback: {trace_id}")

            # Check if we should try to fetch MLflow trace (only if we don't have a local one)
            mlflow_trace_id = None
            # Skip MLflow trace lookup for now - it's slow and the local trace_id works fine
            # We can enable this later if needed for production monitoring
            # if not trace_id:
            #     try:
            #         from src.mlflow_tracing import setup_mlflow, get_most_recent_trace_id
            #         setup_mlflow(databricks_config)
            #         mlflow_trace_id = get_most_recent_trace_id(databricks_config)
            #         if mlflow_trace_id:
            #             print(f"📋 Found MLflow trace: {mlflow_trace_id}")
            #             trace_id = mlflow_trace_id
            #     except Exception as e:
            #         print(f"⚠️ Could not get MLflow trace: {e}")

            with col1:
                # Thumbs up button with highlighting
                button_type = (
                    "primary"
                    if st.session_state[feedback_key]["satisfied"] == True
                    else "secondary"
                )
                if st.button(
                    "👍 Satisfied",
                    key=f"thumbs_up_{feedback_key}",
                    type=button_type,
                    use_container_width=True,
                ):
                    st.session_state[feedback_key]["satisfied"] = True
                    st.toast("Thank you for your feedback!", icon="✅")

                    if trace_id:
                        from src.mlflow_tracing import log_user_satisfaction

                        # Log to MLflow (best effort)
                        use_mlflow = True
                        log_user_satisfaction(
                            trace_id,
                            True,
                            st.session_state.user_info["user_id"],
                            message_id=last_msg.get("id"),
                            use_mlflow=use_mlflow,
                        )

            with col2:
                # Thumbs down button with highlighting
                button_type = (
                    "primary"
                    if st.session_state[feedback_key]["satisfied"] == False
                    else "secondary"
                )
                if st.button(
                    "👎 Not Satisfied",
                    key=f"thumbs_down_{feedback_key}",
                    type=button_type,
                    use_container_width=True,
                ):
                    st.session_state[feedback_key]["satisfied"] = False
                    st.toast("Thank you for your feedback!", icon="✅")

                    if trace_id:
                        from src.mlflow_tracing import log_user_satisfaction

                        # Log to MLflow (best effort)
                        use_mlflow = True
                        log_user_satisfaction(
                            trace_id,
                            False,
                            st.session_state.user_info["user_id"],
                            message_id=last_msg.get("id"),
                            use_mlflow=use_mlflow,
                        )

            with col3:
                # Review button with highlighting
                button_type = (
                    "primary" if st.session_state[feedback_key]["review_flagged"] else "secondary"
                )
                if st.button(
                    "🚩 Send for Review",
                    key=f"review_{feedback_key}",
                    type=button_type,
                    use_container_width=True,
                ):
                    st.session_state[feedback_key]["review_flagged"] = True
                    st.toast("Response flagged for review", icon="🚩")

                    if trace_id:
                        from src.mlflow_tracing import log_review_request

                        # Log to MLflow (best effort)
                        use_mlflow = True
                        log_review_request(
                            trace_id,
                            st.session_state.user_info["user_id"],
                            message_id=last_msg.get("id"),
                            use_mlflow=use_mlflow,
                        )

            # Add correction field
            correction_text = st.text_area(
                "Add a correction or expected output:",
                key=f"correction_{feedback_key}",
                placeholder="Enter what the correct response should be...",
            )

            if st.button(
                "Submit Correction",
                key=f"submit_correction_{feedback_key}",
                use_container_width=True,
            ):
                if correction_text and correction_text.strip():
                    st.toast("Correction submitted successfully", icon="📝")

                    if trace_id:
                        from src.mlflow_tracing import log_correction

                        # Log to MLflow (best effort)
                        use_mlflow = True
                        log_correction(
                            trace_id,
                            correction_text.strip(),
                            st.session_state.user_info["user_id"],
                            message_id=last_msg.get("id"),
                            use_mlflow=use_mlflow,
                        )
                else:
                    st.warning("⚠️ Please enter a correction before submitting")

    # Process question submission (form defined above)
    if submit_button and user_question:
        # Create conversation if needed
        if st.session_state.db_enabled and not st.session_state.conversation_id:
            st.session_state.conversation_id = create_conversation(
                db_config, st.session_state.user_info["user_id"]
            )

        # Add message to UI
        with st.chat_message("user"):
            st.write(user_question)

        # Get conversation history for context
        conversation_history = []
        if st.session_state.db_enabled and st.session_state.conversation_id:
            conversation_history = st.session_state.messages if st.session_state.messages else []
            print(f"📜 Loaded {len(conversation_history)} previous messages for context")

        # Process question with streaming
        try:
            # Import the streaming function
            from src.databricks_client import call_endpoint_stream

            # Show streaming indicator
            with st.chat_message("assistant"):
                # Use st.write_stream for proper streaming display, passing conversation history
                # call_endpoint_stream now returns (generator, trace_id)
                stream_generator, trace_id = call_endpoint_stream(
                    databricks_config, user_question, conversation_history=conversation_history
                )
                answer = st.write_stream(stream_generator)

                # Store trace_id in session state for feedback
                if trace_id:
                    st.session_state.last_trace_id = trace_id
                    print(f"📋 Stored local trace_id: {trace_id}")

                    # Try to get the actual MLflow trace ID from the experiment
                    try:
                        from src.mlflow_tracing import setup_mlflow, get_most_recent_trace_id

                        setup_mlflow(databricks_config)
                        mlflow_trace_id = get_most_recent_trace_id(databricks_config)
                        if mlflow_trace_id and mlflow_trace_id.startswith("tr-"):
                            trace_id = mlflow_trace_id
                            st.session_state.last_trace_id = trace_id
                            print(f"📋 Found MLflow trace_id: {trace_id}")
                    except Exception as e:
                        print(f"⚠️ Could not fetch MLflow trace ID: {e}")

        except Exception as stream_error:
            st.error(f"Streaming error: {stream_error}")
            trace_id = None
            # Fallback to non-streaming
            try:
                response = call_endpoint(
                    databricks_config, user_question, conversation_history=conversation_history
                )
                answer = format_response(response)
                with st.chat_message("assistant"):
                    st.write(answer)
            except Exception as e:
                st.error(f"Error processing question: {e}")
                st.info("Please check your configuration and try again.")
                answer = None

        # Save to database
        if st.session_state.db_enabled and answer:
            final_trace_id = trace_id if "trace_id" in locals() else None
            add_message(
                db_config,
                st.session_state.conversation_id,
                st.session_state.user_info["user_id"],
                user_question,
                answer=answer,
                status="complete",
                trace_id=final_trace_id,
            )

            # Update conversation with first trace ID (for the conversation as a whole)
            if final_trace_id and not st.session_state.get("conversation_trace_set"):
                update_conversation_trace(
                    db_config, st.session_state.conversation_id, final_trace_id
                )
                st.session_state.conversation_trace_set = True
                print(f"📋 Set conversation trace ID: {final_trace_id}")

        # Reload messages
        if st.session_state.db_enabled and st.session_state.conversation_id:
            st.session_state.messages = get_conversation_messages(
                db_config, st.session_state.conversation_id
            )

        st.rerun()


if __name__ == "__main__":
    main()
