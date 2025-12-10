from json import JSONEncoder 

from sc_client .models import ScTemplate ,ScAddr 

class SCJSONEncoder (JSONEncoder ):
    """
    Класс для представления кодировщика в JSON-формат
    """
    def default (self ,obj ):
        """
        Метод для представления объекта в JSON-формате
        :param obj: Объект для коди
        :return: Объект в JSON-формате
        """
        print (f"Serializing: {type (obj )}")
        if isinstance (obj ,ScAddr ):
            return obj .value 
        return super ().default (obj )