import configparser 
import os

class Config:
    config = configparser.ConfigParser()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, 'config.ini')
    config.read(config_path)
    
    AGENTS_TO_LOAD ={
    "auth_agent":"service.agents.ostis.OstisAuthAgent",
    "reg_agent":"service.agents.ostis.OstisRegAgent",
    "user_request_agent":"service.agents.ostis.OstisUserRequestAgent",
    "directory_agent":"service.agents.ostis.OstisDirectoryAgent",
    "add_event_agent":"service.agents.ostis.OstisAddEventAgent",
    "delete_event_agent":"service.agents.ostis.OstisDeleteEventAgent",
    "show_event_agent":"service.agents.ostis.OstisShowEventAgent",
    "test_agent":"service.agents.ostis.OstisTestAgent",
    "profile_agent":"service.agents.ostis.OstisProfileAgent",
    "history_agent":"service.agents.ostis.OstisHistoryAgent",
    "bookmarks_agent":"service.agents.ostis.OstisBookmarksAgent",
    "notes_agent":"service.agents.ostis.OstisNotesAgent"
    }
    OSTIS_URL =config ['DEFAULT']['ostis_url']
    PROTOCOL =config ['SERVER']['SC_SERVER_PROTOCOL']
    HOST =config ['SERVER']['SC_SERVER_HOST']
    PORT =config ['SERVER']['SC_SERVER_PORT']
    PROTOCOL_DEFAULT =config ['SERVER']['SC_SERVER_PROTOCOL_DEFAULT']
    HOST_DEFAULT =config ['SERVER']['SC_SERVER_HOST_DEFAULT']
    PORT_DEFAULT =config ['SERVER']['SC_SERVER_PORT_DEFAULT']
    MAX_SESSION_SIZE =4093 


class TestingConfig (Config ):
    TESTING =True 
