from abc import ABC, abstractmethod
from enum import StrEnum

class RegStatus(StrEnum):
    """
    Перечисление для представления статусов результата выполнения агента регистрации
    """
    CREATED = "Valid"
    EXISTS = "Invalid"

class UserType(StrEnum):
    """
    Перечисление для представления типов пользователей
    """
    CLIENT = "client"
    SPECIALIST = "specialist"

class RegAgent(ABC):
    """
    Абстрактный класс для реализации агента регистрации
    """
    
    @abstractmethod
    def reg_agent(
        self,
        email: str,
        password: str,
        password_conf: str,
        user_type: str,
        full_name: str = None,
        gender: str = None,
        age: str = None,
        experience: str = None,
        field: str = None
    ) -> dict:
        """
        Абстрактный метод для запуска агента регистрации
        
        :param email: Email пользователя для регистрации
        :param password: Пароль пользователя для регистрации
        :param password_conf: Подтверждение пароля
        :param user_type: Тип пользователя (client или specialist)
        :param full_name: ФИО специалиста (только для specialist)
        :param gender: Пол специалиста (только для specialist)
        :param age: Возраст специалиста (только для specialist)
        :param experience: Опыт работы специалиста (только для specialist)
        :param field: Сфера деятельности специалиста (только для specialist)
        :return: Словарь со статусом результата выполнения агента регистрации
        """
        pass
