
class SimpleUser:
    """
    Упрощённое представление аутентифицированного пользователя.
    Содержит идентификатор (id), имя пользователя (username) и признак is_authenticated.
    """
    def __init__(self, payload):
        self.id = payload.get('user_id')
        self.username = payload.get('username')
        self.is_authenticated = True


class AnonymousUser:
    """
    Класс для представления неаутентифицированного (анонимного) пользователя.
    Содержит признак is_authenticated, равный False.
    """
    def __init__(self):
        self.is_authenticated = False
