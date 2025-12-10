from abc import ABC ,abstractmethod 
from enum import StrEnum 


class AuthStatus (StrEnum ):
    """
    Перечисление для представления статусов результата выполнения агента аутентификации
    """
    VALID ="Valid"
    INVALID ="Invalid"


class AuthAgent (ABC ):
    """
    Абстрактный класс для реализации агента аутентификации
    """
    @abstractmethod 
    def auth_agent (self ,username :str ,password :str )->dict :
        """
        Абстрактный метод для запуска агента аутентификации
        :param username: Логин пользователя для аутентификации
        :param password: Пароль пользователя для аутентификации
        :return: Словарь со статусом результата выполнения агента аутентификации
        """
        pass 