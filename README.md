# 流式Agent - 基于LangChain和LangGraph

这是一个基于LangChain 1.0和LangGraph构建的流式Agent项目，主要用于生成题目。项目使用FastAPI提供HTTP接口，支持基于userID和session的会话管理。

## 功能特性

- ✅ 基于LangChain 1.0和LangGraph构建
- ✅ 使用GLM（智谱AI）作为LLM提供商
- ✅ 支持流式输出（Server-Sent Events）
- ✅ FastAPI RESTful API
- ✅ 基于userID和session的会话管理
- ✅ 自动维护对话历史

## 项目结构

```
.
├── pyproject.toml       # 项目配置（uv使用）
├── requirements.txt      # 项目依赖（兼容传统pip）
├── config.py            # 配置管理
├── agent.py             # Agent核心实现
├── session_manager.py   # 会话管理
├── api.py               # FastAPI应用
├── env.example          # 环境变量示例
└── README.md            # 项目文档
```

## 安装

### 1. 克隆项目

```bash
git clone <repository-url>
cd langchain_in_way
```

### 2. 安装依赖

#### 方式一：使用 uv（推荐）

`uv` 是一个快速的 Python 包管理器和项目管理工具。

**安装 uv：**

```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**配置镜像源（加速下载）：**

创建或编辑 `~/.pip/pip.conf`（Linux/macOS）或 `%APPDATA%\pip\pip.ini`（Windows）：

```ini
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
```

或者使用环境变量（临时设置）：

```bash
# Windows (PowerShell)
$env:UV_INDEX_URL="https://pypi.tuna.tsinghua.edu.cn/simple"

# Linux/macOS
export UV_INDEX_URL="https://pypi.tuna.tsinghua.edu.cn/simple"
```

**使用 uv 安装依赖：**

```bash
# 同步依赖（创建虚拟环境并安装所有依赖）
uv sync

# 或者指定 Python 版本
uv sync --python 3.11

# 激活虚拟环境（uv 会自动创建 .venv）
# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate
```

**常用 uv 命令：**

```bash
# 同步依赖（安装/更新所有依赖）
uv sync

# 添加新依赖
uv add package-name

# 添加开发依赖
uv add --dev package-name

# 运行命令（自动使用虚拟环境）
uv run python api.py

# 查看已安装的包
uv pip list
```

#### 方式二：使用传统 pip

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `env.example` 为 `.env` 并填写配置：

```bash
cp env.example .env
```

编辑 `.env` 文件，填入你的GLM API密钥：

```env
GLM_API_KEY=your_glm_api_key_here
GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
GLM_MODEL=glm-4
TEMPERATURE=0.7
THINKING_TYPE=disabled  # 关闭深度思考，减少响应时间
```

**配置说明：**
- `GLM_API_KEY`: 从 [智谱AI开放平台](https://open.bigmodel.cn/) 获取
- `GLM_MODEL`: 模型名称，如 `glm-4`、`glm-4-6` 等
- `TEMPERATURE`: 温度参数（0.0-1.0），控制输出的随机性
- `THINKING_TYPE`: 深度思考配置
  - 设置为 `disabled` 关闭深度思考，**减少响应时间**（推荐用于题目生成）
  - 设置为空或注释掉则启用深度思考（适合复杂推理任务）

## 运行

### 启动服务

**使用 uv：**

```bash
# 使用 uv run 自动管理虚拟环境
uv run python api.py

# 或使用 uvicorn
uv run uvicorn api:app --host 0.0.0.0 --port 8000
```

**使用传统方式：**

```bash
# 确保已激活虚拟环境
python api.py

# 或使用 uvicorn
uvicorn api:app --host 0.0.0.0 --port 8000
```

服务启动后，访问：
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

**curl命令参考**: 查看 [API_CURL_EXAMPLES.md](API_CURL_EXAMPLES.md) 获取所有接口的curl命令示例，可用于配置Postman。

## 命令行测试

项目提供了命令行测试工具 `test_cli.py`，可以方便地在命令行中验证整个流程。

### 运行所有测试

```bash
# 使用 uv
uv run python test_cli.py --test

# 或使用传统方式
python test_cli.py --test
```

### 交互式聊天模式

```bash
# 启动交互式聊天
uv run python test_cli.py --interactive
# 或简写
uv run python test_cli.py -i
```

在交互式模式下：
- 输入消息与AI对话
- 输入 `stream` 切换到流式模式
- 输入 `normal` 切换回普通模式
- 输入 `quit` 或 `exit` 退出

### 单次测试

```bash
# 测试非流式对话
uv run python test_cli.py --message "请生成一道Python编程题"

