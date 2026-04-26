from abc import ABC, abstractmethod
from enum import StrEnum
from typing import List, Optional


class BookmarksStatus(StrEnum):
    """
    Перечисление для представления статусов результата выполнения агента закладок
    """
    VALID = "Valid"
    INVALID = "Invalid"
    ERROR = "Error"


class BookmarksAgent(ABC):
    """
    Абстрактный класс для реализации агента закладок
    """

    @abstractmethod
    def get_bookmarks(self, user_email: str) -> dict:
        """
        Получить закладки пользователя
        :param user_email: Email пользователя
        :return: Словарь с закладками
        """
        pass

    @abstractmethod
    def add_bookmark(self, user_email: str, article_id: str,
                     title: str, tags: Optional[List[str]] = None) -> dict:
        """
        Добавить закладку
        :param user_email: Email пользователя
        :param article_id: ID статьи
        :param title: Название статьи
        :param tags: Теги (опционально)
        :return: Словарь со статусом операции
        """
        pass

    @abstractmethod
    def update_bookmark(self, user_email: str, bookmark_id: str,
                        tags: Optional[List[str]] = None) -> dict:
        """
        Обновить закладку
        :param user_email: Email пользователя
        :param bookmark_id: ID закладки
        :param tags: Новые теги
        :return: Словарь со статусом операции
        """
        pass

    @abstractmethod
    def delete_bookmark(self, user_email: str, bookmark_id: str) -> dict:
        """
        Удалить закладку
        :param user_email: Email пользователя
        :param bookmark_id: ID закладки
        :return: Словарь со статусом операции
        """
        pass
