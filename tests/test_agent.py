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


def test_dictionary_agent (client ):
    with client .session_transaction ()as session :
        session ["_user_id"]="123"
        session ["_fresh"]=True 
    response =client .post ("/directory")
    assert response .status_code ==200 
    assert "<h2>Авторизация</h2>"in response .get_data (as_text =True )
