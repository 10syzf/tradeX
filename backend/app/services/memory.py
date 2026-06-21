from app.models import MessageEntity


class MemoryService:
    def build_context(self, messages: list[MessageEntity], max_messages: int) -> list[dict[str, str]]:
        trimmed = messages[-max_messages:]
        return [{'role': item.role, 'content': item.content} for item in trimmed]
