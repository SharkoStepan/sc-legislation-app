from flask import current_app

from service.agents.abstract.auth_agent import AuthAgent
from service.agents.abstract.reg_agent import RegAgent
from service.agents.abstract.user_request_agent import RequestAgent
from service.agents.abstract.directory_agent import DirectoryAgent
from service.agents.abstract.event_agents import AddEventAgent, DeleteEventAgent, ShowEventAgent

from sc_client.models import ScAddr, ScIdtfResolveParams
from sc_client.constants import sc_types
import sc_client.client as client
from .agents.ostis import OstisVerificationAgent


from .agents.ostis import OstisAuthAgent, OstisRegAgent, OstisVerificationAgent

# Инициализация агентов
auth_agent_instance = OstisAuthAgent()
reg_agent_instance = OstisRegAgent()
verification_agent_instance = OstisVerificationAgent()


def auth_agent(username: str, password: str):
    """
    Аутентификация пользователя
    
    :param username: Email пользователя
    :param password: Пароль
    :return: Результат аутентификации
    """
    return auth_agent_instance.auth_agent(username, password)


def reg_agent(
    email: str,
    password: str,
    password_conf: str,
    user_type: str,
    full_name: str = None,
    gender: str = None,
    age: str = None,
    experience: str = None,
    field: str = None
):
    """
    Регистрация пользователя
    """
    return reg_agent_instance.reg_agent(
        email=email,
        password=password,
        password_conf=password_conf,
        user_type=user_type,
        full_name=full_name,
        gender=gender,
        age=age,
        experience=experience,
        field=field
    )


def verification_send_token(email: str):
    """
    Отправка токена верификации
    """
    return verification_agent_instance.send_token(email)


def verification_check_token(email: str, token: str):
    """
    Проверка токена верификации
    """
    return verification_agent_instance.verify_token(email, token)


def user_request_agent(content: str):
    """
    Метод для запуска агента юридических запросов
    :param content: Контент, по которому происходит поиск в БЗ
    :return: Словарь со статусом результата выполнения агента аутентификации
    """
    agent: RequestAgent = current_app.config['agents']['user_request_agent']
    return agent.request_agent(content)

def directory_agent(content: str):
    """
    Метод для запуска агента поиска
    :param content: Контент, по которому происходит поиск в БЗ
    :return: Словарь со статусом результата выполнения агента аутентификации
    """
    agent: DirectoryAgent = current_app.config['agents']['directory_agent']
    return agent.directory_agent(
        content=content
        )

def add_event_agent(user_name, event_name: str, event_date, event_description: str):
    """
    Метод для запуска агента добавления события
    :param user_name: Логин пользователя
    :param event_name: Название события
    :param event_date: Дата события
    :param event_description: Описание события
    :return: Словарь со статусом результата выполнения агента добавления события
    """
    agent: AddEventAgent = current_app.config['agents']['add_event_agent']
    return agent.add_event_agent(
        user_name=user_name,
        event_name=event_name,
        event_date=event_date,
        event_description=event_description
    )

def delete_event_agent(username: str, event_name: str):
    """
    Метод для запуска агента удаления события
    :param username: Логин пользователя
    :param event_name: Название события
    :return: Словарь со статусом результата выполнения агента удаления события
    """
    agent: DeleteEventAgent = current_app.config['agents']['delete_event_agent']
    return agent.delete_event_agent(
        username=username,
        event_name=event_name
    )

def show_event_agent(username):
    """
    Метод для запуска агента просмотра события
    :param username: Логин пользователя
    :return: Словарь со статусом результата выполнения агента просмотра события
    """
    agent: ShowEventAgent = current_app.config['agents']['show_event_agent']
    return agent.show_event_agent(
        username=username
    )


def test_agent_get_question(user_id: str):
    """Получить следующий вопрос"""
    agent = current_app.config['agents']['test_agent']
    return agent.get_next_question(user_id)


def test_agent_get_answers(question_addr):
    """Получить варианты ответов"""
    agent = current_app.config['agents']['test_agent']
    return agent.get_answers_for_question(question_addr)


def test_agent_save_answer(answer_id, user_id: str):
    """Сохранить ответ пользователя"""
    # answer_id уже ScAddr, не нужно конвертировать
    agent = current_app.config['agents']['test_agent']
    return agent.save_answer(user_id, answer_id)



def test_agent_check_answer(question_id, user_id: str):
    """Проверить ответ"""
    # question_id уже ScAddr, не нужно конвертировать
    agent = current_app.config['agents']['test_agent']
    return agent.check_answer(user_id, question_id)



def test_agent_delete_old_data(user_id: str):
    """Удалить старые данные теста"""
    agent = current_app.config['agents']['test_agent']
    return agent.delete_old_test_data(user_id)


def test_agent_update_rating(user_id: str):
    """Обновить рейтинг пользователя"""
    agent = current_app.config['agents']['test_agent']
    return agent.update_rating(user_id)
