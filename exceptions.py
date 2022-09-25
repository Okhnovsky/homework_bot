class APIErrException(Exception):
    """Ошибка доступа к API ЯП"""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message


class NotSendMessage(Exception):
    """Сообщение не отправлено"""
    pass
