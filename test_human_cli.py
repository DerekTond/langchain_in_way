"""
Human-in-the-Loop 命令行测试工具
测试人工审核工作流
"""
import requests
import argparse
import sys
import json
import uuid


BASE_URL = "http://localhost:8000"


def print_json(data):
    """格式化打印JSON"""
    print(json.dumps(data, indent=2, ensure_ascii=False))


def test_health():
    """测试健康检查"""
    print("\n=== 测试健康检查 ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"状态码: {response.status_code}")
    print_json(response.json())
    return response.status_code == 200


def create_session(user_id: str, session_id: str = None):
    """创建会话"""
    print(f"\n=== 创建会话: {user_id} ===")
    data = {"user_id": user_id}
    if session_id:
        data["session_id"] = session_id

    response = requests.post(f"{BASE_URL}/session/create", json=data)
    print(f"状态码: {response.status_code}")
    print_json(response.json())
    return response.json()


def get_session_status(user_id: str, session_id: str):
    """获取会话状态"""
    print(f"\n=== 获取会话状态: {user_id}/{session_id} ===")
    response = requests.get(f"{BASE_URL}/session/{user_id}/{session_id}/status")
    print(f"状态码: {response.status_code}")
    print_json(response.json())
    return response.json()


def generate_content(user_id: str, session_id: str, message: str):
    """生成内容"""
    print(f"\n=== 生成内容 ===")
    print(f"用户消息: {message}")

    data = {
        "user_id": user_id,
        "session_id": session_id,
        "message": message
    }

    response = requests.post(f"{BASE_URL}/chat/generate", json=data)
    print(f"状态码: {response.status_code}")
    result = response.json()
    print_json(result)
    return result


def approve_content(user_id: str, session_id: str, reason: str = ""):
    """批准内容"""
    print(f"\n=== 批准内容 ===")

    data = {
        "user_id": user_id,
        "session_id": session_id,
        "approved": True,
        "reason": reason
    }

    response = requests.post(f"{BASE_URL}/approval/approve", json=data)
    print(f"状态码: {response.status_code}")
    print_json(response.json())
    return response.json()


def reject_content(user_id: str, session_id: str, reason: str = ""):
    """拒绝内容"""
    print(f"\n=== 拒绝内容 ===")
    print(f"拒绝原因: {reason}")

    data = {
        "user_id": user_id,
        "session_id": session_id,
        "approved": False,
        "reason": reason
    }

    response = requests.post(f"{BASE_URL}/approval/reject", json=data)
    print(f"状态码: {response.status_code}")
    print_json(response.json())
    return response.json()


def request_revision(user_id: str, session_id: str, feedback: str = ""):
    """请求修订"""
    print(f"\n=== 请求修订 ===")
    print(f"修订反馈: {feedback}")

    data = {
        "user_id": user_id,
        "session_id": session_id,
        "feedback": feedback
    }

    response = requests.post(f"{BASE_URL}/approval/revise", json=data)
    print(f"状态码: {response.status_code}")
    print_json(response.json())
    return response.json()


def regenerate_content(user_id: str, session_id: str):
    """重新生成内容"""
    print(f"\n=== 重新生成内容 ===")

    data = {
        "user_id": user_id,
        "session_id": session_id,
        "message": ""  # 使用之前的反馈
    }

    response = requests.post(f"{BASE_URL}/chat/regenerate", json=data)
    print(f"状态码: {response.status_code}")
    print_json(response.json())
    return response.json()


def list_sessions(user_id: str = None):
    """列出会话"""
    print(f"\n=== 列出会话 ===")

    url = f"{BASE_URL}/sessions"
    if user_id:
        url += f"?user_id={user_id}"

    response = requests.get(url)
    print(f"状态码: {response.status_code}")
    print_json(response.json())
    return response.json()


def run_full_workflow():
    """运行完整的工作流测试"""
    print("\n" + "=" * 50)
    print("Human-in-the-Loop 工作流测试")
    print("=" * 50)

    # 生成测试ID
    user_id = f"user_test_{uuid.uuid4().hex[:8]}"
    session_id = f"session_test_{uuid.uuid4().hex[:8]}"

    # 1. 健康检查
    if not test_health():
        print("健康检查失败！")
        return False

    # 2. 创建会话
    session = create_session(user_id, session_id)
    session_id = session["session_id"]

    # 3. 生成内容
    result = generate_content(
        user_id,
        session_id,
        "请生成一道Python编程题，主题是关于列表操作的"
    )

    # 4. 查看状态
    status = get_session_status(user_id, session_id)

    # 5. 拒绝内容
    print("\n--- 测试拒绝流程 ---")
    reject_content(user_id, session_id, "题目太简单了，需要更难一点")

    # 6. 重新生成
    regenerate_content(user_id, session_id)

    # 7. 请求修订
    print("\n--- 测试修订流程 ---")
    request_revision(user_id, session_id, "请添加题目要求")

    # 8. 重新生成
    regenerate_content(user_id, session_id)

    # 9. 批准内容
    print("\n--- 测试批准流程 ---")
    approve_content(user_id, session_id)

    # 10. 查看最终状态
    get_session_status(user_id, session_id)

    # 11. 列出会话
    list_sessions(user_id)

    print("\n" + "=" * 50)
    print("测试完成！")
    print("=" * 50)
    return True


def interactive_mode():
    """交互式模式"""
    print("\n=== Human-in-the-Loop 交互模式 ===")
    print("输入 'help' 查看命令列表")

    user_id = f"user_interactive_{uuid.uuid4().hex[:8]}"
    session_id = None

    while True:
        try:
            cmd = input(f"\n[{user_id}] > ").strip()

            if not cmd:
                continue

            if cmd.lower() in ["quit", "exit", "q"]:
                print("退出交互模式")
                break

            elif cmd.lower() == "help":
                print("""
可用命令:
  session [session_id]    - 创建或切换会话
  status                  - 查看当前会话状态
  gen <message>           - 生成内容
  approve [reason]        - 批准待审核内容
  reject <reason>         - 拒绝待审核内容
  revise <feedback>       - 请求修订
  regen                   - 重新生成内容
  list                    - 列出所有会话
  help                    - 显示帮助
  quit/exit/q             - 退出
                """)

            elif cmd.lower().startswith("session"):
                parts = cmd.split(maxsplit=1)
                sid = parts[1] if len(parts) > 1 else None
                result = create_session(user_id, sid)
                session_id = result["session_id"]

            elif cmd.lower() == "status":
                if session_id:
                    get_session_status(user_id, session_id)
                else:
                    print("请先创建会话")

            elif cmd.lower().startswith("gen "):
                if not session_id:
                    print("请先创建会话")
                    continue
                message = cmd[4:].strip()
                generate_content(user_id, session_id, message)

            elif cmd.lower().startswith("approve"):
                if not session_id:
                    print("请先创建会话")
                    continue
                parts = cmd.split(maxsplit=1)
                reason = parts[1] if len(parts) > 1 else ""
                approve_content(user_id, session_id, reason)

            elif cmd.lower().startswith("reject"):
                if not session_id:
                    print("请先创建会话")
                    continue
                parts = cmd.split(maxsplit=1)
                reason = parts[1] if len(parts) > 1 else "内容不符合要求"
                reject_content(user_id, session_id, reason)

            elif cmd.lower().startswith("revise"):
                if not session_id:
                    print("请先创建会话")
                    continue
                parts = cmd.split(maxsplit=1)
                feedback = parts[1] if len(parts) > 1 else ""
                request_revision(user_id, session_id, feedback)

            elif cmd.lower() == "regen":
                if not session_id:
                    print("请先创建会话")
                    continue
                regenerate_content(user_id, session_id)

            elif cmd.lower() == "list":
                list_sessions(user_id)

            else:
                print(f"未知命令: {cmd}，输入 'help' 查看帮助")

        except KeyboardInterrupt:
            print("\n退出交互模式")
            break
        except Exception as e:
            print(f"错误: {e}")


def main():
    parser = argparse.ArgumentParser(description="Human-in-the-Loop API测试工具")
    parser.add_argument("--url", default=BASE_URL, help="API基础URL")
    parser.add_argument("--test", action="store_true", help="运行完整测试")
    parser.add_argument("--interactive", "-i", action="store_true", help="交互式模式")

    args = parser.parse_args()

    global BASE_URL
    BASE_URL = args.url

    if args.test:
        run_full_workflow()
    elif args.interactive:
        interactive_mode()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
