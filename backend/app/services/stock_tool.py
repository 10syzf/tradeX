class StockToolService:
    def get_status(self) -> dict[str, str]:
        return {
            'status': 'not_connected',
            'message': '股票实时行情工具尚未接入，当前仅提供通用模型问答。',
        }
