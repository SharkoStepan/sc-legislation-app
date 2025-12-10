from abc import ABC ,abstractmethod 
from enum import StrEnum 


class RequestStatus (StrEnum ):
    """
    Перечисление для представления статусов результата выполнения агента юридических запросов
    """
    VALID ="valid"
    INVALID ="invalid"


class RequestAgent (ABC ):
    """
    Абстрактный класс для реализации агента юридических запросов
    """
    @abstractmethod 
    def request_agent (self ,content :str )->dict :
        """
        Абстрактный метод для запуска агента юридических запросов
        :param content: Контент, по которому происходит поиск в БЗ
        :return: Словарь со статусом результата выполнения агента юридических запросов
        """
        pass 