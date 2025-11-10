"""
会话管理模块
基于userID和session维护对话历史
"""
from typing import Dict, List, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from datetime import datetime
import uuid


class Session:
    """会话类"""
    
    def __init__(self, user_id: str, session_id: str = None):
        """
        初始化会话
        
        Args:
            user_id: 用户ID
            session_id: 会话ID，如果为None则自动生成
        """
        self.user_id = user_id
        self.session_id = session_id or str(uuid.uuid4())
        self.messages: List[BaseMessage] = []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def add_message(self, message: BaseMessage):
        """添加消息到会话"""
        self.messages.append(message)
        self.updated_at = datetime.now()
    
    def get_history(self) -> List[BaseMessage]:
        """获取消息历史"""
        return self.messages.copy()
    
    def clear(self):
        """清空会话历史"""
        self.messages.clear()
        self.updated_at = datetime.now()


class SessionManager:
    """会话管理器"""
    
    def __init__(self):
        """初始化会话管理器"""
        # 使用字典存储会话: key = (user_id, session_id)
        self._sessions: Dict[tuple, Session] = {}
    
    def get_session(self, user_id: str, session_id: str) -> Optional[Session]:
        """
        获取会话
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            
        Returns:
            Session对象，如果不存在则返回None
        """
        key = (user_id, session_id)
        return self._sessions.get(key)
    
    def create_session(self, user_id: str, session_id: str = None) -> Session:
        """
        创建新会话
        
        Args:
            user_id: 用户ID
            session_id: 会话ID，如果为None则自动生成
            
        Returns:
            新创建的Session对象
        """
        session = Session(user_id, session_id)
        key = (user_id, session.session_id)
        self._sessions[key] = session
        return session
    
    def get_or_create_session(self, user_id: str, session_id: str = None) -> Session:
        """
        获取或创建会话
        
        Args:
            user_id: 用户ID
            session_id: 会话ID，如果为None则自动生成
            
        Returns:
            Session对象
        """
        if session_id:
            session = self.get_session(user_id, session_id)
            if session:
                return session
        
        return self.create_session(user_id, session_id)
    
    def add_message(self, user_id: str, session_id: str, message: BaseMessage):
        """
        向会话添加消息
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            message: 消息对象
        """
        session = self.get_or_create_session(user_id, session_id)
        session.add_message(message)
    
    def get_history(self, user_id: str, session_id: str) -> List[BaseMessage]:
        """
        获取会话历史
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            
        Returns:
            消息历史列表
        """
        session = self.get_or_create_session(user_id, session_id)
        return session.get_history()
    
    def clear_session(self, user_id: str, session_id: str):
        """
        清空会话
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
        """
        session = self.get_session(user_id, session_id)
        if session:
            session.clear()
    
    def delete_session(self, user_id: str, session_id: str):
        """
        删除会话
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
        """
        key = (user_id, session_id)
        if key in self._sessions:
            del self._sessions[key]


# 全局会话管理器实例
session_manager = SessionManager()

