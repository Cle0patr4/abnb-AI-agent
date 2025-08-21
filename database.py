#!/usr/bin/env python3
"""
Module to handle SQLite database
"""
import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

class DatabaseManager:
    def __init__(self, db_path: str = "feedback.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with necessary tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Conversation logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    user_id TEXT NOT NULL,
                    query TEXT NOT NULL,
                    response TEXT NOT NULL,
                    response_time FLOAT,
                    used_rag BOOLEAN DEFAULT FALSE,
                    used_airtable BOOLEAN DEFAULT FALSE,
                    feedback_given BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # Feedback table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    conversation_id INTEGER,
                    user_id TEXT NOT NULL,
                    original_query TEXT NOT NULL,
                    original_response TEXT NOT NULL,
                    feedback_type TEXT NOT NULL, -- 'positive', 'negative', 'comment'
                    feedback_text TEXT,
                    processed BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (conversation_id) REFERENCES conversation_logs (id)
                )
            ''')
            
            conn.commit()
    
    def log_conversation(self, user_id: str, query: str, response: str, 
                        response_time: float = None, used_rag: bool = False, 
                        used_airtable: bool = False) -> int:
        """Log a conversation in the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO conversation_logs 
                (user_id, query, response, response_time, used_rag, used_airtable)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, query, response, response_time, used_rag, used_airtable))
            
            conn.commit()
            return cursor.lastrowid
    
    def add_feedback(self, user_id: str, original_query: str, original_response: str,
                    feedback_type: str, feedback_text: str = None, 
                    conversation_id: int = None) -> int:
        """Add feedback to a response"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO feedback 
                (conversation_id, user_id, original_query, original_response, 
                 feedback_type, feedback_text)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (conversation_id, user_id, original_query, original_response, 
                  feedback_type, feedback_text))
            
            # Mark conversation as having feedback
            if conversation_id:
                cursor.execute('''
                    UPDATE conversation_logs 
                    SET feedback_given = TRUE 
                    WHERE id = ?
                ''', (conversation_id,))
            
            conn.commit()
            return cursor.lastrowid
    
    def get_last_conversation(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get the last conversation of a user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, query, response, timestamp
                FROM conversation_logs 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 1
            ''', (user_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'query': row[1],
                    'response': row[2],
                    'timestamp': row[3]
                }
            return None
    
    def get_feedback_stats(self) -> Dict[str, Any]:
        """Get feedback statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total conversations
            cursor.execute('SELECT COUNT(*) FROM conversation_logs')
            total_conversations = cursor.fetchone()[0]
            
            # Conversations with feedback
            cursor.execute('SELECT COUNT(*) FROM conversation_logs WHERE feedback_given = TRUE')
            conversations_with_feedback = cursor.fetchone()[0]
            
            # Feedback types
            cursor.execute('''
                SELECT feedback_type, COUNT(*) 
                FROM feedback 
                GROUP BY feedback_type
            ''')
            feedback_types = dict(cursor.fetchall())
            
            return {
                'total_conversations': total_conversations,
                'conversations_with_feedback': conversations_with_feedback,
                'feedback_rate': (conversations_with_feedback / total_conversations * 100) if total_conversations > 0 else 0,
                'feedback_types': feedback_types
            }
    
    def get_unprocessed_feedback(self) -> List[Dict[str, Any]]:
        """Get unprocessed feedback"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, user_id, original_query, original_response, 
                       feedback_type, feedback_text, timestamp
                FROM feedback 
                WHERE processed = FALSE 
                ORDER BY timestamp DESC
            ''')
            
            rows = cursor.fetchall()
            return [
                {
                    'id': row[0],
                    'user_id': row[1],
                    'original_query': row[2],
                    'original_response': row[3],
                    'feedback_type': row[4],
                    'feedback_text': row[5],
                    'timestamp': row[6]
                }
                for row in rows
            ]

# Global database instance
db = DatabaseManager()
