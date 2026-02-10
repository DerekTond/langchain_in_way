"""
Human-in-the-Loop 会话管理模块
支持审核状态跟踪
"""
from typing import Dict, List, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from datetime import datetime
import uuid
from human_agent import ApprovalStatus


class PendingApproval:
    """待审核项目"""

    def __init__(
        self,
        content: str,
        approval_status: str = ApprovalStatus.PENDING,
        rejection_reason: str = "",
        revision_count: int = 0
    ):
        self.content = content
        self.approval_status = approval_status
        self.rejection_reason = rejection_reason
        self.revision_count = revision_count
        self.created_at = datetime.now()

    def approve(self):
        """批准"""
        self.approval_status = ApprovalStatus.APPROVED

    def reject(self, reason: str = ""):
        """拒绝"""
        self.approval_status = ApprovalStatus.REJECTED
        self.rejection_reason = reason

    def request_revision(self, feedback: str = ""):
        """请求修订"""
        self.approval_status = ApprovalStatus.REVISED
        self.rejection_reason = feedback


class HumanSession:
    """支持人工审核的会话类"""

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
        self.pending_approval: Optional[PendingApproval] = None
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def add_message(self, message: BaseMessage):
        """添加消息到会话"""
        self.messages.append(message)
        self.updated_at = datetime.now()

    def set_pending_approval(
        self,
        content: str,
        approval_status: str = ApprovalStatus.PENDING,
        rejection_reason: str = "",
        revision_count: int = 0
    ):
        """设置待审核内容"""
        self.pending_approval = PendingApproval(
            content=content,
            approval_status=approval_status,
            rejection_reason=rejection_reason,
            revision_count=revision_count
        )
        self.updated_at = datetime.now()

    def approve_content(self) -> bool:
        """批准待审核内容"""
        if self.pending_approval:
            self.pending_approval.approve()
            # 将批准的内容添加到消息历史
            self.messages.append(AIMessage(content=self.pending_approval.content))
            self.pending_approval = None
            self.updated_at = datetime.now()
            return True
        return False

    def reject_content(self, reason: str = "") -> bool:
        """拒绝待审核内容"""
        if self.pending_approval:
            self.pending_approval.reject(reason)
            self.updated_at = datetime.now()
            return True
        return False

    def request_revision(self, feedback: str = "") -> bool:
        """请求修订待审核内容"""
        if self.pending_approval:
            self.pending_approval.request_revision(feedback)
            self.updated_at = datetime.now()
            return True
        return False

    def get_history(self) -> List[BaseMessage]:
        """获取消息历史"""
        return self.messages.copy()

    def get_pending_approval(self) -> Optional[PendingApproval]:
        """获取待审核项目"""
        return self.pending_approval

    def has_pending_approval(self) -> bool:
        """检查是否有待审核内容"""
        return self.pending_approval is not None

    def get_status_dict(self) -> dict:
        """获取会话状态字典"""
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "message_count": len(self.messages),
            "has_pending_approval": self.has_pending_approval(),
            "pending_content": self.pending_approval.content if self.pending_approval else None,
            "approval_status": self.pending_approval.approval_status if self.pending_approval else None,
            "revision_count": self.pending_approval.revision_count if self.pending_approval else 0,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    def clear(self):
        """清空会话历史"""
        self.messages.clear()
        self.pending_approval = None
        self.updated_at = datetime.now()


class HumanSessionManager:
    """支持人工审核的会话管理器"""

    def __init__(self):
        """初始化会话管理器"""
        # 使用字典存储会话: key = (user_id, session_id)
        self._sessions: Dict[tuple, HumanSession] = {}

    def get_session(self, user_id: str, session_id: str) -> Optional[HumanSession]:
        """
        获取会话

        Args:
            user_id: 用户ID
            session_id: 会话ID

        Returns:
            HumanSession对象，如果不存在则返回None
        """
        key = (user_id, session_id)
        return self._sessions.get(key)

    def create_session(self, user_id: str, session_id: str = None) -> HumanSession:
        """
        创建新会话

        Args:
            user_id: 用户ID
            session_id: 会话ID，如果为None则自动生成

        Returns:
            新创建的HumanSession对象
        """
        session = HumanSession(user_id, session_id)
        key = (user_id, session.session_id)
        self._sessions[key] = session
        return session

    def get_or_create_session(self, user_id: str, session_id: str = None) -> HumanSession:
        """
        获取或创建会话

        Args:
            user_id: 用户ID
            session_id: 会话ID，如果为None则自动生成

        Returns:
            HumanSession对象
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

    def set_pending_approval(
        self,
        user_id: str,
        session_id: str,
        content: str,
        approval_status: str = ApprovalStatus.PENDING,
        rejection_reason: str = "",
        revision_count: int = 0
    ):
        """设置待审核内容"""
        session = self.get_or_create_session(user_id, session_id)
        session.set_pending_approval(content, approval_status, rejection_reason, revision_count)

    def approve_content(self, user_id: str, session_id: str) -> dict:
        """批准待审核内容"""
        session = self.get_session(user_id, session_id)
        if session and session.approve_content():
            return {
                "success": True,
                "message": "内容已批准并添加到对话历史"
            }
        return {
            "success": False,
            "message": "没有待审核的内容"
        }

    def reject_content(self, user_id: str, session_id: str, reason: str = "") -> dict:
        """拒绝待审核内容"""
        session = self.get_session(user_id, session_id)
        if session and session.reject_content(reason):
            return {
                "success": True,
                "message": "内容已拒绝",
                "reason": reason
            }
        return {
            "success": False,
            "message": "没有待审核的内容"
        }

    def request_revision(self, user_id: str, session_id: str, feedback: str = "") -> dict:
        """请求修订待审核内容"""
        session = self.get_session(user_id, session_id)
        if session and session.request_revision(feedback):
            return {
                "success": True,
                "message": "已请求修订",
                "feedback": feedback
            }
        return {
            "success": False,
            "message": "没有待审核的内容"
        }

    def get_session_status(self, user_id: str, session_id: str) -> Optional[dict]:
        """获取会话状态"""
        session = self.get_session(user_id, session_id)
        if session:
            return session.get_status_dict()
        return None

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

    def list_sessions(self, user_id: str = None) -> List[dict]:
        """
        列出所有会话或指定用户的会话

        Args:
            user_id: 用户ID，如果为None则返回所有会话

        Returns:
            会话状态字典列表
        """
        if user_id:
            return [
                session.get_status_dict()
                for (uid, _), session in self._sessions.items()
                if uid == user_id
            ]
        return [session.get_status_dict() for (_, _), session in self._sessions.items()]


# 全局会话管理器实例
human_session_manager = HumanSessionManager()
