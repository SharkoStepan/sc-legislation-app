from flask_wtf import FlaskForm 
from wtforms import StringField ,PasswordField ,SubmitField ,RadioField ,HiddenField ,TextAreaField ,SelectField ,IntegerField 
from wtforms .validators import DataRequired ,Length ,ValidationError ,Email ,EqualTo ,NumberRange ,Optional 
from datetime import datetime 


class LoginForm (FlaskForm ):
    """
    Форма для аутентификации (обновлена под email)
    """
    email =StringField ('Email',validators =[DataRequired (),Email (message ="Некорректный email")])
    password =PasswordField ('Пароль',validators =[DataRequired (),Length (min =8 )])
    submit =SubmitField ('Войти')


class RegistrationForm (FlaskForm ):
    """
    Форма для регистрации (обновлена под новую схему)
    """
    email =StringField ('Email',validators =[
    DataRequired (),
    Email (message ="Некорректный email")
    ])
    password =PasswordField ('Пароль',validators =[
    DataRequired (),
    Length (min =8 ,message ="Минимум 8 символов")
    ])
    password_conf =PasswordField ('Подтверждение пароля',validators =[
    DataRequired (),
    EqualTo ('password',message ='Пароли должны совпадать')
    ])
    user_type =RadioField ('Тип пользователя',
    choices =[('client','Клиент'),('specialist','Специалист')],
    default ='client',
    validators =[DataRequired ()]
    )


    full_name =StringField ('ФИО',validators =[Optional ()])
    gender =SelectField ('Пол',
    choices =[
    ('','Выберите'),
    ('мужской','Мужской'),
    ('женский','Женский')
    ],
    validators =[Optional ()]
    )
    age =IntegerField ('Возраст',validators =[Optional ()])
    experience =IntegerField ('Опыт работы (лет)',validators =[Optional ()])
    field =SelectField ('Сфера деятельности',
    choices =[
    ('','Выберите'),
    ('гражданское право','Гражданское право'),
    ('уголовное право','Уголовное право'),
    ('административное право','Административное право'),
    ('трудовое право','Трудовое право'),
    ('семейное право','Семейное право'),
    ('корпоративное право','Корпоративное право')
    ],
    validators =[Optional ()]
    )

    submit =SubmitField ('Зарегистрироваться')


class VerificationForm (FlaskForm ):
    """
    Форма для верификации email
    """
    email =StringField ('Email',validators =[DataRequired (),Email ()])
    token =StringField ('Код подтверждения',validators =[
    DataRequired (),
    Length (min =6 ,max =6 ,message ="Код должен содержать 6 символов")
    ])
    submit =SubmitField ('Подтвердить')


class AddEventForm (FlaskForm ):
    date =HiddenField ('Дата',validators =[DataRequired ()])
    title =StringField ('Название',validators =[DataRequired ()])
    description =TextAreaField ('Описание')
    submit =SubmitField ('Добавить событие')
