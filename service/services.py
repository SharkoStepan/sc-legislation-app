from flask import current_app 

from service .agents .abstract .auth_agent import AuthAgent 
from service .agents .abstract .reg_agent import RegAgent 
from service .agents .abstract .user_request_agent import RequestAgent 
from service .agents .abstract .directory_agent import DirectoryAgent 
from service .agents .abstract .event_agents import AddEventAgent ,DeleteEventAgent ,ShowEventAgent 

from sc_client .models import ScAddr ,ScIdtfResolveParams 
from sc_client .constants import sc_types 
import sc_client .client as client 
from .agents .ostis import OstisVerificationAgent 


from .agents .ostis import OstisAuthAgent ,OstisRegAgent ,OstisVerificationAgent
from .agents.ostis import OstisProfileAgent, OstisHistoryAgent, OstisBookmarksAgent, OstisNotesAgent 


auth_agent_instance =OstisAuthAgent ()
reg_agent_instance =OstisRegAgent ()
verification_agent_instance =OstisVerificationAgent ()


def auth_agent (username :str ,password :str ):
    """
    Аутентификация пользователя
    
    :param username: Email пользователя
    :param password: Пароль
    :return: Результат аутентификации
    """
    return auth_agent_instance .auth_agent (username ,password )


def reg_agent (
email :str ,
password :str ,
password_conf :str ,
user_type :str ,
full_name :str =None ,
gender :str =None ,
age :str =None ,
experience :str =None ,
field :str =None 
):
    """
    Регистрация пользователя
    """
    return reg_agent_instance .reg_agent (
    email =email ,
    password =password ,
    password_conf =password_conf ,
    user_type =user_type ,
    full_name =full_name ,
    gender =gender ,
    age =age ,
    experience =experience ,
    field =field 
    )


def verification_send_token (email :str ):
    """
    Отправка токена верификации
    """
    return verification_agent_instance .send_token (email )


def verification_check_token (email :str ,token :str ):
    """
    Проверка токена верификации
    """
    return verification_agent_instance .verify_token (email ,token )


def user_request_agent (content :str ):
    """
    Метод для запуска агента юридических запросов
    :param content: Контент, по которому происходит поиск в БЗ
    :return: Словарь со статусом результата выполнения агента аутентификации
    """
    agent :RequestAgent =current_app .config ['agents']['user_request_agent']
    return agent .request_agent (content )

def directory_agent (content :str ):
    """
    Метод для запуска агента поиска
    :param content: Контент, по которому происходит поиск в БЗ
    :return: Словарь со статусом результата выполнения агента аутентификации
    """
    agent :DirectoryAgent =current_app .config ['agents']['directory_agent']
    return agent .directory_agent (
    content =content 
    )

def add_event_agent (user_name ,event_name :str ,event_date ,event_description :str ):
    """
    Метод для запуска агента добавления события
    :param user_name: Логин пользователя
    :param event_name: Название события
    :param event_date: Дата события
    :param event_description: Описание события
    :return: Словарь со статусом результата выполнения агента добавления события
    """
    agent :AddEventAgent =current_app .config ['agents']['add_event_agent']
    return agent .add_event_agent (
    user_name =user_name ,
    event_name =event_name ,
    event_date =event_date ,
    event_description =event_description 
    )

def delete_event_agent (username :str ,event_name :str ):
    """
    Метод для запуска агента удаления события
    :param username: Логин пользователя
    :param event_name: Название события
    :return: Словарь со статусом результата выполнения агента удаления события
    """
    agent :DeleteEventAgent =current_app .config ['agents']['delete_event_agent']
    return agent .delete_event_agent (
    username =username ,
    event_name =event_name 
    )

def show_event_agent (username ):
    """
    Метод для запуска агента просмотра события
    :param username: Логин пользователя
    :return: Словарь со статусом результата выполнения агента просмотра события
    """
    agent :ShowEventAgent =current_app .config ['agents']['show_event_agent']
    return agent .show_event_agent (
    username =username 
    )


