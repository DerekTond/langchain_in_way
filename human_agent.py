"""
基于LangChain和LangGraph的Human-in-the-Loop Agent实现
支持人工审核工作流
"""
from typing import TypedDict, Annotated, Sequence, Literal
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from enum import Enum
import config


class ApprovalStatus(str, Enum):
    """审核状态枚举"""
    PENDING = "pending"        # 待审核
    APPROVED = "approved"      # 已批准
    REJECTED = "rejected"      # 已拒绝
    REVISED = "revised"        # 需要修订


class AgentState(TypedDict):
    """Agent状态定义"""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    approval_status: str              # 审核状态
    pending_content: str              # 待审核的内容
    rejection_reason: str             # 拒绝原因
    revision_count: int               # 修订次数


class HumanInLoopAgent:
    """Human-in-the-Loop Agent类"""

    def __init__(self):
        """初始化Agent"""
        # 构建model_kwargs，用于传递GLM特有的参数
        model_kwargs = {}

        # 如果配置了关闭深度思考，添加thinking参数
        if config.Config.THINKING_TYPE == "disabled":
            model_kwargs["thinking"] = {"type": "disabled"}

        # 配置GLM模型
        self.llm = ChatOpenAI(
            model=config.Config.GLM_MODEL,
            api_key=config.Config.GLM_API_KEY,
            base_url=config.Config.GLM_BASE_URL,
            streaming=config.Config.STREAMING,
            temperature=config.Config.TEMPERATURE,
            model_kwargs=model_kwargs if model_kwargs else {},
        )

        # 构建工作流图
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """构建LangGraph工作流"""
        # 创建状态图
        workflow = StateGraph(AgentState)

        # 添加节点
        workflow.add_node("llm", self._call_llm)
        workflow.add_node("human_review", self._human_review)
        workflow.add_node("process_decision", self._process_decision)

        # 设置入口点
        workflow.set_entry_point("llm")

        # 添加条件边：从llm到human_review或END
        workflow.add_conditional_edges(
            "llm",
            self._should_need_review,
            {
                "review": "human_review",
                "auto_approve": END
            }
        )

        # 添加条件边：从human_review到process_decision或END
        workflow.add_conditional_edges(
            "human_review",
            self._check_approval,
            {
                "approved": END,
                "rejected": "process_decision",
                "revised": "process_decision"
            }
        )

        # 添加边：从process_decision到llm（重新生成）
        workflow.add_edge("process_decision", "llm")

        # 编译图
        return workflow.compile()

    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一个专业的内容生成助手。根据用户的需求，生成相应的内容。

请确保生成的内容：
1. 清晰明确
2. 准确可靠
3. 格式规范
4. 符合用户需求

直接生成内容，不需要额外的解释。"""

    def _should_need_review(self, state: AgentState) -> str:
        """
        决定是否需要人工审核
        这里可以根据内容长度、关键词等条件判断
        """
        # 简单示例：所有内容都需要审核
        # 可以根据实际需求调整逻辑
        return "review"

    def _check_approval(self, state: AgentState) -> str:
        """
        检查人工审核结果
        返回下一步的节点名称
        """
        status = state.get("approval_status", ApprovalStatus.PENDING)

        if status == ApprovalStatus.APPROVED:
            return "approved"
        elif status == ApprovalStatus.REJECTED:
            return "rejected"
        elif status == ApprovalStatus.REVISED:
            return "revised"

        return "approved"

    def _call_llm(self, state: AgentState) -> AgentState:
        """调用LLM节点"""
        # 获取消息历史
        messages = state["messages"]

        # 如果有拒绝原因，添加到消息中以便LLM改进
        if state.get("rejection_reason"):
            messages = list(messages) + [
                HumanMessage(content=f"请根据以下反馈改进内容：{state['rejection_reason']}")
            ]

        # 添加系统提示词
        system_prompt = self._get_system_prompt()
        messages_with_system = [HumanMessage(content=system_prompt)] + list(messages)

        # 调用LLM
        response = self.llm.invoke(messages_with_system)

        # 返回更新后的状态
        return {
            "messages": [response],
            "pending_content": response.content,
            "approval_status": ApprovalStatus.PENDING,
            "rejection_reason": "",
            "revision_count": state.get("revision_count", 0)
        }

    def _human_review(self, state: AgentState) -> AgentState:
        """
        人工审核节点（占位符）
        实际审核通过API触发
        """
        # 这个节点等待人工审核
        # 状态会被API接口更新
        return state

    def _process_decision(self, state: AgentState) -> AgentState:
        """处理人工审核决策"""
        status = state.get("approval_status")

        if status == ApprovalStatus.REJECTED:
            # 拒绝：添加拒绝原因，重新生成
            return {
                "messages": state["messages"],
                "approval_status": status,
                "rejection_reason": state.get("rejection_reason", ""),
                "revision_count": state.get("revision_count", 0) + 1
            }
        elif status == ApprovalStatus.REVISED:
            # 修订：添加修订建议，重新生成
            return {
                "messages": state["messages"],
                "approval_status": status,
                "rejection_reason": state.get("rejection_reason", ""),
                "revision_count": state.get("revision_count", 0) + 1
            }

        return state

    def invoke(self, user_message: str, history: Sequence[BaseMessage] = None) -> dict:
        """
        同步调用Agent（非流式）

        Args:
            user_message: 用户消息
            history: 历史消息列表

        Returns:
            dict: 包含内容和审核状态的结果
        """
        # 构建消息列表
        messages = list(history) if history else []
        messages.append(HumanMessage(content=user_message))

        # 构建初始状态
        initial_state: AgentState = {
            "messages": messages,
            "approval_status": ApprovalStatus.PENDING,
            "pending_content": "",
            "rejection_reason": "",
            "revision_count": 0
        }

        # 调用图
        result = self.graph.invoke(initial_state)

        # 返回结果
        return {
            "content": result.get("pending_content", ""),
            "approval_status": result.get("approval_status", ApprovalStatus.PENDING),
            "revision_count": result.get("revision_count", 0),
            "messages": result.get("messages", [])
        }

    def stream(self, user_message: str, history: Sequence[BaseMessage] = None):
        """
        流式调用Agent

        Args:
            user_message: 用户消息
            history: 历史消息列表

        Yields:
            dict: 流式输出的数据块
        """
        # 构建消息列表
        messages = list(history) if history else []
        messages.append(HumanMessage(content=user_message))

        # 添加系统提示词
        system_prompt = self._get_system_prompt()
        messages_with_system = [HumanMessage(content=system_prompt)] + messages

        # 使用LLM的stream方法进行流式输出
        full_content = ""
        for chunk in self.llm.stream(messages_with_system):
            if hasattr(chunk, "content") and chunk.content:
                full_content += chunk.content
                yield {
                    "type": "chunk",
                    "content": chunk.content
                }

        # 流式输出完成后，返回完整内容待审核
        yield {
            "type": "done",
            "content": full_content,
            "approval_status": ApprovalStatus.PENDING
        }

    def submit_approval(
        self,
        user_id: str,
        session_id: str,
        approved: bool,
        reason: str = ""
    ) -> dict:
        """
        提交人工审核结果

        Args:
            user_id: 用户ID
            session_id: 会话ID
            approved: 是否批准
            reason: 拒绝或修订原因

        Returns:
            dict: 处理结果
        """
        # 这个方法需要配合session_manager使用
        # 具体实现在API层处理
        status = ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED

        return {
            "status": status,
            "reason": reason
        }
