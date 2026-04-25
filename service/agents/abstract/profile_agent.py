from abc import ABC, abstractmethod
from enum import StrEnum


class ProfileStatus(StrEnum):
    """
    Перечисление для представления статусов результата выполнения агента профиля
    """
    VALID = "Valid"
    INVALID = "Invalid"
    ERROR = "Error"


class ProfileAgent(ABC):
    """
    Абстрактный класс для реализации агента профиля пользователя
    """

    @abstractmethod
    def get_profile(self, user_email: str) -> dict:
        """
        Получить данные профиля пользователя
        :param user_email: Email пользователя
        :return: Словарь с данными профиля
        """
        pass

    @abstractmethod
    def update_profile(self, user_email: str, data: dict) -> dict:
        """
        Обновить данные профиля пользователя
        :param user_email: Email пользователя
        :param data: Данные для обновления
        :return: Словарь со статусом операции
        """
        pass

    @abstractmethod
    def get_settings(self, user_email: str) -> dict:
        """
        Получить настройки пользователя
        :param user_email: Email пользователя
        :return: Словарь с настройками
        """
        pass

    @abstractmethod
    def update_settings(self, user_email: str, settings: dict) -> dict:
        """
        Обновить настройки пользователя
        :param user_email: Email пользователя
        :param settings: Новые настройки
        :return: Словарь со статусом операции
        """
        pass
