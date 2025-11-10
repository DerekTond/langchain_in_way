# API curl 命令参考

本文档提供所有API接口的curl命令示例，可用于配置Postman。

**基础URL**: `http://localhost:8000`

---

## 1. 流式对话接口

### POST `/chat/stream`

流式对话接口，使用Server-Sent Events (SSE)格式返回响应。

**curl命令：**

```bash
curl -X POST "http://localhost:8000/chat/stream" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "user_id": "user123",
    "session_id": "session456",
    "message": "请生成一道Python编程题"
  }'
```

**Postman配置：**
- Method: `POST`
- URL: `http://localhost:8000/chat/stream`
- Headers:
  - `Content-Type: application/json`
  - `Accept: text/event-stream`
- Body (raw JSON):
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

---

## 2. 非流式对话接口

### POST `/chat`

同步对话接口，返回完整响应。

**curl命令：**

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "session_id": "session456",
    "message": "请生成一道Python编程题"
  }'
```

**Postman配置：**
- Method: `POST`
- URL: `http://localhost:8000/chat`
- Headers:
  - `Content-Type: application/json`
- Body (raw JSON):
```json
{
  "user_id": "user123",
  "session_id": "session456",
  "message": "请生成一道Python编程题"
}
```

**响应示例：**
```json
{
  "content": "完整AI回复内容"
}
```

---

## 3. 创建会话

### POST `/session/create`

创建新会话。

**curl命令：**

```bash
curl -X POST "http://localhost:8000/session/create" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "session_id": "session456"
  }'
```

**不指定session_id（自动生成）：**

```bash
curl -X POST "http://localhost:8000/session/create" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123"
  }'
```

**Postman配置：**
- Method: `POST`
- URL: `http://localhost:8000/session/create`
- Headers:
  - `Content-Type: application/json`
- Body (raw JSON):
```json
{
  "user_id": "user123",
  "session_id": "session456"
}
```

**响应示例：**
```json
{
  "user_id": "user123",
  "session_id": "session456",
  "message": "会话创建成功"
}
```

---

## 4. 获取会话历史

### GET `/session/{user_id}/{session_id}`

获取指定会话的消息历史。

**curl命令：**

```bash
curl -X GET "http://localhost:8000/session/user123/session456" \
  -H "Accept: application/json"
```

**Postman配置：**
- Method: `GET`
- URL: `http://localhost:8000/session/user123/session456`
- Headers:
  - `Accept: application/json`

**响应示例：**
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

---

## 5. 删除会话

### DELETE `/session/{user_id}/{session_id}`

删除指定会话。

**curl命令：**

```bash
curl -X DELETE "http://localhost:8000/session/user123/session456" \
  -H "Accept: application/json"
```

**Postman配置：**
- Method: `DELETE`
- URL: `http://localhost:8000/session/user123/session456`
- Headers:
  - `Accept: application/json`

**响应示例：**
```json
{
  "message": "会话删除成功"
}
```

---

## 6. 根路径

### GET `/`

获取API基本信息。

**curl命令：**

```bash
curl -X GET "http://localhost:8000/" \
  -H "Accept: application/json"
```

**Postman配置：**
- Method: `GET`
- URL: `http://localhost:8000/`

**响应示例：**
```json
{
  "message": "流式Agent API",
  "version": "1.0.0",
  "docs": "/docs"
}
```

---

## 7. 健康检查

### GET `/health`

健康检查接口。

**curl命令：**

```bash
curl -X GET "http://localhost:8000/health" \
  -H "Accept: application/json"
```

**Postman配置：**
- Method: `GET`
- URL: `http://localhost:8000/health`

**响应示例：**
```json
{
  "status": "healthy"
}
```

---

## Postman 快速导入

### 方法1：手动创建Collection

1. 打开Postman
2. 点击 "New" -> "Collection"
3. 命名为 "流式Agent API"
4. 按照上面的配置逐个添加请求

### 方法2：使用环境变量

在Postman中创建环境变量：
- `base_url`: `http://localhost:8000`
- `user_id`: `user123`
- `session_id`: `session456`

然后在URL中使用：`{{base_url}}/chat`

### 方法3：完整请求示例（JSON格式）

可以创建一个Postman Collection JSON文件，包含所有请求。以下是关键请求的JSON格式：

```json
{
  "info": {
    "name": "流式Agent API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "流式对话",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          },
          {
            "key": "Accept",
            "value": "text/event-stream"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"user_id\": \"user123\",\n  \"session_id\": \"session456\",\n  \"message\": \"请生成一道Python编程题\"\n}"
        },
        "url": {
          "raw": "http://localhost:8000/chat/stream",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["chat", "stream"]
        }
      }
    },
    {
      "name": "非流式对话",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"user_id\": \"user123\",\n  \"session_id\": \"session456\",\n  \"message\": \"请生成一道Python编程题\"\n}"
        },
        "url": {
          "raw": "http://localhost:8000/chat",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["chat"]
        }
      }
    }
  ]
}
```

---

## 注意事项

1. **流式接口**：`/chat/stream` 返回的是SSE格式，在Postman中可能显示为持续流式数据
2. **会话管理**：每次对话需要提供 `user_id` 和 `session_id`，相同ID会复用会话历史
3. **Content-Type**：所有POST请求都需要设置 `Content-Type: application/json`
4. **端口**：默认端口是8000，如果修改了端口，请相应更新URL

---

## 测试流程建议

1. 首先调用 `/health` 确认服务正常
2. 调用 `/session/create` 创建会话（或直接使用任意ID）
3. 调用 `/chat` 或 `/chat/stream` 进行对话
4. 调用 `/session/{user_id}/{session_id}` 查看会话历史
5. 测试完成后可调用 `/session/{user_id}/{session_id}` DELETE删除会话

