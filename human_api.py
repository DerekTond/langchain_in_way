"""
Human-in-the-Loop FastAPI应用
支持人工审核工作流的API接口
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import json
from human_agent import HumanInLoopAgent, ApprovalStatus
from human_session_manager import human_session_manager
import config


app = FastAPI(
    title="Human-in-the-Loop Agent API",
    description="基于LangChain和LangGraph的人工审核Agent API",
    version="1.0.0"
)

# 初始化Agent
agent = HumanInLoopAgent()


# ========== 请求模型 ==========

class ChatRequest(BaseModel):
    """聊天请求模型"""
    user_id: str
    session_id: Optional[str] = None
    message: str


class ApprovalRequest(BaseModel):
    """审核请求模型"""
    user_id: str
    session_id: str
    approved: bool
    reason: Optional[str] = ""


class RevisionRequest(BaseModel):
    """修订请求模型"""
    user_id: str
    session_id: str
    feedback: Optional[str] = ""


class SessionCreateRequest(BaseModel):
    """会话创建请求模型"""
    user_id: str
    session_id: Optional[str] = None


# ========== API接口 ==========

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Human-in-the-Loop Agent API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


@app.post("/session/create")
async def create_session(request: SessionCreateRequest):
    """
    创建新会话

    返回会话信息
    """
    session = human_session_manager.create_session(
        user_id=request.user_id,
        session_id=request.session_id
    )

    return {
        "user_id": session.user_id,
        "session_id": session.session_id,
        "message": "会话创建成功"
    }


@app.get("/session/{user_id}/{session_id}")
async def get_session(user_id: str, session_id: str):
    """
    获取会话历史和状态
    """
    status = human_session_manager.get_session_status(user_id, session_id)

    if not status:
        raise HTTPException(status_code=404, detail="会话不存在")

    history = human_session_manager.get_history(user_id, session_id)

    return {
        "user_id": user_id,
        "session_id": session_id,
        "status": status,
        "messages": [
            {"role": msg.type, "content": msg.content}
            for msg in history
        ]
    }


@app.get("/session/{user_id}/{session_id}/status")
async def get_session_status(user_id: str, session_id: str):
    """
    获取会话状态（包括待审核信息）
    """
    status = human_session_manager.get_session_status(user_id, session_id)

    if not status:
        raise HTTPException(status_code=404, detail="会话不存在")

    return status


@app.delete("/session/{user_id}/{session_id}")
async def delete_session(user_id: str, session_id: str):
    """
    删除会话
    """
    human_session_manager.delete_session(user_id, session_id)
    return {"message": "会话已删除"}


@app.get("/sessions")
async def list_sessions(user_id: Optional[str] = None):
    """
    列出所有会话或指定用户的会话
    """
    sessions = human_session_manager.list_sessions(user_id)
    return {
        "count": len(sessions),
        "sessions": sessions
    }


@app.post("/chat/generate")
async def generate_content(request: ChatRequest):
    """
    生成内容（非流式）

    生成的内容需要人工审核后才会计入对话历史
    """
    # 获取历史
    history = human_session_manager.get_history(request.user_id, request.session_id)

    # 调用Agent
    result = agent.invoke(request.message, history)

    # 设置待审核状态
    human_session_manager.set_pending_approval(
        user_id=request.user_id,
        session_id=request.session_id,
        content=result["content"],
        approval_status=result["approval_status"],
        revision_count=result["revision_count"]
    )

    # 添加用户消息到历史
    human_session_manager.add_message(
        request.user_id,
        request.session_id,
        {"role": "user", "content": request.message}
    )

    return {
        "content": result["content"],
        "approval_status": result["approval_status"],
        "revision_count": result["revision_count"],
        "message": "内容已生成，等待人工审核"
    }


@app.post("/chat/stream")
async def generate_content_stream(request: ChatRequest):
    """
    流式生成内容

    使用SSE格式返回，生成完成后需要人工审核
    """
    async def stream_generator():
        # 获取历史
        history = human_session_manager.get_history(request.user_id, request.session_id)

        full_content = ""

        # 流式输出
        for chunk in agent.stream(request.message, history):
            chunk_json = json.dumps(chunk, ensure_ascii=False)
            yield f"data: {chunk_json}\n\n"

            if chunk.get("type") == "chunk":
                full_content += chunk["content"]
            elif chunk.get("type") == "done":
                # 流式输出完成，设置待审核状态
                human_session_manager.set_pending_approval(
                    user_id=request.user_id,
                    session_id=request.session_id,
                    content=chunk["content"],
                    approval_status=chunk["approval_status"]
                )

                # 添加用户消息到历史
                human_session_manager.add_message(
                    request.user_id,
                    request.session_id,
                    {"role": "user", "content": request.message}
                )

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.post("/approval/approve")
async def approve_content(request: ApprovalRequest):
    """
    批准待审核内容

    批准后，内容会被添加到对话历史
    """
    result = human_session_manager.approve_content(
        user_id=request.user_id,
        session_id=request.session_id
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@app.post("/approval/reject")
async def reject_content(request: ApprovalRequest):
    """
    拒绝待审核内容

    拒绝后，需要重新生成内容
    """
    result = human_session_manager.reject_content(
        user_id=request.user_id,
        session_id=request.session_id,
        reason=request.reason
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@app.post("/approval/revise")
async def request_revision(request: RevisionRequest):
    """
    请求修订待审核内容

    会将反馈发送给Agent重新生成
    """
    result = human_session_manager.request_revision(
        user_id=request.user_id,
        session_id=request.session_id,
        feedback=request.feedback
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@app.post("/chat/regenerate")
async def regenerate_content(request: ChatRequest):
    """
    重新生成内容

    使用之前的反馈原因重新生成
    """
    session = human_session_manager.get_session(request.user_id, request.session_id)

    if not session or not session.has_pending_approval():
        raise HTTPException(status_code=400, detail="没有待审核的内容")

    pending = session.get_pending_approval()

    # 获取历史
    history = human_session_manager.get_history(request.user_id, request.session_id)

    # 构建包含反馈的消息
    if pending.rejection_reason:
        feedback_message = f"请根据以下反馈改进内容：{pending.rejection_reason}"
    else:
        feedback_message = "请重新生成内容"

    # 调用Agent重新生成
    result = agent.invoke(feedback_message, history)

    # 更新待审核状态
    human_session_manager.set_pending_approval(
        user_id=request.user_id,
        session_id=request.session_id,
        content=result["content"],
        approval_status=result["approval_status"],
        rejection_reason="",
        revision_count=pending.revision_count + 1
    )

    return {
        "content": result["content"],
        "approval_status": result["approval_status"],
        "revision_count": pending.revision_count + 1,
        "message": "内容已重新生成，等待人工审核"
    }


# ========== 启动服务 ==========

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )
