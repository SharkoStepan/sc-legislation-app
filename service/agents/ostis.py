from enum import Enum 
from threading import Event 

import sc_client .client as client 

from ..exceptions import ScServerError 
from sc_client .client import is_connected ,search_links_by_contents 
from sc_client .models import (
ScAddr ,
ScConstruction ,
ScEventSubscriptionParams ,
ScIdtfResolveParams ,
ScLinkContent ,
ScLinkContentType ,
ScTemplate
)
from sc_client .constants .common import ScEventType 
from sc_client .constants import sc_types 
from sc_kpm import ScKeynodes 

from service .models import RequestResponse ,DirectoryResponse ,EventResponse ,UserEvent 
from service .models import get_user_by_login 
from service .agents .abstract .auth_agent import AuthAgent ,AuthStatus 
from service .agents .abstract .reg_agent import RegAgent ,RegStatus 
from service .agents .abstract .user_request_agent import RequestAgent ,RequestStatus 
from service .agents .abstract .directory_agent import DirectoryAgent ,DirectoryStatus 
from service .agents .abstract .event_agents import (
AddEventAgent ,
AddEventStatus ,
DeleteEventAgent ,
DeleteEventStatus ,
ShowEventAgent ,
ShowEventStatus 
)
from service .exceptions import AgentError 
from service .utils .ostis_utils import (
create_link ,
get_node ,
set_gender_content ,
split_date_content ,
get_main_idtf ,
set_system_idtf 
)
from config import Config 
from service .agents .abstract .test_agent import TestAgent ,TestStatus
from service .agents .abstract .verification_agent import VerificationAgent ,VerificationStatus
from service.agents.abstract.profile_agent import ProfileAgent, ProfileStatus
from service.agents.abstract.history_agent import HistoryAgent, HistoryStatus
from service.agents.abstract.bookmarks_agent import BookmarksAgent, BookmarksStatus
from service.agents.abstract.notes_agent import NotesAgent, NotesStatus
from datetime import datetime 


payload =None 
callback_event =Event ()

gender_dict ={
"male":"мужчина",
"female":"женщина"
}

class result (Enum ):
    """
    Перечисление для представления результата выполнения агента
    """
    SUCCESS =0 
    FAILURE =1 

def call_back (src :ScAddr ,connector :ScAddr ,trg :ScAddr )->Enum :
    """
    Метод для реализации дефолтной колбэк-функции выполнения агента
    :param src: Адрес ноды для вызова агента
    :param connector: Коннектор
    :param trg: Адрес ноды, которая показывает результат выполнения агента
    :return: Результат выполнения агента
    """
    global payload 
    callback_event .clear ()
    succ_node =client .resolve_keynodes (
    ScIdtfResolveParams (idtf ='action_finished_successfully',type =sc_types .NODE_CONST_CLASS )
    )[0 ]
    unsucc_node =client .resolve_keynodes (
    ScIdtfResolveParams (idtf ='action_finished_unsuccessfully',type =sc_types .NODE_CONST_CLASS )
    )[0 ]
    node_err =client .resolve_keynodes (
    ScIdtfResolveParams (idtf ='action_finished_with_error',type =sc_types .NODE_CONST_CLASS )
    )[0 ]
    if trg .value ==succ_node .value :
        print (trg .value )
        print (succ_node .value )
        nrel_result =client .resolve_keynodes (
        ScIdtfResolveParams (idtf ='nrel_result',type =sc_types .NODE_CONST_CLASS )
        )[0 ]
        res_templ =ScTemplate ()
        res_templ .triple_with_relation (
        src ,
        sc_types .EDGE_D_COMMON_VAR ,
        sc_types .NODE_VAR_STRUCT >>"_res_struct",
        sc_types .EDGE_ACCESS_VAR_POS_PERM ,
        nrel_result 
        )
        res_templ .triple (
        succ_node ,
        sc_types .EDGE_ACCESS_VAR_POS_PERM ,
        src 
        )
        gen_res =client .template_search (res_templ )[0 ]
        payload ={"message":result .SUCCESS }
    elif trg .value ==unsucc_node .value or trg .value ==node_err .value :
        payload ={"message":result .FAILURE }

    callback_event .set ()
    if not payload :
        return result .FAILURE 
    return result .SUCCESS 

def call_back_request (src :ScAddr ,connector :ScAddr ,trg :ScAddr )->Enum :
    """
    Метод для реализации колбэк-функции выполнения агента юридических запросов
    :param src: Адрес ноды для вызова агента
    :param connector: Коннектор
    :param trg: Адрес ноды, которая показывает результат выполнения агента
    :return: Результат выполнения агента
    """
    global payload
    # Only handle finish signals — ignore arcs created during template_generate
    # (action_initiated, action class membership, etc.)
    try:
        succ_node  = client.resolve_keynodes(ScIdtfResolveParams(idtf='action_finished_successfully',  type=sc_types.NODE_CONST_CLASS))[0]
        unsucc_node = client.resolve_keynodes(ScIdtfResolveParams(idtf='action_finished_unsuccessfully', type=sc_types.NODE_CONST_CLASS))[0]
        node_err   = client.resolve_keynodes(ScIdtfResolveParams(idtf='action_finished_with_error',      type=sc_types.NODE_CONST_CLASS))[0]
    except Exception:
        return result.FAILURE

    # Not a finish signal — silently ignore, do NOT set callback_event
    if trg.value not in (succ_node.value, unsucc_node.value, node_err.value):
        return result.FAILURE

    content_list = []

    if trg .value ==succ_node .value :
        nrel_result =client .resolve_keynodes (
        ScIdtfResolveParams (idtf ='nrel_result',type =sc_types .NODE_CONST_CLASS )
        )[0 ]
        body_template =ScTemplate ()
        related_article_template =ScTemplate ()
        related_concept_template =ScTemplate ()

        body_template .triple_with_relation (
        src ,
        sc_types .EDGE_ACCESS_VAR_POS_PERM ,
        sc_types .LINK_VAR >>"_src_link",
        sc_types .EDGE_ACCESS_VAR_POS_PERM ,
        ScKeynodes ["rrel_1"]
        )
        body_template .triple_with_relation (
        src ,
        sc_types .EDGE_D_COMMON_VAR ,
        sc_types .NODE_VAR_STRUCT >>"_res_struct",
        sc_types .EDGE_ACCESS_VAR_POS_PERM ,
        nrel_result 
        )
        body_template .triple (
        "_res_struct",
        sc_types .EDGE_ACCESS_VAR_POS_PERM ,
        sc_types .LINK_VAR >>"_link_body"
        )

        related_article_template .triple_with_relation (
        src ,
        sc_types .EDGE_D_COMMON_VAR ,
        sc_types .NODE_VAR_STRUCT >>"_res_struct",
        sc_types .EDGE_ACCESS_VAR_POS_PERM ,
        nrel_result 
        )
        related_article_template .triple (
        "_res_struct",
        sc_types .EDGE_ACCESS_VAR_POS_PERM ,
        sc_types .NODE_VAR >>"_related_article"
        )
        related_article_template .triple (
        ScKeynodes ["belarus_legal_article"],
        sc_types .EDGE_ACCESS_VAR_POS_PERM ,
        "_related_article",
        )

        related_concept_template .triple_with_relation (
        src ,
        sc_types .EDGE_D_COMMON_VAR ,
        sc_types .NODE_VAR_STRUCT >>"_res_struct",
        sc_types .EDGE_ACCESS_VAR_POS_PERM ,
        nrel_result 
        )
        related_concept_template .triple (
        "_res_struct",
        sc_types .EDGE_ACCESS_VAR_POS_PERM ,
        sc_types .NODE_VAR_CLASS >>"_related_term"
        )

        body_result =client .template_search (body_template )
        for _body in body_result :
            src_link =_body .get ("_src_link")
            link =_body .get ("_link_body")
            term =client .get_link_content (src_link )[0 ].data 
            content =client .get_link_content (link )[0 ].data 

            related_articles =[]
            related_concepts =[]

            article_result =client .template_search (related_article_template )
            for _article in article_result :
                article_node =_article .get ("_related_article")
                if article_node :
                    article_data =get_main_idtf (article_node )
                    if article_data :
                        related_articles .append (article_data )

            concept_result =client .template_search (related_concept_template )
            for _concept in concept_result :
                concept_node =_concept .get ("_related_term")
                if concept_node :
                    concept_data =get_main_idtf (concept_node )
                    if concept_data :
                        related_concepts .append (concept_data )

            response =RequestResponse (
            term =term ,
            content =content ,
            related_articles =related_articles ,
            related_concepts =related_concepts 
            )

            content_list .append (response )

        payload = {"message": content_list}
    elif trg.value == unsucc_node.value or trg.value == node_err.value:
        payload = {"message": []}  # empty list, not string "Nothing"

    # Signal waiting thread only after payload is set
    callback_event.set()
    return result.SUCCESS if payload else result.FAILURE

def call_back_directory (src :ScAddr ,connector :ScAddr ,trg :ScAddr )->Enum :
    """
    Метод для реализации колбэк-функции выполнения агента поиска
    :param src: Адрес ноды для вызова агента
    :param connector: Коннектор
    :param trg: Адрес ноды, которая показывает результат выполнения агента
    :return: Результат выполнения агента
    """
    global payload 
    callback_event .clear ()
    content_list =[]
    succ_node =client .resolve_keynodes (
    ScIdtfResolveParams (idtf ='action_finished_successfully',type =sc_types .NODE_CONST_CLASS )
    )[0 ]
    unsucc_node =client .resolve_keynodes (
    ScIdtfResolveParams (idtf ='action_finished_unsuccessfully',type =sc_types .NODE_CONST_CLASS )
    )[0 ]
    node_err =client .resolve_keynodes (
    ScIdtfResolveParams (idtf ='action_finished_with_error',type =sc_types .NODE_CONST_CLASS )
    )[0 ]

    if trg .value ==succ_node .value :
        nrel_result =client .resolve_keynodes (
        ScIdtfResolveParams (idtf ='nrel_result',type =sc_types .NODE_CONST_CLASS )
        )[0 ]
        res_templ =ScTemplate ()
        res_templ .triple_with_relation (
        src ,
        sc_types .EDGE_D_COMMON_VAR ,
        sc_types .NODE_VAR_STRUCT >>"_res_struct",
        sc_types .EDGE_ACCESS_VAR_POS_PERM ,
        nrel_result 
        )
        res_templ .triple (
        "_res_struct",
        sc_types .EDGE_ACCESS_VAR_POS_PERM ,
        sc_types .NODE_VAR >>"_article_node"
        )
        gen_res =client .template_search (res_templ )
        for _ in gen_res :
            node_res =_ .get ("_article_node")
            _templ =ScTemplate ()
            _templ .triple_with_relation (
            node_res ,
            sc_types .EDGE_D_COMMON_VAR ,
            sc_types .LINK_VAR >>"_title_link",
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            ScKeynodes ["nrel_main_idtf"],
            )
            _templ .triple (
            ScKeynodes ["lang_ru"],
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            "_title_link"
            )
            _templ .triple_with_relation (
            sc_types .NODE_VAR >>"_1",
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            node_res ,
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            ScKeynodes ["rrel_key_sc_element"]
            )
            _templ .triple_with_relation (
            sc_types .NODE_VAR >>"_2",
            sc_types .EDGE_D_COMMON_VAR ,
            "_1",
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            ScKeynodes ["nrel_sc_text_translation"]
            )
            _templ .triple_with_relation (
            "_2",
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            sc_types .LINK_VAR >>"_content_link",
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            ScKeynodes ["rrel_example"]
            )
            _templ .triple (
            ScKeynodes ["lang_ru"],
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            "_content_link"
            )
            _res =client .template_search (_templ )[0 ]
            _title_link =_res .get ("_title_link")
            _content_link =_res .get ("_content_link")
            title_data =client .get_link_content (_title_link )[0 ].data 
            content_data =client .get_link_content (_content_link )[0 ].data 
            content_list .append (
            DirectoryResponse (
            title =title_data ,
            content =content_data )
            )
        payload ={"message":content_list }
    elif trg .value ==unsucc_node .value or trg .value ==node_err .value :
        payload ={"message":"Nothing"}

    callback_event .set ()
    if not payload :
        return result .FAILURE 
    return result .SUCCESS 

def call_back_get_events (src :ScAddr ,connector :ScAddr ,trg :ScAddr )->Enum :
    """
    Метод для реализации колбэк-функции выполнения агента получения событий
    :param src: Адрес ноды для вызова агента
    :param connector: Коннектор
    :param trg: Адрес ноды, которая показывает результат выполнения агента
    :return: Результат выполнения агента
    """
    global payload 
    callback_event .clear ()
    succ_node =client .resolve_keynodes (
    ScIdtfResolveParams (idtf ='action_finished_successfully',type =sc_types .NODE_CONST_CLASS )
    )[0 ]
    unsucc_node =client .resolve_keynodes (
    ScIdtfResolveParams (idtf ='action_finished_unsuccessfully',type =sc_types .NODE_CONST_CLASS )
    )[0 ]
    node_err =client .resolve_keynodes (
    ScIdtfResolveParams (idtf ='action_finished_with_error',type =sc_types .NODE_CONST_CLASS )
    )[0 ]

    if trg .value ==succ_node .value :
        nrel_result =client .resolve_keynodes (
        ScIdtfResolveParams (idtf ='nrel_result',type =sc_types .NODE_CONST_CLASS )
        )[0 ]
        res_templ =ScTemplate ()
        res_templ .triple_with_relation (
        src ,
        sc_types .EDGE_D_COMMON_VAR ,
        sc_types .NODE_VAR_STRUCT >>"_res_struct",
        sc_types .EDGE_ACCESS_VAR_POS_PERM ,
        nrel_result 
        )
        res_templ .triple (
        succ_node ,
        sc_types .EDGE_ACCESS_VAR_POS_PERM ,
        src 
        )
        gen_res =client .template_search (res_templ )[0 ]
        payload ={"message":result .SUCCESS }
    elif trg .value ==unsucc_node .value or trg .value ==node_err .value :
        payload ={"message":result .FAILURE }

    callback_event .set ()
    if not payload :
        return result .FAILURE 
    return result .SUCCESS 

