import re 

import sc_client .client as client 
from sc_client .client import search_links_by_contents 
from sc_client .models import (
ScAddr ,
ScConstruction ,
ScLinkContent ,
ScLinkContentType ,
ScTemplate ,
)
from sc_client .constants import sc_types 
from sc_kpm import ScKeynodes 
from sc_kpm .utils .common_utils import (
generate_link 
)

from service .exceptions import ParseDataError 

from service .models import UserEvent ,EventResponse ,get_user_by_login 

def create_link (client ,content :str ):
    """
    Метод для создания sc-link
    :param client: sc-client
    :param content: Контент sc-link
    :return:
    """
    construction =ScConstruction ()
    to_find_content =ScLinkContent (content ,ScLinkContentType .STRING )
    construction .create_link (sc_types .LINK_CONST ,to_find_content )
    link =client .generate_elements (construction )
    return link [0 ]

def get_node (client )->ScAddr :
    """
    Метод для получения ноды вызова агента
    :param client: sc-client
    :return: Нода вызова агента
    """
    construction =ScConstruction ()
    construction .create_node (sc_types .NODE_CONST )
    main_node :ScAddr =client .generate_elements (construction )[0 ]
    return main_node 

def get_main_idtf (node :ScAddr )->str :
    """
    Метод для получения основного идентификатора ноды
    :param node: Нода
    :return: Основной идентификатор ноды
    """
    template =ScTemplate ()
    template .quintuple (
    node ,
    sc_types .EDGE_D_COMMON_VAR ,
    '_value',
    sc_types .EDGE_ACCESS_VAR_POS_PERM ,
    ScKeynodes ['nrel_main_idtf']
    )
    template_result =client .template_search (template )
    value =''
    if len (template_result ):
        value =client .get_link_content (template_result [0 ].get ('_value'))[0 ].data 
    return value 

def get_system_idtf (node :ScAddr )->str :
    template =ScTemplate ()
    template .quintuple (
    node ,
    sc_types .EDGE_D_COMMON_VAR ,
    '_value',
    sc_types .EDGE_ACCESS_VAR_POS_PERM ,
    ScKeynodes ['nrel_system_idtf']
    )
    template_result =client .template_search (template )
    value =''
    if len (template_result ):
        value =client .get_link_content (template_result [0 ].get ('_value'))[0 ].data 
    return value 

def set_system_idtf (content :str )->ScAddr :

    _link =generate_link (content )

    template =ScTemplate ()

    template .quintuple (
    sc_types .NODE_VAR >>"_node",
    sc_types .EDGE_D_COMMON_VAR ,
    _link >>"_link",
    sc_types .EDGE_ACCESS_VAR_POS_PERM ,
    ScKeynodes ["nrel_system_identifier"]
    )

    result =client .generate_by_template (template )

    return result .get ("_node")

def set_main_idtf (content :str )->ScAddr :

    _link =generate_link (content )

    template =ScTemplate ()

    template .quintuple (
    sc_types .NODE_VAR >>"_node",
    sc_types .EDGE_D_COMMON_VAR ,
    _link >>"_link",
    sc_types .EDGE_ACCESS_VAR_POS_PERM ,
    ScKeynodes ["nrel_main_identifier"]
    )

    result =client .generate_by_template (template )

    return result .get ("_node")

def set_gender_content (gender )->ScAddr :
    """
    Метод для получения ноды пола пользователя
    :param gender: Пол пользователя
    :return: Кейнода для представления пола
    """
    if gender =="male":
        return ScKeynodes ['concept_man']
    if gender =="female":
        return ScKeynodes ['concept_woman']
    else :
        raise ParseDataError (666 ,"Failed to parse args")

def split_date_content (birthdate ):
    pattern =r'(\d{2})\.(\d{2})\.(\d{4})'
    pattern_2 =r'(\d{4})\-(\d{2})\-(\d{2})'
    match =re .match (pattern ,birthdate )
    match_2 =re .match (pattern_2 ,birthdate )
    if match :
        day ,month ,year =map (int ,match .groups ())
        return day ,month ,year 
    elif match_2 :
        day ,month ,year =map (int ,match_2 .groups ()[::-1 ])
        return day ,month ,year 
    else :
        raise ParseDataError (666 ,"Failed to parse args")

def get_term_titles ()->list [str ]:
    template =ScTemplate ()
    term_list =[]
    template .triple (
    ScKeynodes ["belarus_legal_article"],
    sc_types .EDGE_ACCESS_VAR_POS_PERM ,
    sc_types .NODE_VAR >>"_term_node"
    )

    template_result =client .template_search (template )
    print (f'total terms {len (template_result )}')
    for _ in template_result :
        node =_ .get ("_term_node")
        term_list .append (get_main_idtf (node ))
    return term_list 


def get_event_by_date (date :str ,username :str )->EventResponse |None :
    user_node =get_user_by_login (username )

    template =ScTemplate ()
    template .quintuple (
    user_node ,
    sc_types .EDGE_D_COMMON_VAR ,
    sc_types .NODE_VAR >>"_event",
    sc_types .EDGE_ACCESS_VAR_POS_PERM ,
    ScKeynodes ["nrel_user_event"]
    )

    result =client .template_search (template )

    event_list =[]
    if len (result )>0 :
        for event_node in result :
            event_node =event_node .get ("_event")
            sc_filter =ScTemplate ()
            sc_filter .triple_with_relation (
            event_node ,
            sc_types .EDGE_D_COMMON_VAR ,
            sc_types .LINK_VAR >>"_event_name",
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            ScKeynodes ["nrel_event_name"]
            )
            sc_filter .triple_with_relation (
            event_node ,
            sc_types .EDGE_D_COMMON_VAR ,
            sc_types .LINK_VAR >>"_event_description",
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            ScKeynodes ["nrel_event_description"]
            )
            sc_filter .triple_with_relation (
            event_node ,
            sc_types .EDGE_D_COMMON_VAR ,
            sc_types .NODE_VAR_TUPLE >>"_event_date_tuple",
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            ScKeynodes ["nrel_event_date"]
            )
            sc_filter .triple_with_relation (
            "_event_date_tuple",
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            sc_types .LINK_VAR >>"_day_lnk",
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            ScKeynodes ["rrel_event_day"]
            )
            sc_filter .triple_with_relation (
            "_event_date_tuple",
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            sc_types .LINK_VAR >>"_month_lnk",
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            ScKeynodes ["rrel_event_month"]
            )
            sc_filter .triple_with_relation (
            "_event_date_tuple",
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            sc_types .LINK_VAR >>"_year_lnk",
            sc_types .EDGE_ACCESS_VAR_POS_PERM ,
            ScKeynodes ["rrel_event_year"]
            )
            filter_result =client .search_by_template (sc_filter )
            if len (filter_result )==0 :
                continue 
            else :
                for _item in filter_result :
                    event_list .append (UserEvent (
                    username =username ,
                    title =client .get_link_content (_item .get ("_event_name"))[0 ].data ,
                    date =date ,
                    content =client .get_link_content (_item .get ("_event_description"))[0 ].data 
                    ))
        return EventResponse (events =event_list )
    else :
        print ("No data to current date")


