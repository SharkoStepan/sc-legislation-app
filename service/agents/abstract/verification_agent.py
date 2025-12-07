from abc import ABC, abstractmethod
from enum import StrEnum


class VerificationStatus(StrEnum):
    """
    Перечисление для представления статусов результата выполнения агента верификации
    """
    VALID = "Valid"
    INVALID = "Invalid"
    TOKEN_SENT = "TokenSent"
    EMAIL_VERIFIED = "EmailVerified"


class VerificationAgent(ABC):
    """
    Абстрактный класс для реализации агента верификации
    """
    
    @abstractmethod
    def send_token(self, email: str) -> dict:
        """
        Абстрактный метод для отправки токена верификации
        
        :param email: Email пользователя для отправки токена
        :return: Словарь со статусом результата выполнения
        """
        pass
    
    @abstractmethod
    def verify_token(self, email: str, token: str) -> dict:
        """
        Абстрактный метод для проверки токена верификации
        
        :param email: Email пользователя
        :param token: Токен для проверки
        :return: Словарь со статусом результата выполнения
        """
        pass
