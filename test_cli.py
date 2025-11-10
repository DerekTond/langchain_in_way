"""
命令行测试工具
用于验证流式Agent的功能
"""
import sys
import json
import requests
from typing import Optional


class Colors:
    """终端颜色"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_colored(text: str, color: str = Colors.ENDC):
    """打印彩色文本"""
    print(f"{color}{text}{Colors.ENDC}")


def test_health(base_url: str = "http://localhost:8000"):
    """测试健康检查接口"""
    print_colored("\n=== 测试健康检查接口 ===", Colors.HEADER)
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print_colored("✓ 健康检查通过", Colors.OKGREEN)
            print(f"响应: {response.json()}")
            return True
        else:
            print_colored(f"✗ 健康检查失败: {response.status_code}", Colors.FAIL)
            return False
    except requests.exceptions.ConnectionError:
        print_colored("✗ 无法连接到服务器，请确保服务已启动", Colors.FAIL)
        return False
    except Exception as e:
        print_colored(f"✗ 错误: {str(e)}", Colors.FAIL)
        return False


def test_chat(base_url: str = "http://localhost:8000", user_id: str = "test_user", 
              session_id: str = "test_session", message: str = "请生成一道Python编程题"):
    """测试非流式对话接口"""
    print_colored("\n=== 测试非流式对话接口 ===", Colors.HEADER)
    try:
        url = f"{base_url}/chat"
        data = {
            "user_id": user_id,
            "session_id": session_id,
            "message": message
        }
        print(f"请求: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        response = requests.post(url, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print_colored("✓ 对话成功", Colors.OKGREEN)
            print_colored("\nAI回复:", Colors.OKCYAN)
            print(result.get("content", ""))
            return True
        else:
            print_colored(f"✗ 请求失败: {response.status_code}", Colors.FAIL)
            print(f"错误信息: {response.text}")
            return False
    except Exception as e:
        print_colored(f"✗ 错误: {str(e)}", Colors.FAIL)
        return False


def test_chat_stream(base_url: str = "http://localhost:8000", user_id: str = "test_user",
                     session_id: str = "test_session", message: str = "请生成一道Python编程题"):
    """测试流式对话接口"""
    print_colored("\n=== 测试流式对话接口 ===", Colors.HEADER)
    try:
        url = f"{base_url}/chat/stream"
        data = {
            "user_id": user_id,
            "session_id": session_id,
            "message": message
        }
        print(f"请求: {json.dumps(data, ensure_ascii=False, indent=2)}")
        print_colored("\n流式输出:", Colors.OKCYAN)
        
        response = requests.post(url, json=data, stream=True, timeout=60)
        if response.status_code == 200:
            full_content = ""
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # 去掉 'data: ' 前缀
                        try:
                            data_obj = json.loads(data_str)
                            if data_obj.get('type') == 'chunk':
                                chunk = data_obj.get('content', '')
                                print(chunk, end='', flush=True)
                                full_content += chunk
                            elif data_obj.get('type') == 'done':
                                print_colored("\n\n✓ 流式对话完成", Colors.OKGREEN)
                                break
                            elif data_obj.get('type') == 'error':
                                print_colored(f"\n✗ 错误: {data_obj.get('error')}", Colors.FAIL)
                                return False
                        except json.JSONDecodeError:
                            pass
            
            print_colored(f"\n\n完整内容长度: {len(full_content)} 字符", Colors.OKBLUE)
            return True
        else:
            print_colored(f"✗ 请求失败: {response.status_code}", Colors.FAIL)
            print(f"错误信息: {response.text}")
            return False
    except Exception as e:
        print_colored(f"✗ 错误: {str(e)}", Colors.FAIL)
        return False


def test_create_session(base_url: str = "http://localhost:8000", 
                        user_id: str = "test_user", session_id: Optional[str] = None):
    """测试创建会话接口"""
    print_colored("\n=== 测试创建会话接口 ===", Colors.HEADER)
    try:
        url = f"{base_url}/session/create"
        data = {"user_id": user_id}
        if session_id:
            data["session_id"] = session_id
        
        print(f"请求: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        response = requests.post(url, json=data, timeout=5)
        if response.status_code == 200:
            result = response.json()
            print_colored("✓ 会话创建成功", Colors.OKGREEN)
            print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            return result.get("session_id")
        else:
            print_colored(f"✗ 请求失败: {response.status_code}", Colors.FAIL)
            print(f"错误信息: {response.text}")
            return None
    except Exception as e:
        print_colored(f"✗ 错误: {str(e)}", Colors.FAIL)
        return None


def test_get_history(base_url: str = "http://localhost:8000", 
                     user_id: str = "test_user", session_id: str = "test_session"):
    """测试获取会话历史接口"""
    print_colored("\n=== 测试获取会话历史接口 ===", Colors.HEADER)
    try:
        url = f"{base_url}/session/{user_id}/{session_id}"
        
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            result = response.json()
            print_colored("✓ 获取历史成功", Colors.OKGREEN)
            print(f"消息数量: {len(result.get('messages', []))}")
            for i, msg in enumerate(result.get('messages', []), 1):
                role_color = Colors.OKCYAN if msg['role'] == 'user' else Colors.OKGREEN
                print_colored(f"\n[{i}] {msg['role']}:", role_color)
                print(msg['content'])
            return True
        else:
            print_colored(f"✗ 请求失败: {response.status_code}", Colors.FAIL)
            print(f"错误信息: {response.text}")
            return False
    except Exception as e:
        print_colored(f"✗ 错误: {str(e)}", Colors.FAIL)
        return False


def interactive_chat(base_url: str = "http://localhost:8000", 
                     user_id: str = "interactive_user", session_id: str = "interactive_session"):
    """交互式聊天"""
    print_colored("\n=== 交互式聊天模式 ===", Colors.HEADER)
    print_colored("输入消息与AI对话，输入 'quit' 或 'exit' 退出", Colors.OKBLUE)
    print_colored("输入 'stream' 切换到流式模式，输入 'normal' 切换回普通模式\n", Colors.OKBLUE)
    
    use_stream = False
    
    while True:
        try:
            # 获取用户输入
            user_input = input(f"{Colors.OKCYAN}你: {Colors.ENDC}").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print_colored("再见！", Colors.OKGREEN)
                break
            
            if user_input.lower() == 'stream':
                use_stream = True
                print_colored("已切换到流式模式", Colors.OKGREEN)
                continue
            
            if user_input.lower() == 'normal':
                use_stream = False
                print_colored("已切换到普通模式", Colors.OKGREEN)
                continue
            
            # 发送请求
            if use_stream:
                print_colored(f"\nAI ({'流式' if use_stream else '普通'}): ", Colors.OKGREEN)
                test_chat_stream(base_url, user_id, session_id, user_input)
            else:
                print_colored(f"\nAI ({'流式' if use_stream else '普通'}): ", Colors.OKGREEN)
                test_chat(base_url, user_id, session_id, user_input)
            
            print()  # 空行
            
        except KeyboardInterrupt:
            print_colored("\n\n再见！", Colors.OKGREEN)
            break
        except Exception as e:
            print_colored(f"错误: {str(e)}", Colors.FAIL)


def run_all_tests(base_url: str = "http://localhost:8000"):
    """运行所有测试"""
    print_colored("=" * 50, Colors.BOLD)
    print_colored("开始测试流式Agent API", Colors.BOLD)
    print_colored("=" * 50, Colors.BOLD)
    
    # 测试健康检查
    if not test_health(base_url):
        print_colored("\n服务未启动，请先启动服务：", Colors.WARNING)
        print("  python api.py")
        print("  或")
        print("  uv run python api.py")
        return
    
    # 测试创建会话
    session_id = test_create_session(base_url, "test_user", "test_session")
    if not session_id:
        session_id = "test_session"
    
    # 测试非流式对话
    test_chat(base_url, "test_user", session_id, "请生成一道简单的Python编程题")
    
    # 测试流式对话
    test_chat_stream(base_url, "test_user", session_id, "请生成一道关于列表操作的Python编程题")
    
    # 测试获取历史
    test_get_history(base_url, "test_user", session_id)
    
    print_colored("\n" + "=" * 50, Colors.BOLD)
    print_colored("所有测试完成", Colors.BOLD)
    print_colored("=" * 50, Colors.BOLD)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="流式Agent命令行测试工具")
    parser.add_argument("--url", default="http://localhost:8000", help="API基础URL")
    parser.add_argument("--user-id", default="test_user", help="用户ID")
    parser.add_argument("--session-id", default="test_session", help="会话ID")
    parser.add_argument("--message", help="要发送的消息（用于单次测试）")
    parser.add_argument("--stream", action="store_true", help="使用流式接口")
    parser.add_argument("--interactive", "-i", action="store_true", help="交互式聊天模式")
    parser.add_argument("--test", action="store_true", help="运行所有测试")
    
    args = parser.parse_args()
    
    if args.interactive:
        interactive_chat(args.url, args.user_id, args.session_id)
    elif args.test:
        run_all_tests(args.url)
    elif args.message:
        if args.stream:
            test_chat_stream(args.url, args.user_id, args.session_id, args.message)
        else:
            test_chat(args.url, args.user_id, args.session_id, args.message)
    else:
        # 默认运行所有测试
        run_all_tests(args.url)
        print_colored("\n提示: 使用 --interactive 或 -i 进入交互式聊天模式", Colors.OKBLUE)


if __name__ == "__main__":
    main()

