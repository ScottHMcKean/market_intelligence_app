"""Database module for managing conversation history."""
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Optional
from contextlib import contextmanager

from .config import DatabaseConfig


def init_database(config: DatabaseConfig) -> None:
    """Initialize database schema."""
    with get_connection(config) as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
                    user_id TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT,
                    status TEXT DEFAULT 'pending',
                    query_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_conversation_id 
                ON messages(conversation_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_query_id 
                ON messages(query_id)
            """)
            
            conn.commit()


@contextmanager
def get_connection(config: DatabaseConfig):
    """Get a database connection."""
    conn = psycopg2.connect(
        host=config.host,
        port=config.port,
        dbname=config.name,
        user=config.user,
        password=config.password,
    )
    try:
        yield conn
    finally:
        conn.close()


def create_conversation(config: DatabaseConfig, user_id: str) -> int:
    """Create a new conversation."""
    with get_connection(config) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO conversations (user_id) VALUES (%s) RETURNING id",
                (user_id,)
            )
            conversation_id = cursor.fetchone()[0]
            conn.commit()
            return conversation_id


def add_message(
    config: DatabaseConfig,
    conversation_id: int,
    user_id: str,
    question: str,
    answer: Optional[str] = None,
    status: str = "pending",
    query_id: Optional[str] = None,
) -> int:
    """Add a message to a conversation."""
    with get_connection(config) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO messages 
                (conversation_id, user_id, question, answer, status, query_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (conversation_id, user_id, question, answer, status, query_id)
            )
            message_id = cursor.fetchone()[0]
            conn.commit()
            return message_id


def update_message(
    config: DatabaseConfig,
    message_id: int,
    answer: Optional[str] = None,
    status: Optional[str] = None,
) -> None:
    """Update a message with answer and status."""
    with get_connection(config) as conn:
        with conn.cursor() as cursor:
            updates = []
            params = []
            
            if answer is not None:
                updates.append("answer = %s")
                params.append(answer)
            
            if status is not None:
                updates.append("status = %s")
                params.append(status)
            
            if updates:
                updates.append("updated_at = CURRENT_TIMESTAMP")
                params.append(message_id)
                
                query = f"UPDATE messages SET {', '.join(updates)} WHERE id = %s"
                cursor.execute(query, params)
                conn.commit()


def get_conversation_messages(
    config: DatabaseConfig, conversation_id: int
) -> List[Dict]:
    """Get all messages from a conversation."""
    with get_connection(config) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT id, question, answer, status, query_id, created_at, updated_at
                FROM messages
                WHERE conversation_id = %s
                ORDER BY created_at ASC
                """,
                (conversation_id,)
            )
            return [dict(row) for row in cursor.fetchall()]


def get_message_by_query_id(config: DatabaseConfig, query_id: str) -> Optional[Dict]:
    """Get a message by query_id for resuming long-running queries."""
    with get_connection(config) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT id, conversation_id, question, answer, status, query_id, 
                       created_at, updated_at
                FROM messages
                WHERE query_id = %s
                """,
                (query_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None


def get_user_conversations(config: DatabaseConfig, user_id: str) -> List[Dict]:
    """Get all conversations for a user."""
    with get_connection(config) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT c.id, c.created_at, COUNT(m.id) as message_count
                FROM conversations c
                LEFT JOIN messages m ON c.id = m.conversation_id
                WHERE c.user_id = %s
                GROUP BY c.id, c.created_at
                ORDER BY c.created_at DESC
                """,
                (user_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

