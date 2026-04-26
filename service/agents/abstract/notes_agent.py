from abc import ABC, abstractmethod
from enum import StrEnum


class NotesStatus(StrEnum):
    """
    Перечисление для представления статусов результата выполнения агента заметок
    """
    VALID = "Valid"
    INVALID = "Invalid"
    ERROR = "Error"


class NotesAgent(ABC):
    """
    Абстрактный класс для реализации агента заметок
    """

    @abstractmethod
    def get_notes(self, user_email: str) -> dict:
        """
        Получить заметки пользователя
        :param user_email: Email пользователя
        :return: Словарь с заметками
        """
        pass

    @abstractmethod
    def add_note(self, user_email: str, article_id: str,
                 article_title: str, text: str) -> dict:
        """
        Добавить заметку
        :param user_email: Email пользователя
        :param article_id: ID статьи
        :param article_title: Название статьи
        :param text: Текст заметки
        :return: Словарь со статусом операции
        """
        pass

    @abstractmethod
    def update_note(self, user_email: str, note_id: str, text: str) -> dict:
        """
        Обновить заметку
        :param user_email: Email пользователя
        :param note_id: ID заметки
        :param text: Новый текст
        :return: Словарь со статусом операции
        """
        pass

    @abstractmethod
    def delete_note(self, user_email: str, note_id: str) -> dict:
        """
        Удалить заметку
        :param user_email: Email пользователя
        :param note_id: ID заметки
        :return: Словарь со статусом операции
        """
        pass
