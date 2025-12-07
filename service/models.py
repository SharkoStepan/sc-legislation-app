from typing import Optional, List
from flask_login import UserMixin
from service import login_manager
from pydantic.dataclasses import dataclass
from sc_client.client import get_link_content, search_by_template
from sc_client.models import ScTemplate, ScAddr, ScIdtfResolveParams
from sc_client.constants import sc_types
from sc_kpm import ScKeynodes

@dataclass
class DirectoryResponse:
    title: str
    content: str
    
    def __str__(self) -> str:
        return f"{self.title} - {self.content}"

@dataclass
class RequestResponse:
    term: str
    content: str
    related_concepts: List[str] = None
    related_articles: List[str] = None
    
    def __post_init__(self):
        self.related_concepts = self.related_concepts or []
        self.related_articles = self.related_articles or []
    
    def __str__(self) -> str:
        return f"{self.term} - {self.content}"

@dataclass
class UserEvent:
    username: str
    title: str
    date: str
    content: str

@dataclass
class EventResponse:
    events: list[UserEvent]

class User(UserMixin):
    def __init__(
        self,
        sc_addr: str = None,
        gender: str = '',
        surname: str = '',
        name: str = '',
        fname: str = '',
        birthdate: str = '',
        reg_place: str = '',
        username: str = '',
        password: str = ''
    ):
        self.sc_addr = sc_addr
        self.gender = gender
        self.surname = surname
        self.name = name
        self.fname = fname
        self.birthdate = birthdate
        self.reg_place = reg_place
        self.username = username
        self.password = password

    @property
    def get_sc_addr_str(self):
        return self.sc_addr

    def get_id(self):
        return str(self.username)

    def __repr__(self):
        return f"User({self.username}, {self.sc_addr})"


def find_user_by_username(username: str) -> Optional[User]:
    """
    Поиск пользователя по email (username теперь = email)
    """
    try:
        # ИМПОРТ ВНУТРИ ФУНКЦИИ - избегаем циклического импорта
        import sc_client.client as client
        
        # Резолвим необходимые keynodes
        nrel_email = client.resolve_keynodes(
            ScIdtfResolveParams(idtf='nrel_email', type=sc_types.NODE_CONST_NOROLE)
        )[0]
        
        concept_verified_user = client.resolve_keynodes(
            ScIdtfResolveParams(idtf='concept_verified_user', type=sc_types.NODE_CONST_CLASS)
        )[0]
        
        # Создаем шаблон поиска
        template = ScTemplate()
        
        # concept_verified_user -> user
        template.triple(
            concept_verified_user,
            sc_types.EDGE_ACCESS_VAR_POS_PERM,
            sc_types.NODE_VAR >> 'user'
        )
        
        # user -nrel_email-> email_link
        template.triple_with_relation(
            'user',
            sc_types.EDGE_D_COMMON_VAR,
            sc_types.LINK_VAR >> 'email',
            sc_types.EDGE_ACCESS_VAR_POS_PERM,
            nrel_email
        )
        
        results = search_by_template(template)
        
        for result in results:
            email_content = get_link_content(result.get('email'))[0].data
            if email_content == username:
                # Создаем минимальный объект User для Flask-Login
                user_addr = result.get('user')
                return User(
                    sc_addr=str(user_addr.value),
                    gender='',
                    surname='',
                    name='',
                    fname='',
                    birthdate='',
                    reg_place='',
                    username=email_content,
                    password=''
                )
        
        return None
        
    except Exception as e:
        print(f"Error in find_user_by_username: {e}")
        import traceback
        traceback.print_exc()
        return None


@login_manager.user_loader
def load_user(username: str) -> Optional[User]:
    """
    Загрузка пользователя для Flask-Login (по email)
    """
    return find_user_by_username(username)


def collect_user_info(user: ScAddr) -> User:
    """
    Сбор информации о пользователе (старая функция - оставляем для совместимости)
    """
    template = ScTemplate()
    template.triple_with_relation(
        user,
        sc_types.EDGE_D_COMMON_VAR,
        sc_types.LINK_VAR >> 'login',
        sc_types.EDGE_ACCESS_VAR_POS_PERM,
        ScKeynodes['nrel_user_login']
    )
    template.triple_with_relation(
        user,
        sc_types.EDGE_D_COMMON_VAR,
        sc_types.LINK_VAR >> 'password',
        sc_types.EDGE_ACCESS_VAR_POS_PERM,
        ScKeynodes['nrel_user_password']
    )
    template.triple_with_relation(
        user,
        sc_types.EDGE_D_COMMON_VAR,
        sc_types.LINK_VAR >> 'surname',
        sc_types.EDGE_ACCESS_VAR_POS_PERM,
        ScKeynodes['nrel_user_surname']
    )
    template.triple_with_relation(
        user,
        sc_types.EDGE_D_COMMON_VAR,
        sc_types.LINK_VAR >> 'name',
        sc_types.EDGE_ACCESS_VAR_POS_PERM,
        ScKeynodes['nrel_user_name']
    )
    template.triple_with_relation(
        user,
        sc_types.EDGE_D_COMMON_VAR,
        sc_types.LINK_VAR >> 'patronymic',
        sc_types.EDGE_ACCESS_VAR_POS_PERM,
        ScKeynodes['nrel_user_patronymic']
    )
    template.triple_with_relation(
        user,
        sc_types.EDGE_D_COMMON_VAR,
        sc_types.LINK_VAR >> 'address',
        sc_types.EDGE_ACCESS_VAR_POS_PERM,
        ScKeynodes['nrel_user_address']
    )
    template.triple_with_relation(
        user,
        sc_types.EDGE_D_COMMON_VAR,
        sc_types.NODE_VAR >> 'gender',
        sc_types.EDGE_ACCESS_VAR_POS_PERM,
        ScKeynodes['nrel_user_gender']
    )
    template.triple_with_relation(
        user,
        sc_types.EDGE_D_COMMON_VAR,
        sc_types.NODE_VAR >> 'birthdate',
        sc_types.EDGE_ACCESS_VAR_POS_PERM,
        ScKeynodes['nrel_user_birthdate']
    )
    
    result = search_by_template(template)[0]
    
    return User(
        sc_addr=str(user.value),
        gender=result.get('gender'),
        surname=result.get('surname'),
        name=result.get('name'),
        fname=result.get('patronymic'),
        birthdate=result.get('birthdate'),
        reg_place=result.get('address'),
        username=result.get('login'),
        password=result.get('password')
    )


def get_user_by_login(username: str) -> ScAddr:
    """
    Получение ScAddr пользователя по логину (старая функция)
    """
    template = ScTemplate()
    template.triple_with_relation(
        sc_types.NODE_VAR >> 'user',
        sc_types.EDGE_D_COMMON_VAR,
        sc_types.LINK_VAR >> 'login',
        sc_types.EDGE_ACCESS_VAR_POS_PERM,
        ScKeynodes['nrel_user_login']
    )
    
    results = search_by_template(template)
    for result in results:
        login_content = get_link_content(result.get('login'))[0].data
        if login_content == username:
            return result.get('user')