def callback_rating (src :ScAddr ,connector :ScAddr ,trg :ScAddr ):
    """
    Специальный callback для RatingUpdateAgent - извлекает РАНГ пользователя (строкой)
    """
    global payload 
    callback_event .clear ()

    succ_node =client .resolve_keynodes (
    ScIdtfResolveParams (idtf ="action_finished_successfully",type =sc_types .NODE_CONST_CLASS )
    )[0 ]
    unsucc_node =client .resolve_keynodes (
    ScIdtfResolveParams (idtf ="action_finished_unsuccessfully",type =sc_types .NODE_CONST_CLASS )
    )[0 ]
    node_err =client .resolve_keynodes (
    ScIdtfResolveParams (idtf ="action_finished_with_error",type =sc_types .NODE_CONST_CLASS )
    )[0 ]

    if trg .value ==succ_node .value :

        nrel_result =client .resolve_keynodes (
        ScIdtfResolveParams (idtf ="nrel_result",type =sc_types .NODE_CONST_CLASS )
        )[0 ]

        res_templ =ScTemplate ()
        res_templ .triple_with_relation (
        src ,
        sc_types .EDGE_D_COMMON_VAR ,
        sc_types .NODE_VAR_STRUCT >>"res_struct",
        sc_types .EDGE_ACCESS_VAR_POS_PERM ,
        nrel_result 
        )
        res_templ .triple (
        "res_struct",
        sc_types .EDGE_ACCESS_VAR_POS_PERM ,
        sc_types .LINK_VAR >>"rank_link"
        )

        results =client .template_search (res_templ )

        if results and len (results )>0 :
            try :
                rank_link =results [0 ].get ("rank_link")
                rank_data =client .get_link_content (rank_link )

                if rank_data and len (rank_data )>0 :

                    rank_str =str (rank_data [0 ].data )
                    payload ={"message":result .SUCCESS ,"rating":rank_str }
                    print (f"DEBUG: Extracted rank = {rank_str }")
                else :
                    payload ={"message":result .SUCCESS ,"rating":"третий ранг"}
            except Exception as e :
                print (f"Error extracting rank: {e }")
                payload ={"message":result .SUCCESS ,"rating":"третий ранг"}
        else :
            print ("WARNING: No result structure found, returning default rank")
            payload ={"message":result .SUCCESS ,"rating":"третий ранг"}

    elif trg .value ==unsucc_node .value or trg .value ==node_err .value :
        payload ={"message":result .FAILURE }

    callback_event .set ()

    if not payload :
        return result .FAILURE 

    return result .SUCCESS 

def callback_check_answer (src :ScAddr ,connector :ScAddr ,trg :ScAddr ):
    """
    Специальный callback для CheckTheAnswerAgent - извлекает правильность ответа
    """
    global payload 
    callback_event .clear ()

    succ_node =client .resolve_keynodes (
    ScIdtfResolveParams (idtf ="action_finished_successfully",type =sc_types .NODE_CONST_CLASS )
    )[0 ]
    unsucc_node =client .resolve_keynodes (
    ScIdtfResolveParams (idtf ="action_finished_unsuccessfully",type =sc_types .NODE_CONST_CLASS )
    )[0 ]
    node_err =client .resolve_keynodes (
    ScIdtfResolveParams (idtf ="action_finished_with_error",type =sc_types .NODE_CONST_CLASS )
    )[0 ]

    if trg .value ==succ_node .value :

        nrel_result =client .resolve_keynodes (
        ScIdtfResolveParams (idtf ="nrel_result",type =sc_types .NODE_CONST_CLASS )
        )[0 ]

        res_templ =ScTemplate ()
        res_templ .triple_with_relation (
        src ,
        sc_types .EDGE_D_COMMON_VAR ,
        sc_types .NODE_VAR_STRUCT >>"res_struct",
        sc_types .EDGE_ACCESS_VAR_POS_PERM ,
        nrel_result 
        )
        res_templ .triple (
        "res_struct",
        sc_types .EDGE_ACCESS_VAR_POS_PERM ,
        sc_types .LINK_VAR >>"result_link"
        )

        genres =client .template_search (res_templ )

        if genres and len (genres )>0 :
            try :
                result_link =genres [0 ].get ("result_link")
                result_data =client .get_link_content (result_link )

                if result_data and len (result_data )>0 :
                    is_correct =result_data [0 ].data =="1"
                    payload ={"message":result .SUCCESS ,"is_correct":is_correct }
                    print (f"DEBUG: Answer is correct = {is_correct }")
                else :
                    payload ={"message":result .SUCCESS ,"is_correct":False }
            except Exception as e :
                print (f"Error extracting check result: {e }")
                payload ={"message":result .SUCCESS ,"is_correct":False }
        else :
            print ("WARNING: No result structure found for check answer")
            payload ={"message":result .SUCCESS ,"is_correct":False }

    elif trg .value ==unsucc_node .value or trg .value ==node_err .value :
        payload ={"message":result .FAILURE }

    callback_event .set ()

    if not payload :
        return result .FAILURE 

    return result .SUCCESS 

