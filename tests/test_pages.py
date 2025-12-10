import flask_login 
import pytest 
from service import create_app 


class DummyUser (flask_login .UserMixin ):
    def __init__ (self ,id ="dummy"):
        self .id =id 


@pytest .fixture ()
def app ():
    app =create_app ("config.TestingConfig")

    login_manager =flask_login .LoginManager ()
    login_manager .init_app (app )

    @login_manager .user_loader 
    def load_user (user_id ):
        return DummyUser (id =user_id )

    ctx =app .app_context ()
    ctx .push ()

    yield app 

    ctx .pop ()


@pytest .fixture ()
def client (app ):
    return app .test_client ()


@pytest .fixture ()
def runner (app ):
    return app .test_cli_runner ()



def test_auth_page (client ):
    response =client .get ("/auth")
    assert response .status_code ==200 
    assert "<h2>Авторизация</h2>"in response .get_data (as_text =True )


def test_reg_page (client ):
    response =client .get ("/reg")
    assert response .status_code ==200 
    assert "<h2>Регистрация</h2>"in response .get_data (as_text =True )


def test_directory_page_with_unauthorized_user (client ):
    response =client .get ("/directory")


    assert response .status_code ==500 


def test_requests_page_with_unauthorized_user (client ):
    response =client .get ("/requests")


    assert response .status_code ==500 


def test_show_calendar_page_with_unauthorized_user (client ):
    response =client .get ("/show_calendar")


    assert response .status_code ==500 


def test_templates_page_with_unauthorized_user (client ):
    response =client .get ("/templates")


    assert response .status_code ==500 



def test_directory_page_with_authorized_user (client ):
    with client .session_transaction ()as session :
        session ["_user_id"]="123"
    response =client .get ("/directory")
    assert response .status_code ==200 
    assert '<h1 class="main-heading">Справочник</h1>'in response .get_data (as_text =True )


def test_requests_page_with_authorized_user (client ):
    with client .session_transaction ()as session :
        session ["_user_id"]="123"
    response =client .get ("/requests")
    assert response .status_code ==200 
    assert '<h1 class="main-heading">Запросы</h1>'in response .get_data (as_text =True )


def test_show_calendar_page_with_authorized_user (client ):
    with client .session_transaction ()as session :
        session ["_user_id"]="123"
    response =client .get ("/show_calendar")
    assert '<h2 class="events-title">События</h2>'in response .get_data (as_text =True )
    assert response .status_code ==200 


def test_templates_page_with_authorized_user (client ):
    with client .session_transaction ()as session :
        session ["_user_id"]="123"
    response =client .get ("/templates")
    assert response .status_code ==200 
    assert '<h1 class="header-title">Выберите шаблон</h1>'in response .get_data (as_text =True )
