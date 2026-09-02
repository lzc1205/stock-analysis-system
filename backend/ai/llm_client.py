"""
大模型客户端
支持豆包、通义千问等兼容 OpenAI 接口的模型
"""
from openai import OpenAI
from app.config import settings
from app.utils.logger import logger


class LLMClient:
    def __init__(self):
        self.client = None
        self._init_client()

    def _init_client(self):
        if not settings.llm_api_key:
            logger.warning("LLM API Key 未配置，AI 问答功能不可用")
            return

        self.client = OpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
        )

    def chat(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """
        调用大模型进行对话
        :param messages: 对话消息列表
        :param temperature: 温度参数
        :param max_tokens: 最大 token 数
        :return: 模型回复内容
        """
        if not self.client:
            return "AI 服务未配置，请检查 LLM_API_KEY 环境变量"

        try:
            response = self.client.chat.completions.create(
                model=settings.llm_model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"大模型调用失败: {e}")
            return f"AI 服务调用失败: {str(e)}"


llm_client = LLMClient()