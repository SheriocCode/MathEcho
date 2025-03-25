# db.py
from flask_sqlalchemy import SQLAlchemy

from models import ApiSession, db
from models import Session, Question, WebSearchResult, RAGResult, KnowledgeSearchResult

def init_db(app):
    """初始化数据库"""
    db.init_app(app)
    with app.app_context():
        db.create_all()

def create_session(session_id):
    """创建一个新的会话"""
    try:
        new_session = Session(session_id=session_id)
        db.session.add(new_session)
        db.session.commit()
        return True, session_id
    except Exception as e:
        db.session.rollback()
        return False, str(e)

def add_question_to_session(session_id, content):
    """向会话中添加问题"""
    try:
        session = Session.query.filter_by(session_id=session_id).first()
        if not session:
            return False, "Session not found"
        
        new_question = Question(session_id=session_id, content=content)
        db.session.add(new_question)
        db.session.commit()
        return True, new_question.id
    except Exception as e:
        db.session.rollback()
        return False, str(e)


def add_question_answer(question_id, answer):
    question = Question.query.filter_by(id=question_id).first()
    if not question:
        return False, "Question not found"

    question.answer = answer
    db.session.commit()
    return True, question.id

def add_question_summary(question_id, summary):
    question = Question.query.filter_by(id=question_id).first()
    if not question:
        return False, "Question not found"

    question.summary = summary
    db.session.commit()
    return True, question.id

def get_question_by_id(question_id):
    """根据问题ID获取问题"""
    current_question = Question.query.filter_by(id=question_id).first()
    
    return True, current_question

def get_answer_by_question_id(question_id):
    """根据问题ID获取回答"""
    question = Question.query.filter_by(id=question_id).first()
    if not question:
        return False, "Question not found"

    return True, question.answer

def get_previous_questions(session_id, question_id):
    """获取先前的问题"""
    previous_questions = Question.query.filter(
        Question.session_id == session_id, Question.id < question_id
    ).order_by(Question.id.desc()).limit(5).all()
    return True, previous_questions

def add_web_search_result(question_id, web_search_result):
    """添加网络搜索结果"""
    question = Question.query.filter_by(id=question_id).first()
    if not question:
        return False, "Question_Id not found"

    web_search_result = WebSearchResult(question_id=question_id, content=web_search_result)
    db.session.add(web_search_result)
    db.session.commit()
    return True, web_search_result.id

def add_rag_result(question_id, rag_result):
    """添加RAG结果"""
    question = Question.query.filter_by(id=question_id).first()
    if not question:
        return False, "Question_Id not found"

    rag_result = RAGResult(question_id=question_id, content=rag_result)
    db.session.add(rag_result)
    db.session.commit()

    return True, rag_result.id

def add_knowledge_search_result(question_id, knowledge_search_result):
    """添加知识搜索结果"""
    question = Question.query.filter_by(id=question_id).first()
    if not question:
        return False, "Question_Id not found"

    knowledge_search_result = KnowledgeSearchResult(question_id=question_id, content=knowledge_search_result)
    db.session.add(knowledge_search_result)
    db.session.commit()

    return True, knowledge_search_result.id


def get_retrieve_data(question_id):
    """获取检索数据"""
    web_search_result = WebSearchResult.query.filter_by(question_id=question_id).first()
    rag_result = RAGResult.query.filter_by(question_id=question_id).first()
    knowledge_search_result = KnowledgeSearchResult.query.filter_by(question_id=question_id).first()

    retrieve_data = {
        "web_search_result": web_search_result.content if web_search_result else '',
        "rag_result": rag_result.content if rag_result else '', 
        "knowledge_search_result": knowledge_search_result.content if knowledge_search_result else ''
    }

    return True, retrieve_data

def create_apisession(session_id, api_session_id=None):
    """获取或创建API会话"""
    api_session = ApiSession.query.filter_by(session_id=session_id).first()
    if not api_session:
        api_session = ApiSession(session_id=session_id, api_session_id=api_session_id)
        db.session.add(api_session)
        db.session.commit()

    return True, api_session.api_session_id

def get_apisession(session_id):
    """获取API会话"""
    api_session = ApiSession.query.filter_by(session_id=session_id).first()
    if not api_session:
        return False, None

    return True, api_session.api_session_id