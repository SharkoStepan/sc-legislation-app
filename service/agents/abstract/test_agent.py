from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Optional

class TestStatus(StrEnum):
    """Статусы выполнения тестовых агентов"""
    VALID = "valid"
    INVALID = "invalid"
    
class TestAgent(ABC):
    """Базовый класс для тестовых агентов"""
    
    @abstractmethod
    def get_next_question(self, user_addr) -> dict:
        """Получить следующий вопрос для пользователя"""
        pass
    
    @abstractmethod
    def get_answers_for_question(self, question_addr) -> dict:
        """Получить варианты ответов для вопроса"""
        pass
    
    @abstractmethod
    def save_answer(self, answer_addr, user_addr) -> dict:
        """Сохранить ответ пользователя"""
        pass
    
    @abstractmethod
    def check_answer(self, question_addr, user_addr) -> dict:
        """Проверить правильность ответа"""
        pass
    
    @abstractmethod
    def delete_old_test_data(self, user_addr) -> dict:
        """Удалить старые данные теста"""
        pass
    
    @abstractmethod
    def update_rating(self, user_addr) -> dict:
        """Обновить рейтинг пользователя"""
        pass
