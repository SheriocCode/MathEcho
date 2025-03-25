# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()

class Session(db.Model):
    __tablename__ = "sessions"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    session_id = db.Column(db.String(32), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))

class Question(db.Model):
    __tablename__ = "questions"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    session_id = db.Column(db.String(32), db.ForeignKey("sessions.session_id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=True)
    summary = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))

class WebSearchResult(db.Model):
    __tablename__ = "web_search_results"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    question_id = db.Column(db.String(32), db.ForeignKey("questions.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)

class RAGResult(db.Model):
    __tablename__ = "rag_results"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    question_id = db.Column(db.String(32), db.ForeignKey("questions.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    # java = db.Column(db.Text, nullable=False)

class KnowledgeSearchResult(db.Model):
    __tablename__ = "knowledge_search_results"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    question_id = db.Column(db.String(32), db.ForeignKey("questions.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)

class ApiSession(db.Model):
    __tablename__ = "api_sessions"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    api_session_id = db.Column(db.String(32), unique=True, nullable=False)
    session_id = db.Column(db.String(32), db.ForeignKey("sessions.session_id"), nullable=False)