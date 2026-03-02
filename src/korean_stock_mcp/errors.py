class KoreanStockMcpError(Exception):
    def __init__(self, code: str, message: str, data: dict | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data or {}

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "message": self.message,
            "data": self.data,
        }
