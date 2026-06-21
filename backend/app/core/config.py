from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = 'Tradex API'
    app_version: str = '0.1.0'
    api_prefix: str = '/api'
    llm_provider: str = 'mock'
    openai_api_key: str = Field(default='', validation_alias=AliasChoices('OPENAI_API_KEY', 'LLM_API_KEY'))
    openai_base_url: str = Field(
        default='https://api.openai.com/v1',
        validation_alias=AliasChoices('OPENAI_BASE_URL', 'LLM_BASE_URL'),
    )
    openai_model: str = Field(default='gpt-4o-mini', validation_alias=AliasChoices('OPENAI_MODEL', 'LLM_MODEL'))
    database_url: str = 'sqlite:///./data/app.db'
    frontend_origin: str = 'http://localhost:5173'
    max_context_messages: int = 12
    agent_max_steps: int = 8
    agent_log_level: str = 'INFO'

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[3] / '.env'),
        env_file_encoding='utf-8',
        extra='ignore',
    )

    @property
    def active_model(self) -> str:
        return self.openai_model

    @property
    def active_base_url(self) -> str:
        return self.openai_base_url

    @property
    def active_api_key(self) -> str:
        return self.openai_api_key


@lru_cache
def get_settings() -> Settings:
    return Settings()
