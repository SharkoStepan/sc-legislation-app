from .abstract .auth_agent import AuthAgent ,AuthStatus 
from .abstract .reg_agent import RegAgent ,RegStatus 
from .abstract .user_request_agent import RequestAgent ,RequestStatus 
from .abstract .directory_agent import DirectoryAgent ,DirectoryStatus 
from .abstract .event_agents import (
AddEventStatus ,
AddEventAgent ,
DeleteEventStatus ,
DeleteEventAgent ,
ShowEventStatus ,
ShowEventAgent 
)
from sc_client .models import ScAddr 
class OstisAuthAgent (AuthAgent ):
    """
    Класс-заглушка для представления агента аутентификации
    """
    def auth_agent (self ,username :str ,password :str ):
        """
        Метод-заглушка для запуска агента аутентификации
        :param username: Логин пользователя для аутентификации
        :param password: Пароль пользователя для аутентификации
        :return: Словарь со статусом результата выполнения агента аутентификации
        """
        print (f"MockAgent: Pretend authenticating {username } - {password }")
        return {
        "status":AuthStatus .INVALID ,
        "message":"Invalid credentials",
        }

class OstisRegAgent (RegAgent ):
    """
    Класс-заглушка для представления агента регистрации
    """
    def reg_agent (
    self ,
    gender ,
    surname :str ,
    name :str ,
    fname :str ,
    birthdate ,
    reg_place :str ,
    username :str ,
    password :str 
    ):
        """
        Метод-заглушка для запуска агента регистрации
        :param gender: Пол пользователя для регистрации
        :param surname: Фамилия пользователя для регистрации
        :param name: Имя пользователя для регистрации
        :param fname: Отчество пользователя для регистрации
        :param birthdate: Дата рождения пользователя для регистрации
        :param reg_place: Место регистрации пользователя для регистрации
        :param username: Логин пользователя для регистрации
        :param password: Пароль пользователя для регистрации
        :return: Словарь со статусом результата выполнения агента регистрации
        """
        print (f"MockAgent: Pretend registering {gender } - {surname } - {name } - {fname } - {birthdate } - {reg_place } - {username } - {password }")
        return {"status":RegStatus .CREATED }

class OstisUserRequestAgent (RequestAgent ):
    """
    Класс-заглушка для представления агента юридических запросов
    """
    def request_agent (
    self ,
    content :str 
    ):
        """
        Метод-заглушка для запуска агента юридических запросов
        :param content: Контент, по которому происходит поиск в БЗ
        :return: Словарь со статусом результата выполнения агента юридических запросов
        """
        print (f"MockAgent: Pretend requesting {content }")
        return {"status":RequestStatus .VALID }

class OstisDirectoryAgent (DirectoryAgent ):
    """
    Класс-заглушка для представления агента поиска
    """
    def directory_agent (
    self ,
    content ,
    ):
        """
        Метод-заглушка для запуска агента поиска
        :param content: Контент, по которому происходит поиск в БЗ
        :return: Словарь со статусом результата выполнения агента поиска
        """
        print (f"MockAgent: Pretend requesting {content }")
        return {"status":DirectoryStatus .VALID }

class OstisAddEventAgent (AddEventAgent ):
    """
    Класс-заглушка для представления агента добавления события
    """
    def add_event_agent (self ,
    user_name :str ,
    event_name :str ,
    event_date ,
    event_description :str 
    ):
        """
        Метод-заглушка для запуска агента добавления события
        :param user_name: Логин пользователя
        :param event_name: Название события
        :param event_date: Дата события
        :param event_description: Описание события
        :return:
        """
        print (f"MockAgent: Pretend requesting {event_name } {event_description }")
        return {"status":AddEventStatus .VALID }

class OstisDeleteEventAgent (DeleteEventAgent ):
    """
    Класс-заглушка для представления агента удаления события
    """
    def delete_event_agent (self ,
    event_name :str ,
    ):
        """
        Метод-заглушка для запуска агента удаления события
        :param event_name: Название события
        :return:
        """
        print (f"MockAgent: Pretend requesting {event_name }")
        return {"status":DeleteEventStatus .VALID }

class OstisShowEventAgent (ShowEventAgent ):
    """
    Класс-заглушка для представления агента просмотра события
    """
    def show_event_agent (self ,
    username :str ,
    ):
        """
        Метод-заглушка для запуска агента просмотра события
        :param username: Логин пользователя
        :return:
        """
        print (f"MockAgent: Pretend requesting {username }")
        return {"status":ShowEventStatus .VALID }