class Ostis :
    """
    Класс для представления OSTIS-системы
    """
    def __init__ (self ,url ):
        self .ostis_url =url 

    def call_registration_agent (
    self ,
    action_name :str ,
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
        Метод для вызова агента регистрации
        """
        if not is_connected ():
            raise ScServerError ()

        global payload 
        payload =None 


        email_lnk =create_link (client ,email )
        password_lnk =create_link (client ,password )
        password_conf_lnk =create_link (client ,password_conf )


        action_agent =client .resolve_keynodes (
        ScIdtfResolveParams (idtf =action_name ,type =sc_types .NODE_CONST_CLASS )
        )[0 ]

        initiated_node =client .resolve_keynodes (
        ScIdtfResolveParams (idtf ='action_initiated',type =sc_types .NODE_CONST_CLASS )
        )[0 ]


        rrel_1 =client .resolve_keynodes (ScIdtfResolveParams (idtf ='rrel_1',type =sc_types .NODE_CONST_ROLE ))[0 ]
        rrel_2 =client .resolve_keynodes (ScIdtfResolveParams (idtf ='rrel_2',type =sc_types .NODE_CONST_ROLE ))[0 ]
        rrel_3 =client .resolve_keynodes (ScIdtfResolveParams (idtf ='rrel_3',type =sc_types .NODE_CONST_ROLE ))[0 ]
        rrel_4 =client .resolve_keynodes (ScIdtfResolveParams (idtf ='rrel_4',type =sc_types .NODE_CONST_ROLE ))[0 ]


        concept_client_kn =client .resolve_keynodes (
        ScIdtfResolveParams (idtf ='concept_client',type =sc_types .NODE_CONST_CLASS )
        )[0 ]
        concept_specialist_kn =client .resolve_keynodes (
        ScIdtfResolveParams (idtf ='concept_specialist',type =sc_types .NODE_CONST_CLASS )
        )[0 ]


        user_type_class =concept_client_kn if user_type =='client'else concept_specialist_kn 


        main_node =get_node (client )


        template =ScTemplate ()


        template .triple_with_relation (
        main_node >>"_main_node",
        sc_types .EDGE_ACCESS_VAR_POS_PERM ,
        email_lnk ,
        sc_types .EDGE_ACCESS_VAR_POS_PERM ,
        rrel_1 
        )


        template .triple_with_relation (
        main_node >>"_main_node",
        sc_types .EDGE_ACCESS_VAR_POS_PERM ,
        password_lnk ,
        sc_types .EDGE_ACCESS_VAR_POS_PERM ,
        rrel_2 
        )


        template .triple_with_relation (
        main_node >>"_main_node",
        sc_types .EDGE_ACCESS_VAR_POS_PERM ,
        password_conf_lnk ,
        sc_types .EDGE_ACCESS_VAR_POS_PERM ,
        rrel_3 
        )


        template .triple_with_relation (
        main_node >>"_main_node",
        sc_types .EDGE_ACCESS_VAR_POS_PERM ,
        sc_types .NODE_VAR >>"_user_type",
        sc_types .EDGE_ACCESS_VAR_POS_PERM ,
        rrel_4 
        )

        template .triple (
        user_type_class ,
        sc_types .EDGE_ACCESS_VAR_POS_PERM ,
        "_user_type"
        )


        if user_type =='specialist':
            rrel_5 =client .resolve_keynodes (ScIdtfResolveParams (idtf ='rrel_5',type =sc_types .NODE_CONST_ROLE ))[0 ]
            rrel_6 =client .resolve_keynodes (ScIdtfResolveParams (idtf ='rrel_6',type =sc_types .NODE_CONST_ROLE ))[0 ]
            rrel_7 =client .resolve_keynodes (ScIdtfResolveParams (idtf ='rrel_7',type =sc_types .NODE_CONST_ROLE ))[0 ]
            rrel_8 =client .resolve_keynodes (ScIdtfResolveParams (idtf ='rrel_8',type =sc_types .NODE_CONST_ROLE ))[0 ]
            rrel_9 =client .resolve_keynodes (ScIdtfResolveParams (idtf ='rrel_9',type =sc_types .NODE_CONST_ROLE ))[0 ]

            if full_name :
                full_name_lnk =create_link (client ,full_name )
                template .triple_with_relation (
                main_node >>"_main_node",
                sc_types .EDGE_ACCESS_VAR_POS_PERM ,
                full_name_lnk ,
                sc_types .EDGE_ACCESS_VAR_POS_PERM ,
                rrel_5 
                )

            if gender :
                gender_lnk =create_link (client ,gender )
                template .triple_with_relation (
                main_node >>"_main_node",
                sc_types .EDGE_ACCESS_VAR_POS_PERM ,
                gender_lnk ,
                sc_types .EDGE_ACCESS_VAR_POS_PERM ,
                rrel_6 
                )

            if age :
                age_lnk =create_link (client ,str (age ))
                template .triple_with_relation (
                main_node >>"_main_node",
                sc_types .EDGE_ACCESS_VAR_POS_PERM ,
                age_lnk ,
                sc_types .EDGE_ACCESS_VAR_POS_PERM ,
                rrel_7 
                )

            if experience :
                experience_lnk =create_link (client ,str (experience ))
                template .triple_with_relation (
                main_node >>"_main_node",
                sc_types .EDGE_ACCESS_VAR_POS_PERM ,
                experience_lnk ,
                sc_types .EDGE_ACCESS_VAR_POS_PERM ,
                rrel_8 
                )

            if field :
                field_lnk =create_link (client ,field )
                template .triple_with_relation (
                main_node >>"_main_node",
                sc_types .EDGE_ACCESS_VAR_POS_PERM ,
                field_lnk ,
                sc_types .EDGE_ACCESS_VAR_POS_PERM ,
                rrel_9 
                )


        template .triple (
        action_agent ,
        sc_types .EDGE_ACCESS_VAR_POS_PERM ,
        "_main_node",
        )


        template .triple (
        initiated_node ,
        sc_types .EDGE_ACCESS_VAR_POS_PERM ,
        "_main_node",
        )


        event_params =ScEventSubscriptionParams (
        main_node ,
        ScEventType .AFTER_GENERATE_INCOMING_ARC ,
        call_back 
        )
        client .events_create (event_params )


        client .template_generate (template )


        if callback_event .wait (timeout =30 ):
            while not payload :
                continue 
            return payload 
        else :
            raise AgentError (524 ,"Timeout")



    def call_auth_agent (self ,action_name :str ,email :str ,password :str ):
        """
        Метод для вызова агента аутентификации
        """
        if not is_connected ():
            raise ScServerError ()

        global payload 
        payload =None 


        username_lnk =create_link (client ,email )
        password_lnk =create_link (client ,password )


        rrel_1 =client .resolve_keynodes (ScIdtfResolveParams (idtf ='rrel_1',type =sc_types .NODE_CONST_ROLE ))[0 ]
        rrel_2 =client .resolve_keynodes (ScIdtfResolveParams (idtf ='rrel_2',type =sc_types .NODE_CONST_ROLE ))[0 ]
        initiated_node =client .resolve_keynodes (ScIdtfResolveParams (idtf ='action_initiated',type =sc_types .NODE_CONST_CLASS ))[0 ]
        action_agent =client .resolve_keynodes (ScIdtfResolveParams (idtf =action_name ,type =sc_types .NODE_CONST_CLASS ))[0 ]

        main_node =get_node (client )


        template =ScTemplate ()
        template .triple_with_relation (
        main_node >>"_main_node",
        sc_types .EDGE_ACCESS_VAR_POS_PERM ,
        username_lnk ,
        sc_types .EDGE_ACCESS_VAR_POS_PERM ,
        rrel_1 
        )
        template .triple_with_relation (
        main_node >>"_main_node",
        sc_types .EDGE_ACCESS_VAR_POS_PERM ,
        password_lnk ,
        sc_types .EDGE_ACCESS_VAR_POS_PERM ,
        rrel_2 
        )
        template .triple (
        action_agent ,
        sc_types .EDGE_ACCESS_VAR_POS_PERM ,
        "_main_node",
        )
        template .triple (
        initiated_node ,
        sc_types .EDGE_ACCESS_VAR_POS_PERM ,
        "_main_node",
        )

        event_params =ScEventSubscriptionParams (
        main_node ,
        ScEventType .AFTER_GENERATE_INCOMING_ARC ,
        call_back 
        )
        client .events_create (event_params )
        client .template_generate (template )

        if callback_event .wait (timeout =10 ):
            while not payload :
                continue 
            return payload 
        else :
            raise AgentError (524 ,"Timeout")


    def call_verification_agent (self ,action_name :str ,email :str ,token :str =None ):
        """
        Метод для вызова агента верификации
        """
        if not is_connected ():
            raise ScServerError ()

        global payload 
        payload =None 


        email_lnk =create_link (client ,email )


        rrel_1 =client .resolve_keynodes (ScIdtfResolveParams (idtf ='rrel_1',type =sc_types .NODE_CONST_ROLE ))[0 ]
        initiated_node =client .resolve_keynodes (ScIdtfResolveParams (idtf ='action_initiated',type =sc_types .NODE_CONST_CLASS ))[0 ]
        action_agent =client .resolve_keynodes (ScIdtfResolveParams (idtf =action_name ,type =sc_types .NODE_CONST_CLASS ))[0 ]

        main_node =get_node (client )


        template =ScTemplate ()
        template .triple_with_relation (
        main_node >>"_main_node",
        sc_types .EDGE_ACCESS_VAR_POS_PERM ,
        email_lnk ,
        sc_types .EDGE_ACCESS_VAR_POS_PERM ,
        rrel_1 
        )


        if token is not None :
            rrel_2 =client .resolve_keynodes (ScIdtfResolveParams (idtf ='rrel_2',type =sc_types .NODE_CONST_ROLE ))[0 ]
            token_lnk =create_link (client ,token )
            template .triple_with_relation (
            main_node >>"_main_node",
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            token_lnk ,
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            rrel_2 
            )

        template .triple (
        action_agent ,
        sc_types .EDGE_ACCESS_VAR_POS_PERM ,
        "_main_node",
        )
        template .triple (
        initiated_node ,
        sc_types .EDGE_ACCESS_VAR_POS_PERM ,
        "_main_node",
        )

        event_params =ScEventSubscriptionParams (
        main_node ,
        ScEventType .AFTER_GENERATE_INCOMING_ARC ,
        call_back 
        )
        client .events_create (event_params )
        client .template_generate (template )

        if callback_event .wait (timeout =10 ):
            while not payload :
                continue 
            return payload 
        else :
            raise AgentError (524 ,"Timeout")



    def call_user_request_agent (self ,
    action_name :str ,
    content :str 
    ):
        """
        Метод для вызова агента юридических запросов
        :param action_name: Идентификатор action-ноды агента
        :param content: Контент, по которому происходит поиск в БЗ
        :return: Ответ сервера
        :raises AgentError: Возникает при истечении времени ожидания
        :raises ScServerError: Возникает при отсутствии запущенного sc-сервера
        """
        if not is_connected():
            return None

        global payload
        # Reset state BEFORE subscribing to avoid stale event from previous request
        payload = None
        callback_event.clear()

        request_lnk   = create_link(client, content)
        rrel_1         = client.resolve_keynodes(ScIdtfResolveParams(idtf='rrel_1',          type=sc_types.NODE_CONST_ROLE))[0]
        initiated_node = client.resolve_keynodes(ScIdtfResolveParams(idtf='action_initiated', type=sc_types.NODE_CONST_CLASS))[0]
        action_agent   = client.resolve_keynodes(ScIdtfResolveParams(idtf=action_name,        type=sc_types.NODE_CONST_CLASS))[0]
        main_node      = get_node(client)

        template = ScTemplate()
        template.triple_with_relation(
            main_node >> "_main_node",
            sc_types.EDGE_ACCESS_VAR_POS_PERM,
            request_lnk,
            sc_types.EDGE_ACCESS_VAR_POS_PERM,
            rrel_1,
        )
        template.triple(action_agent,   sc_types.EDGE_ACCESS_VAR_POS_PERM, "_main_node")
        template.triple(initiated_node, sc_types.EDGE_ACCESS_VAR_POS_PERM, "_main_node")

        event_params = ScEventSubscriptionParams(
            main_node, ScEventType.AFTER_GENERATE_INCOMING_ARC, call_back_request
        )
        client.events_create(event_params)
        client.template_generate(template)

        # Wait for finish signal — callback only sets event on action_finished_* arcs
        if callback_event.wait(timeout=30):
            return payload   # may be {"message": []} on failure
        # Timeout — sc-machine agent didn't respond
        print(f"[REQUEST] Timeout waiting for action_user_request response")
        return None

    def call_directory_agent (self ,action_name :str ,content :str )->str :
        """
        Метод для вызова агента поиска
        :param action_name: Идентификатор action-ноды агента
        :param content: Контент, по которому происходит поиск в БЗ
        :return: Ответ сервера
        :raises AgentError: Возникает при истечении времени ожидания
        :raises ScServerError: Возникает при отсутствии запущенного sc-сервера
        """
        if is_connected ():
            part_node =ScKeynodes ["CONCEPT_FULL_SEARCH"]
            area_node =ScKeynodes ["FULL_SEARCH"]
            content_lnk =create_link (client ,content )

            rrel_1 =client .resolve_keynodes (ScIdtfResolveParams (idtf ='rrel_1',type =sc_types .NODE_CONST_ROLE ))[0 ]
            rrel_2 =client .resolve_keynodes (ScIdtfResolveParams (idtf ='rrel_2',type =sc_types .NODE_CONST_ROLE ))[0 ]
            rrel_3 =client .resolve_keynodes (ScIdtfResolveParams (idtf ='rrel_3',type =sc_types .NODE_CONST_ROLE ))[0 ]

            initiated_node =client .resolve_keynodes (ScIdtfResolveParams (idtf ='action_initiated',type =sc_types .NODE_CONST_CLASS ))[0 ]
            action_agent =client .resolve_keynodes (ScIdtfResolveParams (idtf =action_name ,type =sc_types .NODE_CONST_CLASS ))[0 ]
            main_node =get_node (client )

            template =ScTemplate ()
            template .triple_with_relation (
            main_node >>"_main_node",
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            part_node ,
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            rrel_1 
            )
            template .triple_with_relation (
            main_node >>"_main_node",
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            area_node ,
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            rrel_2 
            )
            template .triple_with_relation (
            main_node >>"_main_node",
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            content_lnk ,
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            rrel_3 
            )
            template .triple (
            action_agent ,
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            "_main_node",
            )
            template .triple (
            initiated_node ,
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            "_main_node",
            )

            event_params =ScEventSubscriptionParams (main_node ,ScEventType .AFTER_GENERATE_INCOMING_ARC ,call_back_directory )
            client .events_create (event_params )
            client .template_generate (template )

            global payload 
            if callback_event .wait (timeout =10 ):
                while not payload :
                    continue 
                return payload 
            else :
                raise AgentError (524 ,"Timeout")
        else :
            raise ScServerError 

    def call_add_event_agent (self ,action_name :str ,user_name ,event_name :str ,event_date ,event_description :str )->str :
        """
        Метод для вызова агента добавления события
        :param action_name: Идентификатор action-ноды агента
        :param user_name: Логин пользователя
        :param event_name: Название события
        :param event_date: Дата события
        :param event_description: Описание события
        :return: Ответ сервера
        :raises AgentError: Возникает при истечении времени ожидания
        :raises ScServerError: Возникает при отсутствии запущенного sc-сервера
        """
        if is_connected ():
            event_name_lnk =create_link (client ,event_name )
            day ,month ,year =split_date_content (event_date )
            day_node =set_system_idtf (day )
            month_node =set_system_idtf (month )
            year_node =set_system_idtf (year )
            event_description_lnk =create_link (client ,event_description )

            rrel_1 =client .resolve_keynodes (ScIdtfResolveParams (idtf ='rrel_1',type =sc_types .NODE_CONST_ROLE ))[0 ]
            rrel_2 =client .resolve_keynodes (ScIdtfResolveParams (idtf ='rrel_2',type =sc_types .NODE_CONST_ROLE ))[0 ]
            rrel_3 =client .resolve_keynodes (ScIdtfResolveParams (idtf ='rrel_3',type =sc_types .NODE_CONST_ROLE ))[0 ]
            rrel_4 =client .resolve_keynodes (ScIdtfResolveParams (idtf ='rrel_4',type =sc_types .NODE_CONST_ROLE ))[0 ]

            rrel_event_day =client .resolve_keynodes (ScIdtfResolveParams (idtf ='rrel_event_day',type =sc_types .NODE_CONST_ROLE ))[0 ]
            rrel_event_month =client .resolve_keynodes (ScIdtfResolveParams (idtf ='rrel_event_month',type =sc_types .NODE_CONST_ROLE ))[0 ]
            rrel_event_year =client .resolve_keynodes (ScIdtfResolveParams (idtf ='rrel_event_year',type =sc_types .NODE_CONST_ROLE ))[0 ]

            initiated_node =client .resolve_keynodes (ScIdtfResolveParams (idtf ='action_initiated',type =sc_types .NODE_CONST_CLASS ))[0 ]
            action_agent =client .resolve_keynodes (ScIdtfResolveParams (idtf =action_name ,type =sc_types .NODE_CONST_CLASS ))[0 ]
            main_node =get_node (client )

            user =get_user_by_login (user_name )
            template =ScTemplate ()
            template .triple_with_relation (
            main_node >>"_main_node",
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            user ,
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            rrel_1 
            )
            template .triple_with_relation (
            main_node >>"_main_node",
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            event_name_lnk ,
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            rrel_2 
            )
            template .triple_with_relation (
            main_node >>"_main_node",
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            sc_types .NODE_VAR_TUPLE >>"_tuple",
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            rrel_3 
            )
            template .triple_with_relation (
            "_tuple",
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            day_node ,
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            rrel_event_day 
            )
            template .triple_with_relation (
            "_tuple",
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            month_node ,
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            rrel_event_month 
            )
            template .triple_with_relation (
            "_tuple",
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            year_node ,
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            rrel_event_year 
            )
            template .triple_with_relation (
            main_node >>"_main_node",
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            event_description_lnk ,
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            rrel_4 
            )
            template .triple (
            action_agent ,
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            "_main_node",
            )
            template .triple (
            initiated_node ,
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            "_main_node",
            )
            event_params =ScEventSubscriptionParams (main_node ,ScEventType .AFTER_GENERATE_INCOMING_ARC ,call_back )
            client .events_create (event_params )
            client .template_generate (template )
            global payload 
            if callback_event .wait (timeout =10 ):
                while not payload :
                    continue 
                return payload 
            else :
                raise AgentError (524 ,"Timeout")
        else :
            raise ScServerError 

    def call_delete_event_agent (self ,action_name :str ,username :str ,event_name :str )->str :
        """
        Метод для вызова агента удаления события
        :param action_name: Идентификатор action-ноды агента
        :param event_name: Название события
        :param username: Логин пользователя
        :return: Ответ сервера
        :raises AgentError: Возникает при истечении времени ожидания
        :raises ScServerError: Возникает при отсутствии запущенного sc-сервера
        """
        if is_connected ():

            event_name_lnk =create_link (client ,event_name )
            rrel_1 =client .resolve_keynodes (ScIdtfResolveParams (idtf ='rrel_1',type =sc_types .NODE_CONST_ROLE ))[0 ]
            rrel_2 =client .resolve_keynodes (ScIdtfResolveParams (idtf ='rrel_2',type =sc_types .NODE_CONST_ROLE ))[0 ]

            initiated_node =client .resolve_keynodes (ScIdtfResolveParams (idtf ='action_initiated',type =sc_types .NODE_CONST_CLASS ))[0 ]
            action_agent =client .resolve_keynodes (ScIdtfResolveParams (idtf =action_name ,type =sc_types .NODE_CONST_CLASS ))[0 ]
            main_node =get_node (client )

            user =get_user_by_login (username )
            template =ScTemplate ()
            template .triple_with_relation (
            main_node >>"_main_node",
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            user ,
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            rrel_1 
            )
            template .triple_with_relation (
            main_node >>"_main_node",
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            event_name_lnk ,
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            rrel_2 
            )
            template .triple (
            action_agent ,
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            "_main_node",
            )
            template .triple (
            initiated_node ,
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            "_main_node",
            )

            event_params =ScEventSubscriptionParams (main_node ,ScEventType .AFTER_GENERATE_INCOMING_ARC ,call_back )
            client .events_create (event_params )
            client .template_generate (template )
            global payload 
            if callback_event .wait (timeout =10 ):
                while not payload :
                    continue 
                return payload 
            else :
                raise AgentError (524 ,"Timeout")
        else :
            raise ScServerError 

    def call_show_event_agent (self ,action_name :str ,username :str )->str :
        """
        Метод для вызова агента просмотра события
        :param action_name: Идентификатор action-ноды агента
        :param username: Логин пользователя
        :return: Ответ сервера
        :raises AgentError: Возникает при истечении времени ожидания
        :raises ScServerError: Возникает при отсутствии запущенного sc-сервера
        """
        if is_connected ():

            rrel_1 =client .resolve_keynodes (ScIdtfResolveParams (idtf ='rrel_1',type =sc_types .NODE_CONST_ROLE ))[0 ]

            initiated_node =client .resolve_keynodes (ScIdtfResolveParams (idtf ='action_initiated',type =sc_types .NODE_CONST_CLASS ))[0 ]
            action_agent =client .resolve_keynodes (ScIdtfResolveParams (idtf =action_name ,type =sc_types .NODE_CONST_CLASS ))[0 ]
            main_node =get_node (client )

            user =get_user_by_login (username )
            template =ScTemplate ()
            template .triple_with_relation (
            main_node >>"_main_node",
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            user ,
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            rrel_1 
            )
            template .triple (
            action_agent ,
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            "_main_node",
            )
            template .triple (
            initiated_node ,
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            "_main_node",
            )

            event_params =ScEventSubscriptionParams (main_node ,ScEventType .AFTER_GENERATE_INCOMING_ARC ,call_back_get_events )
            client .events_create (event_params )
            client .template_generate (template )
            print ("here")
            global payload 
            if callback_event .wait (timeout =10 ):
                while not payload :
                    continue 
                return payload 
            else :
                raise AgentError (524 ,"Timeout")
        else :
            raise ScServerError 

    def call_choice_next_question_agent (self ,action_name :str ,username :str )->dict :
        """Вызов ChoiceNextQuestionAgent"""
        if is_connected ():
            from service .models import get_user_by_login 
            user =get_user_by_login (username )
            if not user :
                raise Exception (f"User node for {username } not found")

            rrel_1 =client .resolve_keynodes (ScIdtfResolveParams (idtf ='rrel_1',type =sc_types .NODE_CONST_ROLE ))[0 ]
            initiated_node =client .resolve_keynodes (ScIdtfResolveParams (idtf ='action_initiated',type =sc_types .NODE_CONST_CLASS ))[0 ]
            action_agent =client .resolve_keynodes (ScIdtfResolveParams (idtf =action_name ,type =sc_types .NODE_CONST_CLASS ))[0 ]
            main_node =get_node (client )

            template =ScTemplate ()
            template .triple_with_relation (main_node >>"_main_node",sc_types .EDGE_ACCESS_VAR_POS_PERM ,user ,sc_types .EDGE_ACCESS_VAR_POS_PERM ,rrel_1 )
            template .triple (action_agent ,sc_types .EDGE_ACCESS_VAR_POS_PERM ,"_main_node")
            template .triple (initiated_node ,sc_types .EDGE_ACCESS_VAR_POS_PERM ,"_main_node")

            event_params =ScEventSubscriptionParams (main_node ,ScEventType .AFTER_GENERATE_INCOMING_ARC ,call_back )
            client .events_create (event_params )
            client .template_generate (template )

            global payload 
            payload =None 

            if callback_event .wait (timeout =30 ):
                while not payload :
                    continue 
                return payload 
            else :
                raise AgentError (524 ,"Timeout")
        else :
            raise ScServerError 

    def call_search_answers_agent (self ,action_name :str ,question_addr )->dict :
        """Вызов SearchAnswersForQuestionAgent"""
        if is_connected ():
            rrel_1 =client .resolve_keynodes (ScIdtfResolveParams (idtf ='rrel_1',type =sc_types .NODE_CONST_ROLE ))[0 ]
            initiated_node =client .resolve_keynodes (ScIdtfResolveParams (idtf ='action_initiated',type =sc_types .NODE_CONST_CLASS ))[0 ]
            action_agent =client .resolve_keynodes (ScIdtfResolveParams (idtf =action_name ,type =sc_types .NODE_CONST_CLASS ))[0 ]
            main_node =get_node (client )

            template =ScTemplate ()
            template .triple_with_relation (main_node >>"_main_node",sc_types .EDGE_ACCESS_VAR_POS_PERM ,question_addr ,sc_types .EDGE_ACCESS_VAR_POS_PERM ,rrel_1 )
            template .triple (action_agent ,sc_types .EDGE_ACCESS_VAR_POS_PERM ,"_main_node")
            template .triple (initiated_node ,sc_types .EDGE_ACCESS_VAR_POS_PERM ,"_main_node")

            event_params =ScEventSubscriptionParams (main_node ,ScEventType .AFTER_GENERATE_INCOMING_ARC ,call_back )
            client .events_create (event_params )
            client .template_generate (template )

            global payload 
            payload =None 

            if callback_event .wait (timeout =30 ):
                while not payload :
                    continue 
                return payload 
            else :
                raise AgentError (524 ,"Timeout")
        else :
            raise ScServerError 

    def call_save_answer_agent (self ,action_name :str ,username :str ,answer_addr )->dict :
        """Вызов SaveAnswerAgent"""
        if is_connected ():
            from service .models import get_user_by_login 
            user =get_user_by_login (username )
            if not user :
                raise Exception (f"User node for {username } not found")

            rrel_1 =client .resolve_keynodes (ScIdtfResolveParams (idtf ='rrel_1',type =sc_types .NODE_CONST_ROLE ))[0 ]
            rrel_2 =client .resolve_keynodes (ScIdtfResolveParams (idtf ='rrel_2',type =sc_types .NODE_CONST_ROLE ))[0 ]
            initiated_node =client .resolve_keynodes (ScIdtfResolveParams (idtf ='action_initiated',type =sc_types .NODE_CONST_CLASS ))[0 ]
            action_agent =client .resolve_keynodes (ScIdtfResolveParams (idtf =action_name ,type =sc_types .NODE_CONST_CLASS ))[0 ]
            main_node =get_node (client )

            template =ScTemplate ()
            template .triple_with_relation (main_node >>"_main_node",sc_types .EDGE_ACCESS_VAR_POS_PERM ,answer_addr ,sc_types .EDGE_ACCESS_VAR_POS_PERM ,rrel_1 )
            template .triple_with_relation ("_main_node",sc_types .EDGE_ACCESS_VAR_POS_PERM ,user ,sc_types .EDGE_ACCESS_VAR_POS_PERM ,rrel_2 )
            template .triple (action_agent ,sc_types .EDGE_ACCESS_VAR_POS_PERM ,"_main_node")
            template .triple (initiated_node ,sc_types .EDGE_ACCESS_VAR_POS_PERM ,"_main_node")

            event_params =ScEventSubscriptionParams (main_node ,ScEventType .AFTER_GENERATE_INCOMING_ARC ,call_back )
            client .events_create (event_params )
            client .template_generate (template )

            global payload 
            payload =None 

            if callback_event .wait (timeout =30 ):
                while not payload :
                    continue 
                return payload 
            else :
                raise AgentError (524 ,"Timeout")
        else :
            raise ScServerError 


    def call_check_answer_agent (self ,action_name :str ,username :str ,question_addr )->dict :
        """CheckTheAnswerAgent"""
        if is_connected ():
            from service .models import get_user_by_login 

            user =get_user_by_login (username )
            if not user :
                raise Exception (f"User node for {username } not found")

            rrel_1 =client .resolve_keynodes (ScIdtfResolveParams (idtf ="rrel_1",type =sc_types .NODE_CONST_ROLE ))[0 ]
            rrel_2 =client .resolve_keynodes (ScIdtfResolveParams (idtf ="rrel_2",type =sc_types .NODE_CONST_ROLE ))[0 ]
            initiated_node =client .resolve_keynodes (ScIdtfResolveParams (idtf ="action_initiated",type =sc_types .NODE_CONST_CLASS ))[0 ]
            action_agent =client .resolve_keynodes (ScIdtfResolveParams (idtf =action_name ,type =sc_types .NODE_CONST_CLASS ))[0 ]

            main_node =get_node (client )

            template =ScTemplate ()
            template .triple_with_relation (main_node ,sc_types .EDGE_ACCESS_VAR_POS_PERM ,question_addr ,sc_types .EDGE_ACCESS_VAR_POS_PERM ,rrel_1 )
            template .triple_with_relation (main_node ,sc_types .EDGE_ACCESS_VAR_POS_PERM ,user ,sc_types .EDGE_ACCESS_VAR_POS_PERM ,rrel_2 )
            template .triple (action_agent ,sc_types .EDGE_ACCESS_VAR_POS_PERM ,main_node )
            template .triple (initiated_node ,sc_types .EDGE_ACCESS_VAR_POS_PERM ,main_node )


            event_params =ScEventSubscriptionParams (
            main_node ,
            ScEventType .AFTER_GENERATE_INCOMING_ARC ,
            callback_check_answer 
            )
            client .events_create (event_params )
            client .template_generate (template )

            global payload 
            payload =None 

            if callback_event .wait (timeout =30 ):
                while not payload :
                    continue 
                return payload 
            else :
                raise AgentError (524 ,"Timeout")
        else :
            raise ScServerError ()

    def call_search_answers_agent (self ,action_name :str ,question_addr :ScAddr )->dict :
        """Вызов SearchAnswersForQuestionAgent"""
        if is_connected ():
            rrel_1 =client .resolve_keynodes (ScIdtfResolveParams (idtf ='rrel_1',type =sc_types .NODE_CONST_ROLE ))[0 ]
            initiated_node =client .resolve_keynodes (ScIdtfResolveParams (idtf ='action_initiated',type =sc_types .NODE_CONST_CLASS ))[0 ]
            action_agent =client .resolve_keynodes (ScIdtfResolveParams (idtf =action_name ,type =sc_types .NODE_CONST_CLASS ))[0 ]
            main_node =get_node (client )

            template =ScTemplate ()
            template .triple_with_relation (main_node >>"_main_node",sc_types .EDGE_ACCESS_VAR_POS_PERM ,question_addr ,sc_types .EDGE_ACCESS_VAR_POS_PERM ,rrel_1 )
            template .triple (action_agent ,sc_types .EDGE_ACCESS_VAR_POS_PERM ,"_main_node")
            template .triple (initiated_node ,sc_types .EDGE_ACCESS_VAR_POS_PERM ,"_main_node")

            event_params =ScEventSubscriptionParams (main_node ,ScEventType .AFTER_GENERATE_INCOMING_ARC ,call_back )
            client .events_create (event_params )
            client .template_generate (template )

            global payload 
            if callback_event .wait (timeout =10 ):
                while not payload :
                    continue 
                return payload 
            else :
                raise AgentError (524 ,"Timeout")
        else :
            raise ScServerError 


    def call_delete_old_nodes_agent (self ,action_name :str ,username :str )->dict :
        """Вызов DeleteOldNodesAgent"""
        if is_connected ():
            print (1 )
            rrel_1 =client .resolve_keynodes (
            ScIdtfResolveParams (idtf ='rrel_1',type =sc_types .NODE_CONST_ROLE )
            )[0 ]
            initiated_node =client .resolve_keynodes (
            ScIdtfResolveParams (idtf ='action_initiated',type =sc_types .NODE_CONST_CLASS )
            )[0 ]
            action_agent =client .resolve_keynodes (
            ScIdtfResolveParams (idtf =action_name ,type =sc_types .NODE_CONST_CLASS )
            )[0 ]
            main_node =get_node (client )

            print (2 )
            username_str =str (username )


            from service .models import get_user_by_login 
            user =get_user_by_login (username_str )
            print (f"DEBUG: user from get_user_by_login = {user }")
            if not user :
                raise Exception (f"User node for {username_str } not found")

            print (3 )
            template =ScTemplate ()
            template .triple_with_relation (
            main_node >>"_main_node",
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            user ,
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            rrel_1 ,
            )
            template .triple (
            action_agent ,
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            "_main_node",
            )
            template .triple (
            initiated_node ,
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            "_main_node",
            )

            print (4 )
            print (f"DEBUG: Creating event subscription for main_node = {main_node }")
            event_params =ScEventSubscriptionParams (
            main_node ,
            ScEventType .AFTER_GENERATE_INCOMING_ARC ,
            call_back ,
            )
            client .events_create (event_params )

            print (5 )
            print (f"DEBUG: Generating template, waiting for agent response...")
            client .template_generate (template )
            print (6 )

            print ("DEBUG: Waiting for callback event (timeout=30)...")
            global payload 
            payload =None 

            if callback_event .wait (timeout =30 ):
                print (f"DEBUG: Callback event received! payload = {payload }")
                while not payload :
                    continue 
                print (f"DEBUG: Returning payload = {payload }")
                return payload 
            else :
                print ("DEBUG: Timeout! Agent didn't respond in 30 seconds")
                raise AgentError (524 ,"Timeout")
        else :
            raise ScServerError 

    def call_rating_update_agent (self ,action_name :str ,username :str )->dict :
        """RatingUpdateAgent"""
        if is_connected ():
            from service .models import get_user_by_login 

            user =get_user_by_login (username )
            if not user :
                raise Exception (f"User node for {username } not found")

            rrel_1 =client .resolve_keynodes (ScIdtfResolveParams (idtf ="rrel_1",type =sc_types .NODE_CONST_ROLE ))[0 ]
            initiated_node =client .resolve_keynodes (ScIdtfResolveParams (idtf ="action_initiated",type =sc_types .NODE_CONST_CLASS ))[0 ]
            action_agent =client .resolve_keynodes (ScIdtfResolveParams (idtf =action_name ,type =sc_types .NODE_CONST_CLASS ))[0 ]

            main_node =get_node (client )

            template =ScTemplate ()
            template .triple_with_relation (
            main_node ,
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            user ,
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            rrel_1 
            )
            template .triple (action_agent ,sc_types .EDGE_ACCESS_VAR_POS_PERM ,main_node )
            template .triple (initiated_node ,sc_types .EDGE_ACCESS_VAR_POS_PERM ,main_node )


            event_params =ScEventSubscriptionParams (
            main_node ,
            ScEventType .AFTER_GENERATE_INCOMING_ARC ,
            callback_rating 
            )
            client .events_create (event_params )
            client .template_generate (template )

            global payload 
            payload =None 

            if callback_event .wait (timeout =30 ):
                while not payload :
                    continue 
                return payload 
            else :
                raise AgentError (524 ,"Timeout")
        else :
            raise ScServerError ()





    def call_add_topic_agent (self ,action_name :str ,username :str ,title :str ,description :str ):
        """Создает новый топик на форуме"""
        if is_connected ():
            from service .models import get_user_by_login 
            user =get_user_by_login (username )
            if not user :
                raise Exception (f"User not found: {username }")


            title_link =create_link (client ,title )
            description_link =create_link (client ,description )


            rrel_1 =client .resolve_keynodes (ScIdtfResolveParams (idtf ="rrel_1",type =sc_types .NODE_CONST_ROLE ))[0 ]
            rrel_2 =client .resolve_keynodes (ScIdtfResolveParams (idtf ="rrel_2",type =sc_types .NODE_CONST_ROLE ))[0 ]
            rrel_3 =client .resolve_keynodes (ScIdtfResolveParams (idtf ="rrel_3",type =sc_types .NODE_CONST_ROLE ))[0 ]
            initiated_node =client .resolve_keynodes (ScIdtfResolveParams (idtf ="action_initiated",type =sc_types .NODE_CONST_CLASS ))[0 ]
            action_agent =client .resolve_keynodes (ScIdtfResolveParams (idtf =action_name ,type =sc_types .NODE_CONST_CLASS ))[0 ]


            main_node =get_node (client )

            template =ScTemplate ()
            template .triple_with_relation (
            main_node ,
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            user ,
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            rrel_1 
            )
            template .triple_with_relation (
            main_node ,
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            title_link ,
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            rrel_2 
            )
            template .triple_with_relation (
            main_node ,
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            description_link ,
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            rrel_3 
            )
            template .triple (action_agent ,sc_types .EDGE_ACCESS_VAR_POS_PERM ,main_node )
            template .triple (initiated_node ,sc_types .EDGE_ACCESS_VAR_POS_PERM ,main_node )

            event_params =ScEventSubscriptionParams (main_node ,ScEventType .AFTER_GENERATE_INCOMING_ARC ,call_back )
            client .events_create (event_params )
            client .template_generate (template )

            global payload 
            payload =None 
            if callback_event .wait (timeout =10 ):
                while not payload :
                    continue 
                return payload 
            else :
                raise AgentError (524 ,"Timeout")
        else :
            raise ScServerError ()


    def call_add_message_agent (self ,action_name :str ,username :str ,topic_addr :ScAddr ,message_text :str ):
        """Добавляет сообщение в топик"""
        if is_connected ():
            from service .models import get_user_by_login 
            user =get_user_by_login (username )
            if not user :
                raise Exception (f"User not found: {username }")


            message_link =create_link (client ,message_text )


            rrel_1 =client .resolve_keynodes (ScIdtfResolveParams (idtf ="rrel_1",type =sc_types .NODE_CONST_ROLE ))[0 ]
            rrel_2 =client .resolve_keynodes (ScIdtfResolveParams (idtf ="rrel_2",type =sc_types .NODE_CONST_ROLE ))[0 ]
            rrel_3 =client .resolve_keynodes (ScIdtfResolveParams (idtf ="rrel_3",type =sc_types .NODE_CONST_ROLE ))[0 ]
            initiated_node =client .resolve_keynodes (ScIdtfResolveParams (idtf ="action_initiated",type =sc_types .NODE_CONST_CLASS ))[0 ]
            action_agent =client .resolve_keynodes (ScIdtfResolveParams (idtf =action_name ,type =sc_types .NODE_CONST_CLASS ))[0 ]


            main_node =get_node (client )

            template =ScTemplate ()
            template .triple_with_relation (
            main_node ,
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            user ,
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            rrel_1 
            )
            template .triple_with_relation (
            main_node ,
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            topic_addr ,
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            rrel_2 
            )
            template .triple_with_relation (
            main_node ,
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            message_link ,
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            rrel_3 
            )
            template .triple (action_agent ,sc_types .EDGE_ACCESS_VAR_POS_PERM ,main_node )
            template .triple (initiated_node ,sc_types .EDGE_ACCESS_VAR_POS_PERM ,main_node )

            event_params =ScEventSubscriptionParams (main_node ,ScEventType .AFTER_GENERATE_INCOMING_ARC ,call_back )
            client .events_create (event_params )
            client .template_generate (template )

            global payload 
            payload =None 
            if callback_event .wait (timeout =10 ):
                while not payload :
                    continue 
                return payload 
            else :
                raise AgentError (524 ,"Timeout")
        else :
            raise ScServerError ()


    def get_all_topics (self ):
        """Получает список всех топиков форума"""
        if is_connected ():
            try :
                concept_topic =client .resolve_keynodes (ScIdtfResolveParams (idtf ="concept_topic",type =sc_types .NODE_CONST_CLASS ))[0 ]
                print (f"DEBUG: concept_topic = {concept_topic }")

                nrel_topic_title =client .resolve_keynodes (ScIdtfResolveParams (idtf ="nrel_topic_title",type =sc_types .NODE_CONST_NOROLE ))[0 ]
                nrel_author =client .resolve_keynodes (ScIdtfResolveParams (idtf ="nrel_author",type =sc_types .NODE_CONST_NOROLE ))[0 ]


                template =ScTemplate ()
                template .triple (
                concept_topic ,
                sc_types .EDGE_ACCESS_VAR_POS_PERM >>"_topic_arc",
                sc_types .NODE_VAR >>"_topic"
                )

                result =client .template_search (template )
                print (f"DEBUG: Found {len (result )} topics")
                topics =[]

                for item in result :
                    topic_addr =item .get ("_topic")


                    title_template =ScTemplate ()
                    title_template .triple (
                    topic_addr ,
                    sc_types .EDGE_D_COMMON_VAR >>"_title_arc",
                    sc_types .LINK_VAR >>"_title_link"
                    )
                    title_template .triple (
                    nrel_topic_title ,
                    sc_types .EDGE_ACCESS_VAR_POS_PERM ,
                    "_title_arc"
                    )

                    title_result =client .template_search (title_template )
                    title =""
                    if title_result :
                        title_link =title_result [0 ].get ("_title_link")
                        title =client .get_link_content (title_link )[0 ].data 


                    author_template =ScTemplate ()
                    author_template .triple (
                    topic_addr ,
                    sc_types .EDGE_D_COMMON_VAR >>"_author_arc",
                    sc_types .NODE_VAR >>"_author"
                    )
                    author_template .triple (
                    nrel_author ,
                    sc_types .EDGE_ACCESS_VAR_POS_PERM ,
                    "_author_arc"
                    )

                    author_result =client .template_search (author_template )
                    author_display ="Unknown"
                    if author_result :
                        author_addr =author_result [0 ].get ("_author")
                        author_display =self .format_user_display (author_addr )

                    topics .append ({
                    'addr':topic_addr .value ,
                    'title':title ,
                    'author':author_display 
                    })

                return topics 

            except Exception as e :
                print (f"Error getting topics: {e }")
                return []
        else :
            raise ScServerError ()


    def get_topic_details (self ,topic_addr :ScAddr ):
        """Получает детали топика: заголовок, описание, автор"""
        if is_connected ():
            try :
                nrel_topic_title =client .resolve_keynodes (ScIdtfResolveParams (idtf ="nrel_topic_title",type =sc_types .NODE_CONST_NOROLE ))[0 ]
                nrel_topic_description =client .resolve_keynodes (ScIdtfResolveParams (idtf ="nrel_topic_description",type =sc_types .NODE_CONST_NOROLE ))[0 ]
                nrel_author =client .resolve_keynodes (ScIdtfResolveParams (idtf ="nrel_author",type =sc_types .NODE_CONST_NOROLE ))[0 ]


                title_template =ScTemplate ()
                title_template .triple (
                topic_addr ,
                sc_types .EDGE_D_COMMON_VAR >>"_title_arc",
                sc_types .LINK_VAR >>"_title_link"
                )
                title_template .triple (
                nrel_topic_title ,
                sc_types .EDGE_ACCESS_VAR_POS_PERM ,
                "_title_arc"
                )

                title_result =client .template_search (title_template )
                title =""
                if title_result :
                    title_link =title_result [0 ].get ("_title_link")
                    title =client .get_link_content (title_link )[0 ].data 


                desc_template =ScTemplate ()
                desc_template .triple (
                topic_addr ,
                sc_types .EDGE_D_COMMON_VAR >>"_desc_arc",
                sc_types .LINK_VAR >>"_desc_link"
                )
                desc_template .triple (
                nrel_topic_description ,
                sc_types .EDGE_ACCESS_VAR_POS_PERM ,
                "_desc_arc"
                )

                desc_result =client .template_search (desc_template )
                description =""
                if desc_result :
                    desc_link =desc_result [0 ].get ("_desc_link")
                    description =client .get_link_content (desc_link )[0 ].data 


                author_template =ScTemplate ()
                author_template .triple (
                topic_addr ,
                sc_types .EDGE_D_COMMON_VAR >>"_author_arc",
                sc_types .NODE_VAR >>"_author"
                )
                author_template .triple (
                nrel_author ,
                sc_types .EDGE_ACCESS_VAR_POS_PERM ,
                "_author_arc"
                )

                author_result =client .template_search (author_template )
                author_display ="Unknown"
                if author_result :
                    author_addr =author_result [0 ].get ("_author")
                    author_display =self .format_user_display (author_addr )

                return {
                'title':title ,
                'description':description ,
                'author':author_display 
                }

            except Exception as e :
                print (f"Error getting topic details: {e }")
                return {
                'title':'Unknown',
                'description':'',
                'author':'Unknown'
                }
        else :
            raise ScServerError ()


    def get_topic_messages (self ,topic_addr :ScAddr ):
        """Получает все сообщения топика"""
        if is_connected ():
            try :
                concept_message =client .resolve_keynodes (ScIdtfResolveParams (idtf ="concept_message",type =sc_types .NODE_CONST_CLASS ))[0 ]
                nrel_message_content =client .resolve_keynodes (ScIdtfResolveParams (idtf ="nrel_message_content",type =sc_types .NODE_CONST_NOROLE ))[0 ]
                nrel_message_author =client .resolve_keynodes (ScIdtfResolveParams (idtf ="nrel_message_author",type =sc_types .NODE_CONST_NOROLE ))[0 ]

                print (f"DEBUG: Looking for messages in topic {topic_addr }")


                template =ScTemplate ()
                template .triple (
                topic_addr ,
                sc_types .EDGE_ACCESS_VAR_POS_PERM >>"_msg_arc",
                sc_types .NODE_VAR >>"_message"
                )
                template .triple (
                concept_message ,
                sc_types .EDGE_ACCESS_VAR_POS_PERM ,
                "_message"
                )

                result =client .template_search (template )
                print (f"DEBUG: Found {len (result )} messages")
                messages =[]

                for item in result :
                    message_addr =item .get ("_message")
                    print (f"DEBUG: Processing message {message_addr }")


                    content_template =ScTemplate ()
                    content_template .triple (
                    message_addr ,
                    sc_types .EDGE_D_COMMON_VAR >>"_content_arc",
                    sc_types .LINK_VAR >>"_content_link"
                    )
                    content_template .triple (
                    nrel_message_content ,
                    sc_types .EDGE_ACCESS_VAR_POS_PERM ,
                    "_content_arc"
                    )

                    content_result =client .template_search (content_template )
                    content =""
                    if content_result :
                        content_link =content_result [0 ].get ("_content_link")
                        content =client .get_link_content (content_link )[0 ].data 
                        print (f"DEBUG: Message content: {content }")
                    else :
                        print (f"DEBUG: No content found for message {message_addr }")


                    author_template =ScTemplate ()
                    author_template .triple (
                    message_addr ,
                    sc_types .EDGE_D_COMMON_VAR >>"_author_arc",
                    sc_types .NODE_VAR >>"_author"
                    )
                    author_template .triple (
                    nrel_message_author ,
                    sc_types .EDGE_ACCESS_VAR_POS_PERM ,
                    "_author_arc"
                    )

                    author_result =client .template_search (author_template )
                    author_display ="Unknown"
                    if author_result :
                        author_addr =author_result [0 ].get ("_author")
                        author_display =self .format_user_display (author_addr )
                        print (f"DEBUG: Message author: {author_display }")
                    else :
                        print (f"DEBUG: No author found for message {message_addr }")

                    messages .append ({
                    'content':content ,
                    'author':author_display 
                    })

                print (f"DEBUG: Returning {len (messages )} messages")
                return messages 

            except Exception as e :
                print (f"Error getting messages: {e }")
                import traceback 
                traceback .print_exc ()
                return []
        else :
            raise ScServerError ()



    def format_user_display (self ,user_addr :ScAddr ):
        """Форматирует отображение пользователя: email (тип, ранг для специалистов)"""
        try :
            nrel_system_identifier =client .resolve_keynodes (
            ScIdtfResolveParams (idtf ="nrel_system_identifier",type =sc_types .NODE_CONST_NOROLE )
            )[0 ]
            concept_specialist =client .resolve_keynodes (
            ScIdtfResolveParams (idtf ="concept_specialist",type =sc_types .NODE_CONST_CLASS )
            )[0 ]


            email_template =ScTemplate ()
            email_template .triple (
            user_addr ,
            sc_types .EDGE_D_COMMON_VAR >>"_email_arc",
            sc_types .LINK_VAR >>"_email_link"
            )
            email_template .triple (
            nrel_system_identifier ,
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            "_email_arc"
            )

            email_result =client .template_search (email_template )
            email ="Unknown"
            if email_result :
                email_link =email_result [0 ].get ("_email_link")
                email =client .get_link_content (email_link )[0 ].data 


            specialist_template =ScTemplate ()
            specialist_template .triple (
            concept_specialist ,
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            user_addr 
            )
            is_specialist =len (client .template_search (specialist_template ))>0 


            if is_specialist :
                nrel_selected_answers =client .resolve_keynodes (
                ScIdtfResolveParams (idtf ="nrel_selected_answers",type =sc_types .NODE_CONST_NOROLE )
                )[0 ]
                concept_correct_answer =client .resolve_keynodes (
                ScIdtfResolveParams (idtf ="concept_correct_answer",type =sc_types .NODE_CONST_CLASS )
                )[0 ]

                answers_template =ScTemplate ()
                answers_template .triple (
                user_addr ,
                sc_types .EDGE_D_COMMON_VAR >>"_answers_arc",
                sc_types .NODE_VAR >>"_answers_set"
                )
                answers_template .triple (
                nrel_selected_answers ,
                sc_types .EDGE_ACCESS_VAR_POS_PERM ,
                "_answers_arc"
                )
                answers_template .triple (
                "_answers_set",
                sc_types .EDGE_ACCESS_VAR_POS_PERM >>"_answer_arc",
                sc_types .NODE_VAR >>"_answer"
                )

                answers_result =client .template_search (answers_template )

                total_answers =len (answers_result )
                correct_count =0 

                for answer_item in answers_result :
                    answer_addr =answer_item .get ("_answer")

                    correct_template =ScTemplate ()
                    correct_template .triple (
                    concept_correct_answer ,
                    sc_types .EDGE_ACCESS_VAR_POS_PERM ,
                    answer_addr 
                    )

                    if len (client .template_search (correct_template ))>0 :
                        correct_count +=1 

                rating =correct_count if total_answers >0 else 0 


                if rating >=8 :
                    rank_str ="первый ранг"
                elif rating >=5 :
                    rank_str ="второй ранг"
                else :
                    rank_str ="третий ранг"

                return f"{email } (Специалист, {rank_str })"
            else :
                return f"{email } (Клиент)"

        except Exception as e :
            print (f"Error formatting user display: {e }")
            return "Unknown"

class OstisVerificationAgent (VerificationAgent ):
    """
    Класс для реализации агента верификации через OSTIS
    """

    def __init__ (self ):
        self .ostis =Ostis (Config .OSTIS_URL )

    def send_token (self ,email :str )->dict :
        """
        Отправка токена верификации на email
        
        :param email: Email пользователя
        :return: Словарь со статусом
        """
        try :
            global payload 
            payload =None 

            agent_response =self .ostis .call_verification_agent (
            action_name ="action_verification",
            email =email ,
            token =None 
            )

            if agent_response and agent_response .get ('message')==result .SUCCESS :
                return {
                "status":VerificationStatus .TOKEN_SENT ,
                "message":"Токен отправлен на email"
                }
            else :
                return {
                "status":VerificationStatus .INVALID ,
                "message":"Не удалось отправить токен"
                }
        except Exception as e :
            print (f"Error in send_token: {e }")
            return {
            "status":VerificationStatus .INVALID ,
            "message":str (e )
            }

    def verify_token (self ,email :str ,token :str )->dict :
        """
        Проверка токена верификации
        
        :param email: Email пользователя
        :param token: Токен для проверки
        :return: Словарь со статусом
        """
        try :
            global payload 
            payload =None 

            agent_response =self .ostis .call_verification_agent (
            action_name ="action_verification",
            email =email ,
            token =token 
            )

            if agent_response and agent_response .get ('message')==result .SUCCESS :
                return {
                "status":VerificationStatus .EMAIL_VERIFIED ,
                "message":"Email успешно подтвержден"
                }
            else :
                return {
                "status":VerificationStatus .INVALID ,
                "message":"Неверный код подтверждения"
                }
        except Exception as e :
            print (f"Error in verify_token: {e }")
            return {
            "status":VerificationStatus .INVALID ,
            "message":str (e )
            }



class OstisRegAgent (RegAgent ):
    def __init__ (self ):
        self .ostis =Ostis (Config .OSTIS_URL )

    def reg_agent (
    self ,
    email :str ,
    password :str ,
    password_conf :str ,
    user_type :str ,
    full_name :str =None ,
    gender :str =None ,
    age :str =None ,
    experience :str =None ,
    field :str =None 
    )->dict :
        try :
            global payload 
            payload =None 

            agent_response =self .ostis .call_registration_agent (
            action_name ="action_user_registration",
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

            if not isinstance (agent_response ,dict ):
                return {
                "status":RegStatus .EXISTS ,
                "message":"Invalid response from agent"
                }

            if agent_response and agent_response .get ('message')==result .SUCCESS :
                return {
                "status":RegStatus .CREATED ,
                "message":"Пользователь успешно зарегистрирован"
                }
            else :
                error_msg ="Ошибка регистрации"
                if isinstance (agent_response ,dict ):
                    error_msg =agent_response .get ('message',error_msg )

                return {
                "status":RegStatus .EXISTS ,
                "message":str (error_msg )
                }
        except Exception as e :
            return {
            "status":RegStatus .EXISTS ,
            "message":str (e )
            }

class OstisAuthAgent (AuthAgent ):
    """
    Класс для реализации агента аутентификации через OSTIS
    """

    def __init__ (self ):
        self .ostis =Ostis (Config .OSTIS_URL )

    def auth_agent (self ,username :str ,password :str )->dict :
        """
        Метод для запуска агента аутентификации
        
        :param username: Email пользователя (теперь это email!)
        :param password: Пароль пользователя
        :return: Словарь со статусом результата выполнения агента аутентификации
        """
        try :
            global payload 
            payload =None 

            agent_response =self .ostis .call_auth_agent (
            action_name ="action_authentication",
            email =username ,
            password =password 
            )

            if agent_response and agent_response .get ('message')==result .SUCCESS :
                return {
                "status":AuthStatus .VALID ,
                "message":"Authentication successful"
                }
            else :
                return {
                "status":AuthStatus .INVALID ,
                "message":"Invalid credentials or email not verified"
                }
        except Exception as e :
            print (f"Error in auth_agent: {e }")
            return {
            "status":AuthStatus .INVALID ,
            "message":str (e )
            }


class OstisUserRequestAgent (RequestAgent ):
    """
    Класс для представления агента юридических запросов
    """
    def __init__ (self ):
        self .ostis =Ostis (Config .OSTIS_URL )

    def request_agent (self ,content :str ):
        """
        Метод для запуска агента юридических запросов
        :param content: Контент, по которому происходит поиск в БЗ
        :return: Словарь со статусом результата выполнения агента юридических запросов
        """
        try:
            agent_response = self.ostis.call_user_request_agent(
                action_name="action_user_request",
                content=content,
            )
            if agent_response and isinstance(agent_response.get("message"), list):
                return {"status": RequestStatus.VALID, "message": agent_response["message"]}
            return {"status": RequestStatus.INVALID, "message": None}
        except Exception as e:
            print(f"[REQUEST] request_agent error: {e}")
            return {"status": RequestStatus.INVALID, "message": None}

class OstisDirectoryAgent (DirectoryAgent ):
    """
    Класс для представления агента поиска
    """
    def __init__ (self ):
        self .ostis =Ostis (Config .OSTIS_URL )

    def directory_agent (self ,content :str ):
        """
        Метод для запуска агента поиска
        :param content: Контент, по которому происходит поиск в БЗ
        :return: Словарь со статусом результата выполнения агента поиска
        """
        global payload 
        payload =None 
        agent_response =self .ostis .call_directory_agent (
        action_name ="action_search",
        content =content 
        )
        if agent_response is not None :
            return {"status":DirectoryStatus .VALID ,
            "message":agent_response ["message"]}
        elif agent_response is None :
            return {
            "status":DirectoryStatus .INVALID ,
            "message":"Invalid credentials",
            }
        raise AgentError 

class OstisAddEventAgent (AddEventAgent ):
    """
    Класс для представления агента добавления события
    """
    def __init__ (self ):
        self .ostis =Ostis (Config .OSTIS_URL )

    def add_event_agent (self ,
    user_name :ScAddr ,
    event_name :str ,
    event_date ,
    event_description :str 
    ):
        """
        Метод для запуска агента добавления события
        :param user_name: Логин пользователя
        :param event_name: Название события
        :param event_date: Дата события
        :param event_description: Описание события
        :return:
        """
        global payload 
        payload =None 
        agent_response =self .ostis .call_add_event_agent (
        action_name ="action_add_event",
        user_name =user_name ,
        event_name =event_name ,
        event_date =event_date ,
        event_description =event_description 
        )
        if agent_response is not None :
            return {"status":AddEventStatus .VALID ,
            "message":agent_response ["message"]}
        elif agent_response is None :
            return {
            "status":AddEventStatus .INVALID ,
            "message":"Invalid credentials",
            }
        raise AgentError 

class OstisDeleteEventAgent (DeleteEventAgent ):
    """
    Класс для представления агента удаления события
    """
    def __init__ (self ):
        self .ostis =Ostis (Config .OSTIS_URL )

    def delete_event_agent (self ,
    username :str ,
    event_name :str ,
    ):
        """
        Метод для запуска агента удаления события
        :param event_name: Название события
        :param username: Логин пользователя
        :return:
        """
        global payload 
        payload =None 
        agent_response =self .ostis .call_delete_event_agent (
        action_name ="action_del_event",
        username =username ,
        event_name =event_name ,
        )
        if agent_response is not None :
            return {"status":DeleteEventStatus .VALID ,
            "message":agent_response ["message"]}
        elif agent_response is None :
            return {
            "status":DeleteEventStatus .INVALID ,
            "message":"Invalid credentials",
            }
        raise AgentError 

class OstisShowEventAgent (ShowEventAgent ):
    """
    Класс для представления агента просмотра события
    """
    def __init__ (self ):
        self .ostis =Ostis (Config .OSTIS_URL )

    def show_event_agent (self ,
    username 
    ):
        """
        Метод для запуска агента просмотра события
        :param username: Логин пользователя
        :return:
        """
        global payload 
        payload =None 
        agent_response =self .ostis .call_show_event_agent (
        action_name ="action_user_events",
        username =username 
        )
        if agent_response is not None :
            return {"status":ShowEventStatus .VALID ,
            "message":agent_response ["message"]}
        elif agent_response is None :
            return {
            "status":ShowEventStatus .INVALID ,
            "message":"Invalid credentials",
            }

class OstisTestAgent (TestAgent ):
    """Класс для работы с тестовыми агентами"""

    def __init__ (self ):
        self .ostis =Ostis (Config .OSTIS_URL )

    def get_next_question (self ,username :str ):
        """Вызывает ChoiceNextQuestionAgent"""
        try :
            from service .models import get_user_by_login 
            from sc_client .client import create_elements_by_scs 

            global payload 
            payload =None 

            agent_response =self .ostis .call_choice_next_question_agent (
            action_name ="action_choice_next_question",
            username =username 
            )

            if agent_response and agent_response .get ('message')==result .SUCCESS :

                user_addr =get_user_by_login (username )
                if not user_addr :
                    return {"status":TestStatus .INVALID ,"message":"User not found"}


                nrel_asked_questions =client .resolve_keynodes (
                ScIdtfResolveParams (idtf ='nrel_asked_questions',type =sc_types .NODE_CONST_NOROLE )
                )[0 ]


                template =ScTemplate ()
                template .quintuple (
                user_addr ,
                sc_types .EDGE_D_COMMON_VAR ,
                sc_types .NODE_VAR >>"_asked_questions",
                sc_types .EDGE_ACCESS_VAR_POS_PERM ,
                nrel_asked_questions 
                )

                search_result =client .template_search (template )
                if search_result and len (search_result )>0 :
                    asked_questions_set =search_result [0 ].get ("_asked_questions")


                    questions_template =ScTemplate ()
                    questions_template .triple (
                    asked_questions_set ,
                    sc_types .EDGE_ACCESS_VAR_POS_PERM ,
                    sc_types .NODE_VAR >>"_question"
                    )

                    questions_result =client .template_search (questions_template )

                    if questions_result and len (questions_result )>0 :

                        last_question =questions_result [-1 ].get ("_question")


                        links =client .get_links_by_content (str (last_question ))

                        return {
                        "status":TestStatus .VALID ,
                        "question":str (last_question .value ),
                        "question_addr":last_question 
                        }

                return {"status":TestStatus .INVALID ,"message":"No questions found"}
            return {"status":TestStatus .INVALID ,"message":"Failed to get next question"}
        except Exception as e :
            print (f"Error in get_next_question: {e }")
            import traceback 
            traceback .print_exc ()
            return {"status":TestStatus .INVALID ,"message":str (e )}

    def get_answers_for_question (self ,question_addr ):
        """Вызывает SearchAnswersForQuestionAgent"""
        try :
            global payload 
            payload =None 

            agent_response =self .ostis .call_search_answers_agent (
            action_name ="action_search_answers_for_question",
            question_addr =question_addr 
            )

            if agent_response and agent_response .get ('message')==result .SUCCESS :

                nrel_answer =client .resolve_keynodes (
                ScIdtfResolveParams (idtf ='nrel_answer',type =sc_types .NODE_CONST_NOROLE )
                )[0 ]


                answers_template =ScTemplate ()
                answers_template .quintuple (
                question_addr ,
                sc_types .EDGE_D_COMMON_VAR ,
                sc_types .NODE_VAR >>"_answer",
                sc_types .EDGE_ACCESS_VAR_POS_PERM ,
                nrel_answer 
                )

                answers_result =client .template_search (answers_template )

                answers =[]
                if answers_result and len (answers_result )>0 :
                    for item in answers_result :
                        answer_addr =item .get ("_answer")
                        answers .append ({
                        "answer_addr":answer_addr ,
                        "answer_id":str (answer_addr .value )
                        })

                return {
                "status":TestStatus .VALID ,
                "answers":answers 
                }
            return {"status":TestStatus .INVALID ,"message":"Failed to get answers"}
        except Exception as e :
            print (f"Error in get_answers_for_question: {e }")
            import traceback 
            traceback .print_exc ()
            return {"status":TestStatus .INVALID ,"message":str (e )}


    def save_answer (self ,username :str ,answer_addr ):
        """Вызывает SaveAnswerAgent"""
        try :
            global payload 
            payload =None 

            agent_response =self .ostis .call_save_answer_agent (
            action_name ="action_save_answer",
            username =username ,
            answer_addr =answer_addr 
            )

            if agent_response and agent_response .get ('message')==result .SUCCESS :
                return {"status":TestStatus .VALID }
            return {"status":TestStatus .INVALID ,"message":"Failed to save answer"}
        except Exception as e :
            print (f"Error in save_answer: {e }")
            return {"status":TestStatus .INVALID ,"message":str (e )}

    def check_answer (self ,username :str ,question_addr ):
        """CheckTheAnswerAgent"""
        try :
            global payload 
            payload =None 

            agent_response =self .ostis .call_check_answer_agent (
            action_name ="action_check_answer",
            username =username ,
            question_addr =question_addr 
            )

            if agent_response and agent_response .get ("message")==result .SUCCESS :
                is_correct =agent_response .get ("is_correct",False )
                return {"status":TestStatus .VALID ,"is_correct":is_correct }

            return {"status":TestStatus .INVALID ,"message":"Failed to check answer"}
        except Exception as e :
            print (f"Error in check_answer: {e }")
            return {"status":TestStatus .INVALID ,"message":str (e )}

    def delete_old_test_data (self ,username :str ):
        """Вызывает DeleteOldNodesAgent"""
        try :
            global payload 
            payload =None 

            agent_response =self .ostis .call_delete_old_nodes_agent (
            action_name ="action_delete_old_nodes",
            username =username 
            )

            if agent_response and agent_response .get ('message')==result .SUCCESS :
                return {"status":TestStatus .VALID }
            return {"status":TestStatus .INVALID ,"message":"Failed"}
        except Exception as e :
            print (f"Error in delete_old_test_data: {e }")
            return {"status":TestStatus .INVALID ,"message":str (e )}



    def update_rating (self ,username :str ):
        """RatingUpdateAgent — теперь возвращает ранг"""
        try :
            global payload 
            payload =None 

            agent_response =self .ostis .call_rating_update_agent (
            action_name ="action_update_rating",
            username =username 
            )

            print (f"DEBUG: agent_response = {agent_response }")

            if agent_response and agent_response .get ("message")==result .SUCCESS :

                rank =agent_response .get ("rating","третий ранг")
                print (f"DEBUG: Rank extracted = {rank }")
                return {"status":TestStatus .VALID ,"rating":rank }

            return {"status":TestStatus .INVALID ,"message":"Failed to update rating"}
        except Exception as e :
            print (f"Error in update_rating: {e }")
            import traceback
            traceback .print_exc ()
            return {"status":TestStatus .INVALID ,"message":str (e )}


# ============================================================================
# CABINET AGENTS - Profile, History, Bookmarks, Notes
# ============================================================================

# ---------------------------------------------------------------------------
# Shared helpers (module-level, used by all cabinet agents)
# ---------------------------------------------------------------------------

def _resolve_kn(idtf: str, kn_type=sc_types.NODE_CONST_NOROLE) -> ScAddr:
    """Resolve a single keynode by identifier, creating it if absent."""
    return client.resolve_keynodes(
        ScIdtfResolveParams(idtf=idtf, type=kn_type)
    )[0]


def _get_link_attr(node_addr: ScAddr, rel_idtf: str) -> str:
    """Read the string content of a link reachable via a nrel quintuple."""
    try:
        rel = _resolve_kn(rel_idtf)
        t = ScTemplate()
        t.quintuple(node_addr, sc_types.EDGE_D_COMMON_VAR,
                    sc_types.LINK_VAR >> '_v',
                    sc_types.EDGE_ACCESS_VAR_POS_PERM, rel)
        r = client.template_search(t)
        if r:
            c = client.get_link_content(r[0].get('_v'))
            if c:
                return c[0].data
    except Exception as exc:
        print(f"[CABINET] _get_link_attr({rel_idtf}): {exc}")
    return ''


def _set_link_attr(node_addr: ScAddr, rel_idtf: str, value: str):
    """Write (or update) a string link attribute via a nrel quintuple."""
    try:
        rel = _resolve_kn(rel_idtf)
        t = ScTemplate()
        t.quintuple(node_addr, sc_types.EDGE_D_COMMON_VAR >> '_edge',
                    sc_types.LINK_VAR >> '_v',
                    sc_types.EDGE_ACCESS_VAR_POS_PERM, rel)
        results = client.template_search(t)
        if results:
            link_addr = results[0].get('_v')
            client.set_link_contents(ScLinkContent(value, ScLinkContentType.STRING, addr=link_addr))
        else:
            lc = ScLinkContent(value, ScLinkContentType.STRING)
            con = ScConstruction()
            con.create_link(sc_types.LINK_CONST, lc, 'lnk')
            con.create_edge(sc_types.EDGE_D_COMMON_CONST, node_addr, 'lnk', 'edge')
            con.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, rel, 'edge')
            client.generate_elements(con)
    except Exception as exc:
        print(f"[CABINET] _set_link_attr({rel_idtf}): {exc}")


# ---------------------------------------------------------------------------

class OstisProfileAgent(ProfileAgent):
    """Агент профиля пользователя — прямые операции с SC-памятью."""

    def _is_specialist(self, user_addr: ScAddr) -> bool:
        """Check if user belongs to concept_specialist class."""
        try:
            concept_specialist = client.resolve_keynodes(
                ScIdtfResolveParams(idtf='concept_specialist', type=sc_types.NODE_CONST_CLASS)
            )[0]
            tmpl = ScTemplate()
            tmpl.triple(concept_specialist, sc_types.EDGE_ACCESS_VAR_POS_PERM, user_addr)
            return len(client.template_search(tmpl)) > 0
        except Exception:
            return False

    def get_profile(self, user_email: str) -> dict:
        print(f"[CABINET][PROFILE] get_profile | email={user_email}")
        try:
            if not is_connected():
                return {'status': ProfileStatus.ERROR, 'message': 'Not connected to sc-machine'}
            user_addr = get_user_by_login(user_email)
            if not user_addr:
                print(f"[CABINET][PROFILE] get_profile: user not found — {user_email}")
                return {'status': ProfileStatus.INVALID, 'message': 'User not found'}

            is_spec = self._is_specialist(user_addr)
            name = (_get_link_attr(user_addr, 'nrel_full_name')
                    or _get_link_attr(user_addr, 'nrel_user_name'))
            jurisdiction = _get_link_attr(user_addr, 'nrel_default_jurisdiction') or 'BY'

            profile = {
                'email': user_email,
                'name': name,
                'jurisdiction': jurisdiction,
                'user_type': 'specialist' if is_spec else 'client',
            }
            if is_spec:
                profile['field']      = _get_link_attr(user_addr, 'nrel_field') or ''
                profile['experience'] = _get_link_attr(user_addr, 'nrel_experience') or ''
                profile['gender']     = _get_link_attr(user_addr, 'nrel_gender') or ''
                profile['age']        = _get_link_attr(user_addr, 'nrel_age') or ''

            print(f"[CABINET][PROFILE] get_profile OK | profile={profile}")
            return {'status': ProfileStatus.VALID, 'profile': profile}
        except Exception as e:
            print(f"[CABINET][PROFILE] get_profile ERROR: {e}")
            import traceback; traceback.print_exc()
            return {'status': ProfileStatus.ERROR, 'message': str(e)}

    def update_profile(self, user_email: str, data: dict) -> dict:
        print(f"[CABINET][PROFILE] update_profile | email={user_email} data={data}")
        try:
            if not is_connected():
                return {'status': ProfileStatus.ERROR, 'message': 'Not connected to sc-machine'}
            user_addr = get_user_by_login(user_email)
            if not user_addr:
                return {'status': ProfileStatus.INVALID, 'message': 'User not found'}

            if 'name' in data and data['name'] is not None:
                _set_link_attr(user_addr, 'nrel_user_name', str(data['name']))
                _set_link_attr(user_addr, 'nrel_full_name', str(data['name']))
                print(f"[CABINET][PROFILE] update_profile: name → '{data['name']}'")
            if 'jurisdiction' in data and data['jurisdiction'] is not None:
                _set_link_attr(user_addr, 'nrel_default_jurisdiction', str(data['jurisdiction']))
                print(f"[CABINET][PROFILE] update_profile: jurisdiction → '{data['jurisdiction']}'")
            # Specialist-only fields
            for key, rel in (('field', 'nrel_field'), ('experience', 'nrel_experience'),
                             ('gender', 'nrel_gender'), ('age', 'nrel_age')):
                if key in data and data[key] is not None:
                    _set_link_attr(user_addr, rel, str(data[key]))
                    print(f"[CABINET][PROFILE] update_profile: {key} → '{data[key]}'")

            print("[CABINET][PROFILE] update_profile OK")
            return {'status': ProfileStatus.VALID}
        except Exception as e:
            print(f"[CABINET][PROFILE] update_profile ERROR: {e}")
            import traceback; traceback.print_exc()
            return {'status': ProfileStatus.ERROR, 'message': str(e)}

    def get_settings(self, user_email: str) -> dict:
        print(f"[CABINET][PROFILE] get_settings | email={user_email}")
        try:
            if not is_connected():
                return {'status': ProfileStatus.ERROR, 'message': 'Not connected', 'settings': {}}
            user_addr = get_user_by_login(user_email)
            if not user_addr:
                print(f"[CABINET][PROFILE] get_settings: user not found — {user_email}")
                return {'status': ProfileStatus.INVALID, 'settings': {}}

            settings = {
                'jurisdiction':  _get_link_attr(user_addr, 'nrel_default_jurisdiction') or 'BY',
                'theme':         _get_link_attr(user_addr, 'nrel_ui_theme') or 'system',
                'font_size':     _get_link_attr(user_addr, 'nrel_font_size') or 'normal',
                'save_history':  _get_link_attr(user_addr, 'nrel_save_history') != 'false',
                'high_contrast': _get_link_attr(user_addr, 'nrel_high_contrast') == 'true',
            }
            print(f"[CABINET][PROFILE] get_settings OK | settings={settings}")
            return {'status': ProfileStatus.VALID, 'settings': settings}
        except Exception as e:
            print(f"[CABINET][PROFILE] get_settings ERROR: {e}")
            import traceback; traceback.print_exc()
            return {'status': ProfileStatus.ERROR, 'message': str(e), 'settings': {}}

    def update_settings(self, user_email: str, settings: dict) -> dict:
        print(f"[CABINET][PROFILE] update_settings | email={user_email} settings={settings}")
        try:
            if not is_connected():
                return {'status': ProfileStatus.ERROR, 'message': 'Not connected'}
            user_addr = get_user_by_login(user_email)
            if not user_addr:
                return {'status': ProfileStatus.INVALID}

            relation_map = {
                'jurisdiction':  'nrel_default_jurisdiction',
                'theme':         'nrel_ui_theme',
                'font_size':     'nrel_font_size',
                'save_history':  'nrel_save_history',
                'high_contrast': 'nrel_high_contrast',
            }
            updated = []
            for key, value in settings.items():
                if key in relation_map:
                    _set_link_attr(user_addr, relation_map[key], str(value).lower())
                    updated.append(key)

            print(f"[CABINET][PROFILE] update_settings OK | keys={updated}")
            return {'status': ProfileStatus.VALID}
        except Exception as e:
            print(f"[CABINET][PROFILE] update_settings ERROR: {e}")
            import traceback; traceback.print_exc()
            return {'status': ProfileStatus.ERROR, 'message': str(e)}


class OstisHistoryAgent(HistoryAgent):
    """Агент истории запросов — прямые операции с SC-памятью."""

    def get_history(self, user_email: str, period: str = 'week') -> dict:
        print(f"[CABINET][HISTORY] get_history | email={user_email} period={period}")
        try:
            if not is_connected():
                return {'status': HistoryStatus.ERROR, 'history': []}
            user_addr = get_user_by_login(user_email)
            if not user_addr:
                return {'status': HistoryStatus.INVALID, 'history': []}

            nrel_qh = _resolve_kn('nrel_query_history')
            t = ScTemplate()
            t.quintuple(user_addr, sc_types.EDGE_D_COMMON_VAR,
                        sc_types.NODE_VAR >> '_query',
                        sc_types.EDGE_ACCESS_VAR_POS_PERM, nrel_qh)
            results = client.template_search(t)

            history = []
            for res in results:
                query_addr = res.get('_query')
                history.append({
                    'id':   str(query_addr.value),
                    'type': _get_link_attr(query_addr, 'nrel_query_type') or 'Запрос',
                    'text': _get_link_attr(query_addr, 'nrel_query_text') or '',
                    'date': _get_link_attr(query_addr, 'nrel_query_timestamp') or '',
                })

            # Period filtering
            if period != 'all' and history:
                from datetime import timedelta
                cutoff = datetime.now() - timedelta(days=7 if period == 'week' else 30)
                filtered = []
                for h in history:
                    if not h['date']:
                        filtered.append(h)
                        continue
                    try:
                        if datetime.fromisoformat(h['date']) >= cutoff:
                            filtered.append(h)
                    except ValueError:
                        filtered.append(h)
                history = filtered

            history.sort(key=lambda x: x['date'], reverse=True)
            print(f"[CABINET][HISTORY] get_history OK | count={len(history)} period={period}")
            return {'status': HistoryStatus.VALID, 'history': history}
        except Exception as e:
            print(f"[CABINET][HISTORY] get_history ERROR: {e}")
            import traceback; traceback.print_exc()
            return {'status': HistoryStatus.ERROR, 'history': []}

    def add_history_entry(self, user_email: str, query_type: str,
                          query_text: str, article_id: str = None) -> dict:
        print(f"[CABINET][HISTORY] add_history_entry | email={user_email} "
              f"type={query_type!r} text={query_text!r} article={article_id}")
        try:
            if not is_connected():
                return {'status': HistoryStatus.ERROR, 'message': 'Not connected'}
            user_addr = get_user_by_login(user_email)
            if not user_addr:
                return {'status': HistoryStatus.INVALID}

            concept_uq = _resolve_kn('concept_user_query', sc_types.NODE_CONST_CLASS)
            nrel_qh    = _resolve_kn('nrel_query_history')
            nrel_qtype = _resolve_kn('nrel_query_type')
            nrel_qtext = _resolve_kn('nrel_query_text')
            nrel_qts   = _resolve_kn('nrel_query_timestamp')

            timestamp = datetime.now().isoformat()

            con = ScConstruction()
            con.create_node(sc_types.NODE_CONST, 'query_node')
            # Add to concept_user_query class
            con.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, concept_uq, 'query_node', 'cls_edge')

            con.create_link(sc_types.LINK_CONST,
                            ScLinkContent(query_type, ScLinkContentType.STRING), 'type_lnk')
            con.create_link(sc_types.LINK_CONST,
                            ScLinkContent(query_text, ScLinkContentType.STRING), 'text_lnk')
            con.create_link(sc_types.LINK_CONST,
                            ScLinkContent(timestamp, ScLinkContentType.STRING), 'ts_lnk')

            # nrel_query_type quintuple
            con.create_edge(sc_types.EDGE_D_COMMON_CONST, 'query_node', 'type_lnk', 'type_edge')
            con.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, nrel_qtype, 'type_edge')
            # nrel_query_text quintuple
            con.create_edge(sc_types.EDGE_D_COMMON_CONST, 'query_node', 'text_lnk', 'text_edge')
            con.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, nrel_qtext, 'text_edge')
            # nrel_query_timestamp quintuple
            con.create_edge(sc_types.EDGE_D_COMMON_CONST, 'query_node', 'ts_lnk', 'ts_edge')
            con.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, nrel_qts, 'ts_edge')
            # user --[nrel_query_history]--> query_node
            con.create_edge(sc_types.EDGE_D_COMMON_CONST, user_addr, 'query_node', 'hist_edge')
            con.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, nrel_qh, 'hist_edge')

            gen = client.generate_elements(con)
            query_addr = gen[0]  # 'query_node' is at index 0 (first created element)
            print(f"[CABINET][HISTORY] add_history_entry OK | id={query_addr.value}")
            return {'status': HistoryStatus.VALID, 'id': str(query_addr.value)}
        except Exception as e:
            print(f"[CABINET][HISTORY] add_history_entry ERROR: {e}")
            import traceback; traceback.print_exc()
            return {'status': HistoryStatus.ERROR, 'message': str(e)}

    def clear_history(self, user_email: str) -> dict:
        print(f"[CABINET][HISTORY] clear_history | email={user_email}")
        try:
            if not is_connected():
                return {'status': HistoryStatus.ERROR, 'message': 'Not connected'}
            user_addr = get_user_by_login(user_email)
            if not user_addr:
                return {'status': HistoryStatus.INVALID}

            nrel_qh = _resolve_kn('nrel_query_history')
            t = ScTemplate()
            t.quintuple(user_addr,
                        sc_types.EDGE_D_COMMON_VAR >> '_he',
                        sc_types.NODE_VAR >> '_query',
                        sc_types.EDGE_ACCESS_VAR_POS_PERM >> '_re',
                        nrel_qh)
            results = client.template_search(t)

            to_delete = []
            for res in results:
                to_delete.append(res.get('_he'))
                to_delete.append(res.get('_re'))
                to_delete.append(res.get('_query'))

            if to_delete:
                client.erase_elements(*to_delete)

            print(f"[CABINET][HISTORY] clear_history OK | removed {len(results)} entries")
            return {'status': HistoryStatus.VALID}
        except Exception as e:
            print(f"[CABINET][HISTORY] clear_history ERROR: {e}")
            import traceback; traceback.print_exc()
            return {'status': HistoryStatus.ERROR, 'message': str(e)}


class OstisBookmarksAgent(BookmarksAgent):
    """Агент закладок — прямые операции с SC-памятью."""

    def get_bookmarks(self, user_email: str) -> dict:
        print(f"[CABINET][BOOKMARKS] get_bookmarks | email={user_email}")
        try:
            if not is_connected():
                return {'status': BookmarksStatus.ERROR, 'bookmarks': []}
            user_addr = get_user_by_login(user_email)
            if not user_addr:
                return {'status': BookmarksStatus.INVALID, 'bookmarks': []}

            nrel_ub = _resolve_kn('nrel_user_bookmarks')
            t = ScTemplate()
            t.quintuple(user_addr, sc_types.EDGE_D_COMMON_VAR,
                        sc_types.NODE_VAR >> '_bm',
                        sc_types.EDGE_ACCESS_VAR_POS_PERM, nrel_ub)
            results = client.template_search(t)

            bookmarks = []
            for res in results:
                bm_addr = res.get('_bm')
                tags_raw = _get_link_attr(bm_addr, 'nrel_bookmark_tags')
                bookmarks.append({
                    'id':         str(bm_addr.value),
                    'article_id': _get_link_attr(bm_addr, 'nrel_bookmark_article'),
                    'title':      _get_link_attr(bm_addr, 'nrel_bookmark_title'),
                    'tags':       [tg.strip() for tg in tags_raw.split(',') if tg.strip()],
                    'date':       _get_link_attr(bm_addr, 'nrel_bookmark_date'),
                })

            print(f"[CABINET][BOOKMARKS] get_bookmarks OK | count={len(bookmarks)}")
            return {'status': BookmarksStatus.VALID, 'bookmarks': bookmarks}
        except Exception as e:
            print(f"[CABINET][BOOKMARKS] get_bookmarks ERROR: {e}")
            import traceback; traceback.print_exc()
            return {'status': BookmarksStatus.ERROR, 'bookmarks': []}

    def add_bookmark(self, user_email: str, article_id: str,
                     title: str, tags: list = None) -> dict:
        print(f"[CABINET][BOOKMARKS] add_bookmark | email={user_email} "
              f"title={title!r} tags={tags}")
        try:
            if not is_connected():
                return {'status': BookmarksStatus.ERROR, 'message': 'Not connected'}
            user_addr = get_user_by_login(user_email)
            if not user_addr:
                return {'status': BookmarksStatus.INVALID, 'message': 'User not found'}

            concept_bm = _resolve_kn('concept_bookmark', sc_types.NODE_CONST_CLASS)
            nrel_ub    = _resolve_kn('nrel_user_bookmarks')
            nrel_bart  = _resolve_kn('nrel_bookmark_article')
            nrel_btitl = _resolve_kn('nrel_bookmark_title')
            nrel_btags = _resolve_kn('nrel_bookmark_tags')
            nrel_bdate = _resolve_kn('nrel_bookmark_date')

            date_str = datetime.now().isoformat()
            tags_str = ','.join(tags) if tags else ''

            con = ScConstruction()
            con.create_node(sc_types.NODE_CONST, 'bm_node')
            # Add to concept_bookmark class
            con.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, concept_bm, 'bm_node', 'cls_edge')

            con.create_link(sc_types.LINK_CONST,
                            ScLinkContent(article_id or '', ScLinkContentType.STRING), 'art_lnk')
            con.create_link(sc_types.LINK_CONST,
                            ScLinkContent(title or '',      ScLinkContentType.STRING), 'ttl_lnk')
            con.create_link(sc_types.LINK_CONST,
                            ScLinkContent(tags_str,         ScLinkContentType.STRING), 'tag_lnk')
            con.create_link(sc_types.LINK_CONST,
                            ScLinkContent(date_str,         ScLinkContentType.STRING), 'dt_lnk')

            # nrel_bookmark_article quintuple
            con.create_edge(sc_types.EDGE_D_COMMON_CONST, 'bm_node', 'art_lnk', 'art_edge')
            con.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, nrel_bart, 'art_edge')
            # nrel_bookmark_title quintuple
            con.create_edge(sc_types.EDGE_D_COMMON_CONST, 'bm_node', 'ttl_lnk', 'ttl_edge')
            con.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, nrel_btitl, 'ttl_edge')
            # nrel_bookmark_tags quintuple
            con.create_edge(sc_types.EDGE_D_COMMON_CONST, 'bm_node', 'tag_lnk', 'tag_edge')
            con.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, nrel_btags, 'tag_edge')
            # nrel_bookmark_date quintuple
            con.create_edge(sc_types.EDGE_D_COMMON_CONST, 'bm_node', 'dt_lnk', 'dt_edge')
            con.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, nrel_bdate, 'dt_edge')
            # user --[nrel_user_bookmarks]--> bookmark
            con.create_edge(sc_types.EDGE_D_COMMON_CONST, user_addr, 'bm_node', 'usr_edge')
            con.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, nrel_ub, 'usr_edge')

            gen = client.generate_elements(con)
            bm_addr = gen[0]  # 'bm_node' is at index 0
            print(f"[CABINET][BOOKMARKS] add_bookmark OK | id={bm_addr.value}")
            return {'status': BookmarksStatus.VALID, 'id': str(bm_addr.value)}
        except Exception as e:
            print(f"[CABINET][BOOKMARKS] add_bookmark ERROR: {e}")
            import traceback; traceback.print_exc()
            return {'status': BookmarksStatus.ERROR, 'message': str(e)}

    def update_bookmark(self, user_email: str, bookmark_id: str,
                        tags: list = None) -> dict:
        print(f"[CABINET][BOOKMARKS] update_bookmark | email={user_email} "
              f"id={bookmark_id} tags={tags}")
        try:
            if not is_connected():
                return {'status': BookmarksStatus.ERROR, 'message': 'Not connected'}
            bm_addr = ScAddr(int(bookmark_id))
            nrel_btags = _resolve_kn('nrel_bookmark_tags')
            tags_str = ','.join(tags) if tags else ''

            t = ScTemplate()
            t.quintuple(bm_addr, sc_types.EDGE_D_COMMON_VAR >> '_edge',
                        sc_types.LINK_VAR >> '_tags',
                        sc_types.EDGE_ACCESS_VAR_POS_PERM, nrel_btags)
            results = client.template_search(t)

            if results:
                tags_link = results[0].get('_tags')
                client.set_link_contents(ScLinkContent(tags_str, ScLinkContentType.STRING, addr=tags_link))
                print(f"[CABINET][BOOKMARKS] update_bookmark OK | updated existing link")
            else:
                con = ScConstruction()
                con.create_link(sc_types.LINK_CONST,
                                ScLinkContent(tags_str, ScLinkContentType.STRING), 'tag_lnk')
                con.create_edge(sc_types.EDGE_D_COMMON_CONST, bm_addr, 'tag_lnk', 'tag_edge')
                con.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, nrel_btags, 'tag_edge')
                client.generate_elements(con)
                print(f"[CABINET][BOOKMARKS] update_bookmark OK | created new tags link")

            return {'status': BookmarksStatus.VALID}
        except Exception as e:
            print(f"[CABINET][BOOKMARKS] update_bookmark ERROR: {e}")
            import traceback; traceback.print_exc()
            return {'status': BookmarksStatus.ERROR, 'message': str(e)}

    def delete_bookmark(self, user_email: str, bookmark_id: str) -> dict:
        print(f"[CABINET][BOOKMARKS] delete_bookmark | email={user_email} id={bookmark_id}")
        try:
            if not is_connected():
                return {'status': BookmarksStatus.ERROR, 'message': 'Not connected'}
            bm_addr = ScAddr(int(bookmark_id))

            # Remove the connecting edge from user -> bookmark
            user_addr = get_user_by_login(user_email)
            if user_addr:
                nrel_ub = _resolve_kn('nrel_user_bookmarks')
                t = ScTemplate()
                t.quintuple(user_addr, sc_types.EDGE_D_COMMON_VAR >> '_edge',
                            bm_addr, sc_types.EDGE_ACCESS_VAR_POS_PERM, nrel_ub)
                results = client.template_search(t)
                for r in results:
                    edge_addr = r.get('_edge')
                    if edge_addr:
                        client.erase_elements(edge_addr)

            client.erase_elements(bm_addr)
            print(f"[CABINET][BOOKMARKS] delete_bookmark OK | id={bookmark_id}")
            return {'status': BookmarksStatus.VALID}
        except Exception as e:
            print(f"[CABINET][BOOKMARKS] delete_bookmark ERROR: {e}")
            import traceback; traceback.print_exc()
            return {'status': BookmarksStatus.ERROR, 'message': str(e)}


class OstisNotesAgent(NotesAgent):
    """Агент заметок — прямые операции с SC-памятью."""

    def get_notes(self, user_email: str) -> dict:
        print(f"[CABINET][NOTES] get_notes | email={user_email}")
        try:
            if not is_connected():
                return {'status': NotesStatus.ERROR, 'notes': []}
            user_addr = get_user_by_login(user_email)
            if not user_addr:
                return {'status': NotesStatus.INVALID, 'notes': []}

            nrel_un = _resolve_kn('nrel_user_notes')
            t = ScTemplate()
            t.quintuple(user_addr, sc_types.EDGE_D_COMMON_VAR,
                        sc_types.NODE_VAR >> '_note',
                        sc_types.EDGE_ACCESS_VAR_POS_PERM, nrel_un)
            results = client.template_search(t)

            notes = []
            for res in results:
                note_addr = res.get('_note')
                notes.append({
                    'id':            str(note_addr.value),
                    'article_id':    _get_link_attr(note_addr, 'nrel_note_article'),
                    'article_title': _get_link_attr(note_addr, 'nrel_note_article_title'),
                    'text':          _get_link_attr(note_addr, 'nrel_note_text'),
                    'created_at':    _get_link_attr(note_addr, 'nrel_note_created'),
                    'updated_at':    _get_link_attr(note_addr, 'nrel_note_updated'),
                })

            print(f"[CABINET][NOTES] get_notes OK | count={len(notes)}")
            return {'status': NotesStatus.VALID, 'notes': notes}
        except Exception as e:
            print(f"[CABINET][NOTES] get_notes ERROR: {e}")
            import traceback; traceback.print_exc()
            return {'status': NotesStatus.ERROR, 'notes': []}

    def add_note(self, user_email: str, article_id: str,
                 article_title: str, text: str) -> dict:
        print(f"[CABINET][NOTES] add_note | email={user_email} title={article_title!r}")
        try:
            if not is_connected():
                return {'status': NotesStatus.ERROR, 'message': 'Not connected'}
            user_addr = get_user_by_login(user_email)
            if not user_addr:
                return {'status': NotesStatus.INVALID, 'message': 'User not found'}

            concept_un   = _resolve_kn('concept_user_note', sc_types.NODE_CONST_CLASS)
            nrel_un      = _resolve_kn('nrel_user_notes')
            nrel_nart    = _resolve_kn('nrel_note_article')
            nrel_narttit = _resolve_kn('nrel_note_article_title')
            nrel_ntxt    = _resolve_kn('nrel_note_text')
            nrel_ncr     = _resolve_kn('nrel_note_created')
            nrel_nupd    = _resolve_kn('nrel_note_updated')

            timestamp = datetime.now().isoformat()

            con = ScConstruction()
            con.create_node(sc_types.NODE_CONST, 'note_node')
            # Add to concept_user_note class
            con.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, concept_un, 'note_node', 'cls_edge')

            con.create_link(sc_types.LINK_CONST,
                            ScLinkContent(article_id or '',    ScLinkContentType.STRING), 'art_lnk')
            con.create_link(sc_types.LINK_CONST,
                            ScLinkContent(article_title or '', ScLinkContentType.STRING), 'tit_lnk')
            con.create_link(sc_types.LINK_CONST,
                            ScLinkContent(text or '',          ScLinkContentType.STRING), 'txt_lnk')
            con.create_link(sc_types.LINK_CONST,
                            ScLinkContent(timestamp,           ScLinkContentType.STRING), 'cr_lnk')
            con.create_link(sc_types.LINK_CONST,
                            ScLinkContent(timestamp,           ScLinkContentType.STRING), 'upd_lnk')

            # nrel_note_article quintuple
            con.create_edge(sc_types.EDGE_D_COMMON_CONST, 'note_node', 'art_lnk', 'art_edge')
            con.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, nrel_nart, 'art_edge')
            # nrel_note_article_title quintuple
            con.create_edge(sc_types.EDGE_D_COMMON_CONST, 'note_node', 'tit_lnk', 'tit_edge')
            con.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, nrel_narttit, 'tit_edge')
            # nrel_note_text quintuple
            con.create_edge(sc_types.EDGE_D_COMMON_CONST, 'note_node', 'txt_lnk', 'txt_edge')
            con.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, nrel_ntxt, 'txt_edge')
            # nrel_note_created quintuple
            con.create_edge(sc_types.EDGE_D_COMMON_CONST, 'note_node', 'cr_lnk', 'cr_edge')
            con.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, nrel_ncr, 'cr_edge')
            # nrel_note_updated quintuple
            con.create_edge(sc_types.EDGE_D_COMMON_CONST, 'note_node', 'upd_lnk', 'upd_edge')
            con.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, nrel_nupd, 'upd_edge')
            # user --[nrel_user_notes]--> note
            con.create_edge(sc_types.EDGE_D_COMMON_CONST, user_addr, 'note_node', 'usr_edge')
            con.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, nrel_un, 'usr_edge')

            gen = client.generate_elements(con)
            note_addr = gen[0]  # 'note_node' is at index 0
            print(f"[CABINET][NOTES] add_note OK | id={note_addr.value}")
            return {'status': NotesStatus.VALID, 'id': str(note_addr.value)}
        except Exception as e:
            print(f"[CABINET][NOTES] add_note ERROR: {e}")
            import traceback; traceback.print_exc()
            return {'status': NotesStatus.ERROR, 'message': str(e)}

    def update_note(self, user_email: str, note_id: str, text: str) -> dict:
        print(f"[CABINET][NOTES] update_note | email={user_email} id={note_id}")
        try:
            if not is_connected():
                return {'status': NotesStatus.ERROR, 'message': 'Not connected'}
            note_addr = ScAddr(int(note_id))
            nrel_ntxt  = _resolve_kn('nrel_note_text')
            nrel_nupd  = _resolve_kn('nrel_note_updated')
            timestamp = datetime.now().isoformat()

            # Update text link
            t = ScTemplate()
            t.quintuple(note_addr, sc_types.EDGE_D_COMMON_VAR,
                        sc_types.LINK_VAR >> '_txt',
                        sc_types.EDGE_ACCESS_VAR_POS_PERM, nrel_ntxt)
            r = client.template_search(t)
            if r:
                txt_addr = r[0].get('_txt')
                client.set_link_contents(ScLinkContent(text, ScLinkContentType.STRING, addr=txt_addr))
                print(f"[CABINET][NOTES] update_note: text updated")

            # Update timestamp link
            t2 = ScTemplate()
            t2.quintuple(note_addr, sc_types.EDGE_D_COMMON_VAR,
                         sc_types.LINK_VAR >> '_upd',
                         sc_types.EDGE_ACCESS_VAR_POS_PERM, nrel_nupd)
            r2 = client.template_search(t2)
            if r2:
                upd_addr = r2[0].get('_upd')
                client.set_link_contents(ScLinkContent(timestamp, ScLinkContentType.STRING, addr=upd_addr))
                print(f"[CABINET][NOTES] update_note: timestamp updated")

            print(f"[CABINET][NOTES] update_note OK | id={note_id}")
            return {'status': NotesStatus.VALID}
        except Exception as e:
            print(f"[CABINET][NOTES] update_note ERROR: {e}")
            import traceback; traceback.print_exc()
            return {'status': NotesStatus.ERROR, 'message': str(e)}

    def delete_note(self, user_email: str, note_id: str) -> dict:
        print(f"[CABINET][NOTES] delete_note | email={user_email} id={note_id}")
        try:
            if not is_connected():
                return {'status': NotesStatus.ERROR, 'message': 'Not connected'}
            note_addr = ScAddr(int(note_id))

            # Remove the connecting edge from user -> note
            user_addr = get_user_by_login(user_email)
            if user_addr:
                nrel_un = _resolve_kn('nrel_user_notes')
                t = ScTemplate()
                t.quintuple(user_addr, sc_types.EDGE_D_COMMON_VAR >> '_edge',
                            note_addr, sc_types.EDGE_ACCESS_VAR_POS_PERM, nrel_un)
                results = client.template_search(t)
                for r in results:
                    edge_addr = r.get('_edge')
                    if edge_addr:
                        client.erase_elements(edge_addr)

            client.erase_elements(note_addr)
            print(f"[CABINET][NOTES] delete_note OK | id={note_id}")
            return {'status': NotesStatus.VALID}
        except Exception as e:
            print(f"[CABINET][NOTES] delete_note ERROR: {e}")
            import traceback; traceback.print_exc()
            return {'status': NotesStatus.ERROR, 'message': str(e)}

    def _get_attr(self, node_addr: ScAddr, rel_idtf: str) -> str:
        try:
            rel = client.resolve_keynodes(ScIdtfResolveParams(idtf=rel_idtf, type=sc_types.NODE_CONST_NOROLE))[0]
            t = ScTemplate()
            t.quintuple(node_addr, sc_types.EDGE_D_COMMON_VAR, sc_types.LINK_VAR >> '_v',
                        sc_types.EDGE_ACCESS_VAR_POS_PERM, rel)
            r = client.template_search(t)
            if r:
                c = client.get_link_content(r[0].get('_v'))
                if c:
                    return c[0].data
        except:
            pass
        return ''