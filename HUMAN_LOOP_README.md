# Human-in-the-Loop Agent - 基于LangChain和LangGraph

这是一个基于 LangChain 1.0 和 LangGraph 构建的 **Human-in-the-Loop** Agent 项目，支持人工审核工作流。

## 功能特性

- ✅ 基于 LangChain 1.0 和 LangGraph 构建
- ✅ 使用 GLM（智谱AI）作为 LLM 提供商
- ✅ 支持人工审核工作流（批准/拒绝/修订）
- ✅ 流式输出（Server-Sent Events）
- ✅ FastAPI RESTful API
- ✅ 基于 userID 和 session 的会话管理
- ✅ 待审核内容状态跟踪

## 项目结构

```
├── human_agent.py           # Human-in-the-Loop Agent核心实现
├── human_session_manager.py # 支持审核的会话管理
├── human_api.py             # FastAPI应用（审核工作流接口）
├── test_human_cli.py        # 命令行测试工具
├── config.py                # 配置管理
└── HUMAN_LOOP_README.md     # 本文档
```

## 安装

```bash
# 使用 uv 安装依赖
uv sync

# 或使用 pip
pip install -r requirements.txt
```

配置环境变量（同原项目）：

```env
GLM_API_KEY=your_glm_api_key_here
GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
GLM_MODEL=glm-4
TEMPERATURE=0.7
THINKING_TYPE=disabled
```

## 运行

```bash
# 启动服务
uv run python human_api.py

# 或使用 uvicorn
uv run uvicorn human_api:app --host 0.0.0.0 --port 8000
```

服务启动后，访问：
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

## 工作流程

