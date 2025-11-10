"""
基于LangChain和LangGraph的流式Agent实现
用于生成题目
"""
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
import config


class AgentState(TypedDict):
    """Agent状态定义"""
    messages: Annotated[Sequence[BaseMessage], add_messages]


class StreamingAgent:
    """流式Agent类"""
    
    def __init__(self):
        """初始化Agent"""
        # 构建model_kwargs，用于传递GLM特有的参数
        model_kwargs = {}
        
        # 如果配置了关闭深度思考，添加thinking参数
        # 参考: https://open.bigmodel.cn/api/paas/v4/chat/completions
        # thinking参数设置为 {"type": "disabled"} 可以关闭深度思考，减少响应时间
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
        
        # 添加LLM节点
        workflow.add_node("llm", self._call_llm)
        
        # 设置入口点
        workflow.set_entry_point("llm")
        
        # 设置边：从llm到END
        workflow.add_edge("llm", END)
        
        # 编译图
        return workflow.compile()
    
    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一个专业的题目生成助手。根据用户的需求，生成相应的题目。
请确保题目：
1. 清晰明确
2. 难度适中
3. 有实际意义
4. 格式规范

直接生成题目，不需要额外的解释。"""
    
    def _call_llm(self, state: AgentState) -> AgentState:
        """调用LLM节点"""
        # 获取消息历史
        messages = state["messages"]
        
        # 添加系统提示词（用于生成题目）
        system_prompt = self._get_system_prompt()
        messages_with_system = [HumanMessage(content=system_prompt)] + list(messages)
        
        # 调用LLM
        response = self.llm.invoke(messages_with_system)
        
        # 返回更新后的状态
        return {"messages": [response]}
    
    def stream(self, user_message: str, history: Sequence[BaseMessage] = None):
        """
        流式调用Agent
        
        Args:
            user_message: 用户消息
            history: 历史消息列表
            
        Yields:
            str: 流式输出的文本块
        """
        # 构建消息列表
        messages = list(history) if history else []
        messages.append(HumanMessage(content=user_message))
        
        # 添加系统提示词（用于生成题目）
        system_prompt = self._get_system_prompt()
        messages_with_system = [HumanMessage(content=system_prompt)] + messages
        
        # 直接使用LLM的stream方法进行流式输出
        for chunk in self.llm.stream(messages_with_system):
            if hasattr(chunk, "content") and chunk.content:
                yield chunk.content
    
    def invoke(self, user_message: str, history: Sequence[BaseMessage] = None) -> str:
        """
        同步调用Agent（非流式）
        
        Args:
            user_message: 用户消息
            history: 历史消息列表
            
        Returns:
            str: AI回复
        """
        # 构建消息列表
        messages = list(history) if history else []
        messages.append(HumanMessage(content=user_message))
        
        # 构建初始状态
        initial_state = {"messages": messages}
        
        # 调用图
        result = self.graph.invoke(initial_state)
        
        # 提取AI回复
        if "messages" in result:
            for message in result["messages"]:
                if isinstance(message, AIMessage):
                    return message.content
        
        return ""

