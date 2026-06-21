from __future__ import annotations

from typing import Any

import httpx

from app.core.config import Settings


class LLMAdapter:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def generate_reply(self, messages: list[dict[str, str]], model: str | None = None) -> tuple[str, list[str]]:
        provider = self.settings.llm_provider.lower()

        if provider == 'mock':
            fallback = self._build_mock_reply(messages)
            return fallback, ['当前 LLM_PROVIDER=mock，返回本地模拟回复。']

        if provider != 'openai':
            raise ValueError(f'暂不支持的 LLM_PROVIDER: {self.settings.llm_provider}')

        if not self.settings.active_api_key:
            fallback = self._build_mock_reply(messages)
            return fallback, ['未检测到 OPENAI_API_KEY，当前返回本地模拟回复。']

        payload: dict[str, Any] = {
            'model': self._resolve_model_name(model),
            'messages': messages,
            'temperature': 0.7,
        }
        headers = {
            'Authorization': f'Bearer {self.settings.active_api_key}',
            'Content-Type': 'application/json',
        }
        url = f"{self.settings.active_base_url.rstrip('/')}/chat/completions"

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:500]
            raise ValueError(f'模型接口调用失败: {exc.response.status_code} {detail}') from exc
        except httpx.HTTPError as exc:
            raise ValueError(f'模型网络请求失败: {exc}') from exc

        try:
            content = data['choices'][0]['message']['content']
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError('模型返回结构不符合预期') from exc

        warnings: list[str] = []
        return content, warnings

    def _build_mock_reply(self, messages: list[dict[str, str]]) -> str:
        latest = next((item['content'] for item in reversed(messages) if item['role'] == 'user'), '')
        return (
            '这是一个本地模拟回复，用于验证前后端链路已经打通。\n\n'
            f'你刚刚的问题是：{latest}\n\n'
            '当前系统已具备会话、消息存储和模型适配层，后续可以继续接入真实股票工具、记忆系统和多模型路由。'
        )

    def _resolve_model_name(self, model: str | None) -> str:
        if model and model != 'default':
            return model
        return self.settings.active_model
