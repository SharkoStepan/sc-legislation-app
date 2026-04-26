from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Optional


class HistoryStatus(StrEnum):
    """
    Перечисление для представления статусов результата выполнения агента истории
    """
    VALID = "Valid"
    INVALID = "Invalid"
    ERROR = "Error"


class HistoryAgent(ABC):
    """
    Абстрактный класс для реализации агента истории запросов
    """

    @abstractmethod
    def get_history(self, user_email: str, period: str = 'week') -> dict:
        """
        Получить историю запросов пользователя
        :param user_email: Email пользователя
        :param period: Период (week, month, all)
        :return: Словарь с историей
        """
        pass

    @abstractmethod
    def add_history_entry(self, user_email: str, query_type: str,
                          query_text: str, article_id: Optional[str] = None) -> dict:
        """
        Добавить запись в историю
        :param user_email: Email пользователя
        :param query_type: Тип запроса (search, article_view)
        :param query_text: Текст запроса
        :param article_id: ID статьи (опционально)
        :return: Словарь со статусом операции
        """
        pass

    @abstractmethod
    def clear_history(self, user_email: str) -> dict:
        """
        Очистить историю пользователя
        :param user_email: Email пользователя
        :return: Словарь со статусом операции
        """
        pass
