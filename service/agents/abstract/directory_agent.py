from abc import ABC ,abstractmethod 
from enum import StrEnum 


class DirectoryStatus (StrEnum ):
    """
    Перечисление для представления статусов результата выполнения агента поиска
    """
    VALID ="Valid"
    INVALID ="Invalid"


class DirectoryAgent (ABC ):
    """
    Абстрактный класс для реализации агента поиска
    """
    @abstractmethod 
    def directory_agent (self ,content :str )->dict :
        """
        Абстрактный метод для запуска агента поиска
        :param content: Контент, по которому происходит поиск в БЗ
        :return: Словарь со статусом результата выполнения агента поиска
        """
        pass 