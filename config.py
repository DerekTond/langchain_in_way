"""
配置管理模块
从环境变量读取GLM API配置
"""
import os
from typing import Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """配置类"""
    
    # GLM API配置
    GLM_API_KEY: str = os.getenv("GLM_API_KEY", "")
    GLM_BASE_URL: str = os.getenv("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4/")
    GLM_MODEL: str = os.getenv("GLM_MODEL", "glm-4")
    
    # 流式输出配置
    STREAMING: bool = True
    
    # 温度参数
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
    
    # 深度思考配置（GLM特有）
    # 设置为 "disabled" 关闭深度思考，减少响应时间
    # 可选值: "disabled" 或 None（启用深度思考）
    THINKING_TYPE: Optional[str] = os.getenv("THINKING_TYPE", "disabled")
    
    @classmethod
    def validate(cls) -> None:
        """验证配置是否完整"""
        if not cls.GLM_API_KEY:
            raise ValueError("GLM_API_KEY环境变量未设置，请在.env文件中配置")


# 验证配置
try:
    Config.validate()
except ValueError as e:
    print(f"警告: {e}")

