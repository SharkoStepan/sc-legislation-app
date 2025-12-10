class ScServerError (Exception ):
    """
    Класс для представления исключения при недоступном sc-сервере
    """
    message ="Failed to connect to SC-server! Goodbye."

class APIError (Exception ):
    """
    Класс для представления исключения при ошибке клиента
    """
    code =400 
    message ="A client error occurred."
    description =None 

    def __init__ (self ,code =None ,message =None ,description =None ):
        if code is not None :
            self .code =code 
        if message is not None :
            self .message =message 
        if description is not None :
            self .description =description 

    def to_dict (self ):
        """
        Метод для вывода ошибки в виде поиска
        :return: Ошибка в виде словаря
        """
        return {
        "error":self .__class__ .__name__ ,
        "message":self .message ,
        "description":self .description ,
        }


class FieldRequiredError (APIError ):
    """
    Класс для представления исключения при отсутствии введенного обязательного поля
    """
    message ="A required field is missing."
    description ={"field":"Specify the field name causing the error."}


class AgentError (APIError ):
    """
    Класс для представления исключения при ошибке вызова агента
    """
    code =500 
    message ="An unexpected agent error"

class ParseDataError (APIError ):
    """
    Класс для представления исключения при ошибке парсинга данных
    """
    code =666 
    message ="An unexpected input data"