```
┌─────────────────────────────────────────────────────────────┐
│                     Human-in-the-Loop 工作流                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  用户请求 ──→ LLM生成内容 ──→ [待审核状态]                    │
│                                      │                       │
│                                      ▼                       │
│                           ┌─────────────────────┐            │
│                           │   人工审核决策        │            │
│                           └─────────────────────┘            │
│                                      │                       │
│                    ┌─────────────────┼─────────────────┐     │
│                    ▼                 ▼                 ▼     │
│               [批准]            [拒绝]           [修订]        │
│                    │                 │                 │     │
│                    ▼                 ▼                 ▼     │
│              加入对话历史      返回拒绝原因      返回修订建议   │
│                    │                 │                 │     │
│                    └─────────────────┴─────────────────┘     │
│                                      │                       │
│                                      ▼                       │
│                              LLM重新生成内容                  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## API接口

### 1. 生成内容（非流式）

**POST** `/chat/generate`

生成内容并进入待审核状态。

**请求体：**
```json
{
  "user_id": "user123",
  "session_id": "session456",
  "message": "请生成一道Python编程题"
}
```

**响应：**
```json
{
  "content": "生成的内容",
  "approval_status": "pending",
  "revision_count": 0,
  "message": "内容已生成，等待人工审核"
}
```

### 2. 流式生成内容

**POST** `/chat/stream`

流式生成内容，使用SSE格式返回。

**请求体：**
```json
{
  "user_id": "user123",
  "session_id": "session456",
  "message": "请生成一道Python编程题"
}
```

**响应格式（SSE）：**
```
data: {"type": "chunk", "content": "题"}
data: {"type": "chunk", "content": "目"}
data: {"type": "done", "content": "完整内容", "approval_status": "pending"}
```

### 3. 批准内容

**POST** `/approval/approve`

批准待审核内容，内容将被添加到对话历史。

**请求体：**
```json
{
  "user_id": "user123",
  "session_id": "session456",
  "approved": true,
  "reason": "内容符合要求"
}
```

### 4. 拒绝内容

**POST** `/approval/reject`

拒绝待审核内容。

**请求体：**
```json
{
  "user_id": "user123",
  "session_id": "session456",
  "approved": false,
  "reason": "内容不符合要求，需要重新生成"
}
```

### 5. 请求修订

**POST** `/approval/revise`

请求修订待审核内容。

**请求体：**
```json
{
  "user_id": "user123",
  "session_id": "session456",
  "feedback": "请添加更多细节"
}
```

### 6. 重新生成内容

**POST** `/chat/regenerate`

基于之前的反馈重新生成内容。

**请求体：**
```json
{
  "user_id": "user123",
  "session_id": "session456",
  "message": ""
}
```

### 7. 获取会话状态

**GET** `/session/{user_id}/{session_id}/status`

获取会话状态，包括待审核信息。

**响应：**
```json
{
  "user_id": "user123",
  "session_id": "session456",
  "message_count": 3,
  "has_pending_approval": true,
  "pending_content": "待审核的内容",
  "approval_status": "pending",
  "revision_count": 1,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:01:00"
}
```

## 命令行测试

### 运行完整工作流测试

```bash
uv run python test_human_cli.py --test
```

### 交互式模式

```bash
uv run python test_human_cli.py --interactive
```

交互式命令：
- `session [session_id]` - 创建或切换会话
- `status` - 查看当前会话状态
- `gen <message>` - 生成内容
- `approve [reason]` - 批准内容
- `reject <reason>` - 拒绝内容
- `revise <feedback>` - 请求修订
- `regen` - 重新生成内容
- `list` - 列出所有会话

## Python客户端示例

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. 创建会话
session = requests.post(f"{BASE_URL}/session/create", json={
    "user_id": "user123",
    "session_id": "session456"
}).json()

# 2. 生成内容
result = requests.post(f"{BASE_URL}/chat/generate", json={
    "user_id": "user123",
    "session_id": "session456",
    "message": "请生成一道Python编程题"
}).json()

print(f"生成的内容: {result['content']}")
print(f"审核状态: {result['approval_status']}")

# 3. 查看状态
status = requests.get(f"{BASE_URL}/session/user123/session456/status").json()
print(f"待审核: {status['has_pending_approval']}")

# 4. 批准内容
approval = requests.post(f"{BASE_URL}/approval/approve", json={
    "user_id": "user123",
    "session_id": "session456",
    "approved": True,
    "reason": "内容符合要求"
}).json()

print(approval)
```

## 技术架构

### 审核状态枚举

```python
class ApprovalStatus(str, Enum):
    PENDING = "pending"    # 待审核
    APPROVED = "approved"  # 已批准
    REJECTED = "rejected"  # 已拒绝
    REVISED = "revised"    # 需要修订
```

### LangGraph 工作流

```
用户输入 → LLM节点 → [条件判断] → 人工审核节点 → [条件判断] → 处理决策 → LLM节点（重新生成）
                    ↓                              ↓
                自动结束                          结束
```

### 会话状态管理

每个会话维护：
- 消息历史（已批准的内容）
- 待审核项目（PendingApproval）
- 审核状态
- 修订次数

## 与原项目的区别

| 特性 | 原项目 | Human-in-the-Loop项目 |
|------|--------|----------------------|
| 工作流 | 线性（输入→LLM→输出） | 循环（输入→LLM→审核→（拒绝/修订）→LLM） |
| 内容状态 | 直接返回 | 需要人工批准后才计入历史 |
| 会话管理 | 基础消息存储 | 支持待审核状态跟踪 |
| API接口 | 生成对话 | 生成+审核+重新生成 |

## 注意事项

1. **会话存储**：当前使用内存存储，服务重启后会丢失数据
2. **并发处理**：适合学习和开发，生产环境需要优化
3. **API密钥安全**：不要将 `.env` 文件提交到版本控制系统

## 扩展建议

- 添加持久化存储（Redis/数据库）
- 实现批量审核功能
- 添加审核人员角色和权限管理
- 支持多级审核流程
- 添加审核日志和统计

## 许可证

MIT License