# 测试流式对话
uv run python test_cli.py --message "请生成一道Python编程题" --stream

# 指定用户ID和会话ID
uv run python test_cli.py --message "请生成一道Python编程题" --user-id "user123" --session-id "session456"
```

### 测试特定接口

```bash
# 测试健康检查
uv run python test_cli.py --test

# 测试特定URL（如果服务运行在不同端口）
uv run python test_cli.py --url "http://localhost:8080" --test
```

## API接口

### 1. 流式对话接口

**POST** `/chat/stream`

流式对话接口，使用Server-Sent Events (SSE)格式返回响应。

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
data: {"type": "chunk", "content": "题目"}
data: {"type": "chunk", "content": "内容"}
data: {"type": "done", "content": "完整内容"}
```

**使用curl测试：**
```bash
curl -X POST "http://localhost:8000/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "session_id": "session456",
    "message": "请生成一道Python编程题"
  }'
```

### 2. 非流式对话接口

**POST** `/chat`

同步对话接口，返回完整响应。

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
  "content": "完整AI回复内容"
}
```

### 3. 创建会话

**POST** `/session/create`

创建新会话。

**请求体：**
```json
{
  "user_id": "user123",
  "session_id": "session456"  // 可选，不提供则自动生成
}
```

**响应：**
```json
{
  "user_id": "user123",
  "session_id": "session456",
  "message": "会话创建成功"
}
```

### 4. 获取会话历史

**GET** `/session/{user_id}/{session_id}`

获取指定会话的消息历史。

**响应：**
```json
{
  "user_id": "user123",
  "session_id": "session456",
  "messages": [
    {
      "role": "user",
      "content": "用户消息"
    },
    {
      "role": "assistant",
      "content": "AI回复"
    }
  ]
}
```

### 5. 删除会话

**DELETE** `/session/{user_id}/{session_id}`

删除指定会话。

## Python客户端示例

### 流式调用示例

```python
import requests
import json

def stream_chat(user_id: str, session_id: str, message: str):
    """流式对话"""
    url = "http://localhost:8000/chat/stream"
    data = {
        "user_id": user_id,
        "session_id": session_id,
        "message": message
    }
    
    response = requests.post(url, json=data, stream=True)
    
    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            if line.startswith('data: '):
                data_str = line[6:]  # 去掉 'data: ' 前缀
                try:
                    data_obj = json.loads(data_str)
                    if data_obj.get('type') == 'chunk':
                        print(data_obj.get('content', ''), end='', flush=True)
                    elif data_obj.get('type') == 'done':
                        print(f"\n\n完整回复: {data_obj.get('content', '')}")
                except json.JSONDecodeError:
                    pass

# 使用示例
stream_chat("user123", "session456", "请生成一道关于列表操作的Python编程题")
```

### 非流式调用示例

```python
import requests

def chat(user_id: str, session_id: str, message: str):
    """非流式对话"""
    url = "http://localhost:8000/chat"
    data = {
        "user_id": user_id,
        "session_id": session_id,
        "message": message
    }
    
    response = requests.post(url, json=data)
    result = response.json()
    return result['content']

# 使用示例
response = chat("user123", "session456", "请生成一道Python编程题")
print(response)
```

## 技术架构

### Agent工作流

使用LangGraph构建简单的状态图：

```
用户输入 → LLM节点 → AI回复 → 结束
```

### 会话管理

- 使用内存字典存储会话（适合学习和小规模使用）
- 每个会话由 `(user_id, session_id)` 唯一标识
- 自动维护消息历史
- 生产环境可扩展为Redis等持久化存储

### 流式输出

- 使用LangChain的流式功能
- FastAPI的StreamingResponse实现HTTP流式响应
- SSE格式便于前端接收和处理

## 开发说明

### 修改Agent行为

编辑 `agent.py` 中的 `_call_llm` 方法，可以修改系统提示词或添加额外的处理逻辑。

### 扩展功能

- 添加工具（Tools）：在 `agent.py` 中集成LangChain工具
- 持久化存储：修改 `session_manager.py` 使用数据库
- 添加认证：在 `api.py` 中添加JWT等认证机制

## 注意事项

1. **API密钥安全**：不要将 `.env` 文件提交到版本控制系统
2. **会话存储**：当前使用内存存储，服务重启后会丢失会话数据
3. **并发处理**：当前实现适合学习和开发，生产环境需要优化并发性能

## 许可证

MIT License

## 参考资源

- [LangChain文档](https://python.langchain.com/)
- [LangGraph文档](https://langchain-ai.github.io/langgraph/)
- [FastAPI文档](https://fastapi.tiangolo.com/)
- [智谱AI开放平台](https://open.bigmodel.cn/)

