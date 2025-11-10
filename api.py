"""
FastAPI应用
提供流式对话接口和会话管理
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List
import json
import asyncio
from agent import StreamingAgent
from session_manager import session_manager
from langchain_core.messages import HumanMessage, AIMessage
import config

# 创建FastAPI应用
app = FastAPI(
    title="流式Agent API",
    description="基于LangChain和LangGraph的流式Agent，用于生成题目",
    version="1.0.0"
)

# 全局Agent实例
agent = StreamingAgent()


# 请求/响应模型
class ChatRequest(BaseModel):
    """聊天请求模型"""
    user_id: str = Field(..., description="用户ID")
    session_id: str = Field(..., description="会话ID")
    message: str = Field(..., description="用户消息")


class ChatResponse(BaseModel):
    """聊天响应模型"""
    content: str = Field(..., description="AI回复内容")


class SessionCreateRequest(BaseModel):
    """创建会话请求模型"""
    user_id: str = Field(..., description="用户ID")
    session_id: Optional[str] = Field(None, description="会话ID，如果不提供则自动生成")


class SessionCreateResponse(BaseModel):
    """创建会话响应模型"""
    user_id: str = Field(..., description="用户ID")
    session_id: str = Field(..., description="会话ID")
    message: str = Field(..., description="提示信息")


class MessageHistory(BaseModel):
    """消息历史模型"""
    role: str = Field(..., description="角色：user或assistant")
    content: str = Field(..., description="消息内容")


class SessionHistoryResponse(BaseModel):
    """会话历史响应模型"""
    user_id: str = Field(..., description="用户ID")
    session_id: str = Field(..., description="会话ID")
    messages: List[MessageHistory] = Field(..., description="消息历史列表")


def format_sse(data: dict) -> str:
    """格式化SSE数据"""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    流式对话接口
    
    使用Server-Sent Events (SSE)格式返回流式响应
    """
    try:
        # 获取或创建会话
        session = session_manager.get_or_create_session(
            user_id=request.user_id,
            session_id=request.session_id
        )
        
        # 获取历史消息
        history = session.get_history()
        
        # 添加用户消息到会话
        user_message = HumanMessage(content=request.message)
        session.add_message(user_message)
        
        def generate():
            """生成器函数，用于流式输出"""
            try:
                # 调用Agent的流式方法
                full_response = ""
                for chunk in agent.stream(request.message, history):
                    if chunk:
                        full_response += chunk
                        # 发送SSE格式的数据
                        yield format_sse({
                            "type": "chunk",
                            "content": chunk
                        })
                
                # 添加AI回复到会话
                if full_response:
                    ai_message = AIMessage(content=full_response)
                    session.add_message(ai_message)
                
                # 发送完成信号
                yield format_sse({
                    "type": "done",
                    "content": full_response
                })
            except Exception as e:
                # 发送错误信息
                yield format_sse({
                    "type": "error",
                    "error": str(e)
                })
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理请求时出错: {str(e)}")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    非流式对话接口（同步）
    """
    try:
        # 获取或创建会话
        session = session_manager.get_or_create_session(
            user_id=request.user_id,
            session_id=request.session_id
        )
        
        # 获取历史消息
        history = session.get_history()
        
        # 添加用户消息到会话
        user_message = HumanMessage(content=request.message)
        session.add_message(user_message)
        
        # 调用Agent
        response = agent.invoke(request.message, history)
        
        # 添加AI回复到会话
        if response:
            ai_message = AIMessage(content=response)
            session.add_message(ai_message)
        
        return ChatResponse(content=response)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理请求时出错: {str(e)}")


@app.post("/session/create", response_model=SessionCreateResponse)
async def create_session(request: SessionCreateRequest):
    """
    创建新会话
    """
    try:
        session = session_manager.create_session(
            user_id=request.user_id,
            session_id=request.session_id
        )
        return SessionCreateResponse(
            user_id=session.user_id,
            session_id=session.session_id,
            message="会话创建成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建会话时出错: {str(e)}")


@app.get("/session/{user_id}/{session_id}", response_model=SessionHistoryResponse)
async def get_session_history(user_id: str, session_id: str):
    """
    获取会话历史
    """
    try:
        history = session_manager.get_history(user_id, session_id)
        
        # 转换为响应格式
        messages = []
        for msg in history:
            if isinstance(msg, HumanMessage):
                messages.append(MessageHistory(role="user", content=msg.content))
            elif isinstance(msg, AIMessage):
                messages.append(MessageHistory(role="assistant", content=msg.content))
        
        return SessionHistoryResponse(
            user_id=user_id,
            session_id=session_id,
            messages=messages
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话历史时出错: {str(e)}")


@app.delete("/session/{user_id}/{session_id}")
async def delete_session(user_id: str, session_id: str):
    """
    删除会话
    """
    try:
        session_manager.delete_session(user_id, session_id)
        return {"message": "会话删除成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除会话时出错: {str(e)}")


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "流式Agent API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