def test_agent_get_question (user_id :str ):
    """Получить следующий вопрос"""
    agent =current_app .config ['agents']['test_agent']
    return agent .get_next_question (user_id )


def test_agent_get_answers (question_addr ):
    """Получить варианты ответов"""
    agent =current_app .config ['agents']['test_agent']
    return agent .get_answers_for_question (question_addr )


def test_agent_save_answer (answer_id ,user_id :str ):
    """Сохранить ответ пользователя"""

    agent =current_app .config ['agents']['test_agent']
    return agent .save_answer (user_id ,answer_id )



def test_agent_check_answer (question_id ,user_id :str ):
    """Проверить ответ"""

    agent =current_app .config ['agents']['test_agent']
    return agent .check_answer (user_id ,question_id )



def test_agent_delete_old_data (user_id :str ):
    """Удалить старые данные теста"""
    agent =current_app .config ['agents']['test_agent']
    return agent .delete_old_test_data (user_id )


def test_agent_update_rating (user_id :str ):
    """Обновить рейтинг пользователя"""
    agent =current_app .config ['agents']['test_agent']
    return agent .update_rating (user_id )


# ============================================================================
# CABINET SERVICES - Profile, History, Bookmarks, Notes
# ============================================================================

# Initialize cabinet agents
profile_agent_instance = OstisProfileAgent()
history_agent_instance = OstisHistoryAgent()
bookmarks_agent_instance = OstisBookmarksAgent()
notes_agent_instance = OstisNotesAgent()


# Profile services
def get_user_profile(user_email: str):
    """Получить профиль пользователя"""
    return profile_agent_instance.get_profile(user_email)


def update_user_profile(user_email: str, data: dict):
    """Обновить профиль пользователя"""
    return profile_agent_instance.update_profile(user_email, data)


def get_user_settings(user_email: str):
    """Получить настройки пользователя"""
    return profile_agent_instance.get_settings(user_email)


def update_user_settings(user_email: str, settings: dict):
    """Обновить настройки пользователя"""
    return profile_agent_instance.update_settings(user_email, settings)


# History services
def get_user_history(user_email: str, period: str = 'week'):
    """Получить историю запросов пользователя"""
    return history_agent_instance.get_history(user_email, period)


def add_user_history_entry(user_email: str, query_type: str, query_text: str, article_id: str = None):
    """Добавить запись в историю"""
    return history_agent_instance.add_history_entry(user_email, query_type, query_text, article_id)


def clear_user_history(user_email: str):
    """Очистить историю пользователя"""
    return history_agent_instance.clear_history(user_email)


# Bookmarks services
def get_user_bookmarks(user_email: str):
    """Получить закладки пользователя"""
    return bookmarks_agent_instance.get_bookmarks(user_email)


def add_user_bookmark(user_email: str, article_id: str, title: str, tags: list = None):
    """Добавить закладку"""
    return bookmarks_agent_instance.add_bookmark(user_email, article_id, title, tags)


def update_user_bookmark(user_email: str, bookmark_id: str, tags: list = None):
    """Обновить закладку"""
    return bookmarks_agent_instance.update_bookmark(user_email, bookmark_id, tags)


def delete_user_bookmark(user_email: str, bookmark_id: str):
    """Удалить закладку"""
    return bookmarks_agent_instance.delete_bookmark(user_email, bookmark_id)


# Notes services
def get_user_notes(user_email: str):
    """Получить заметки пользователя"""
    return notes_agent_instance.get_notes(user_email)


def add_user_note(user_email: str, article_id: str, article_title: str, text: str):
    """Добавить заметку"""
    return notes_agent_instance.add_note(user_email, article_id, article_title, text)


def update_user_note(user_email: str, note_id: str, text: str):
    """Обновить заметку"""
    return notes_agent_instance.update_note(user_email, note_id, text)


def delete_user_note(user_email: str, note_id: str):
    """Удалить заметку"""
    return notes_agent_instance.delete_note(user_email, note_id)
