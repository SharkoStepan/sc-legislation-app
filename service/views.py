from flask import Blueprint, request, render_template, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from sc_client.client import get_link_content, search_by_template
from sc_client.models import ScAddr, ScIdtfResolveParams, ScTemplate



from .models import (
    find_user_by_username, 
    collect_user_info,
    )

from .utils.string_processing import string_processing
from .utils.ostis_utils import get_term_titles, get_event_by_date
from .services import (
    auth_agent,
    reg_agent,
    user_request_agent,
    directory_agent,
    add_event_agent,
    delete_event_agent,
    show_event_agent
)

from .forms import LoginForm, RegistrationForm, AddEventForm

from .services import (
    # ... существующие импорты
    test_agent_get_question,
    test_agent_get_answers,
    test_agent_save_answer,
    test_agent_check_answer,
    test_agent_delete_old_data,
    test_agent_update_rating
)

from .services import verification_send_token, verification_check_token
from .forms import VerificationForm
from service.agents.ostis import Ostis, result




main = Blueprint("main", __name__)

@main.route("/index")
@login_required
def index():
    return "Hello world!"

@main.route("/protected")
@login_required
def protected():
    return "Только для авторизованных"

@main.route("/about")
def about():
    """
    Метод для реализации ендпоинта, который выводит текущего пользователя
    :return: Разметка страницы
    """
    users = get_term_titles()
    print(users)
    return f"<pre>{str(current_user)}</pre>"

@main.route('/auth', methods=['GET', 'POST'])
def auth():
    """Аутентификация (вход)"""
    if current_user.is_authenticated:
        return redirect(url_for('main.directory'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        
        # Вызов агента аутентификации
        auth_response = auth_agent(email, password)
        
        if auth_response['status'] == 'Valid':
            # Ищем пользователя
            user = find_user_by_username(email)
            
            if user:
                login_user(user)
                flash('Вход выполнен успешно!', 'success')
                return redirect(url_for('main.directory'))
            else:
                flash('Пользователь не найден. Возможно, email не подтвержден.', 'error')
        else:
            flash('Неверный email или пароль', 'error')
    
    return render_template('authorization.html', form=form)


@main.route("/reg", methods=['GET', 'POST'])
def reg():
    """
    Метод для реализации эндпоинта регистрации
    :return: Разметка страницы
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.directory'))
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        # Проверяем, что для специалиста все поля заполнены
        if form.user_type.data == 'specialist':
            if not all([form.full_name.data, form.gender.data, 
                       form.age.data, form.experience.data, form.field.data]):
                flash('Для специалиста необходимо заполнить все дополнительные поля', 'error')
                return render_template('registration.html', form=form)
        
        # Вызываем агент регистрации
        reg_response = reg_agent(
            email=form.email.data,
            password=form.password.data,
            password_conf=form.password_conf.data,
            user_type=form.user_type.data,
            full_name=form.full_name.data if form.user_type.data == 'specialist' else None,
            gender=form.gender.data if form.user_type.data == 'specialist' else None,
            age=str(form.age.data) if form.user_type.data == 'specialist' and form.age.data else None,
            experience=str(form.experience.data) if form.user_type.data == 'specialist' and form.experience.data else None,
            field=form.field.data if form.user_type.data == 'specialist' else None
        )
        
        if reg_response["status"] == "Valid":
            # Сохраняем email И ТИП ПОЛЬЗОВАТЕЛЯ в сессии для верификации
            session['verification_email'] = form.email.data
            session['user_type'] = form.user_type.data  # ← ДОБАВИЛИ ЭТУ СТРОКУ
            flash('Регистрация успешна! Код подтверждения отправлен на ваш email', 'success')
            return redirect(url_for('main.verification'))
        else:
            flash(f'Ошибка регистрации: {reg_response.get("message", "Неизвестная ошибка")}', 'error')
    
    return render_template('registration.html', form=form)

@main.route('/verification', methods=['GET', 'POST'])
def verification():
    """Верификация email с кодом из письма"""
    form = VerificationForm()
    
    # Получаем email из сессии
    email = session.get('verification_email')
    
    if not email:
        flash('Сессия истекла. Пожалуйста, войдите заново.', 'error')
        return redirect(url_for('main.auth'))
    
    # Подставляем email в форму для скрытого поля
    form.email.data = email
    
    if form.validate_on_submit():
        token = form.token.data
        
        try:
            # Проверяем токен через агент верификации
            result = verification_check_token(email, token)
            
            # Получаем статус (может быть строкой или enum)
            status = str(result.get('status', '')).lower()
            
            # Проверяем успешную верификацию
            if 'verified' in status or 'valid' in status or 'success' in status:
                flash('Email успешно подтвержден!', 'success')
                
                # Получаем тип пользователя из сессии
                user_type = session.get('user_type', 'user')
                
                # АВТОМАТИЧЕСКИЙ ВХОД ПОСЛЕ ВЕРИФИКАЦИИ
                user = find_user_by_username(email)
                if user:
                    login_user(user)
                
                # Очищаем данные регистрации из сессии
                session.pop('verification_email', None)
                session.pop('user_type', None)
                
                # РЕДИРЕКТ В ЗАВИСИМОСТИ ОТ ТИПА
                if user_type == 'specialist':
                    flash('Пожалуйста, пройдите тест для подтверждения квалификации.', 'info')
                    return redirect(url_for('main.test_page'))
                else:
                    return redirect(url_for('main.directory'))  # или куда нужно
            else:
                flash(f'Неверный код подтверждения.', 'error')
                
        except Exception as e:
            flash(f'Ошибка при проверке кода: {str(e)}', 'error')
    
    return render_template('verification.html', form=form, email=email)

@main.route('/resend_code', methods=['GET'])
def resend_code():
    """Повторная отправка кода"""
    email = session.get('verification_email')
    
    if not email:
        flash('Сессия истекла. Пожалуйста, зарегистрируйтесь снова.', 'error')
        return redirect(url_for('main.reg'))
    
    # Повторная отправка кода
    send_response = verification_send_token(email)
    
    if send_response['status'] == 'TokenSent':
        flash(f'Новый код отправлен на {email}', 'success')
    else:
        flash('Ошибка отправки кода. Попробуйте позже.', 'error')
    
    return redirect(url_for('main.verification'))


@main.route("/logout")
def logout():
    """
    Метод для реализации эндпоинта выхода с профиля
    :return: Разметка страницы
    """
    logout_user()
    return redirect(url_for('main.auth'))

@main.route("/show_calendar")
@login_required
def show_calendar():
    """
    Метод для реализации эндпоинта календаря
    :return: Разметка страницы
    """
    user = get_link_content(current_user.username)[0].data
    selected_date = request.args.get("selected_date")
    
    events = get_event_by_date(selected_date, user) if selected_date else []
    
    return render_template("calendar.html", 
                         events=events.events if events else [],
                         form=AddEventForm(),
                         selected_date=selected_date)

@main.route("/add_event", methods=["POST"])
@login_required
def add_event():
    """
    Метод для реализации эндпоинта добавления события
    :return: Разметка страницы
    """
    form = AddEventForm()
    if form.validate_on_submit():
        user = get_link_content(current_user.username)[0].data
        add_event_agent(
            user_name=user,
            event_name=form.title.data,
            event_date=form.date.data,
            event_description=form.description.data
        )
    return redirect(url_for('main.show_calendar', selected_date=form.date.data))

@main.route("/delete_event")
@login_required
def delete_event():
    user = get_link_content(current_user.username)[0].data
    event_name = request.args.get("event_name")
    selected_date = request.args.get("selected_date")
    
    delete_event_agent(username=user, event_name=event_name)
    
    return redirect(url_for('main.show_calendar', selected_date=selected_date))

@main.route("/requests", methods=['GET', 'POST'])
@login_required
def requests():
    """
    Метод для реализации эндпоинта юридических запросов
    :return: Разметка страницы
    """
    if request.method == 'POST':
        content = request.form.get("request_entry")
        if content == '':
            flash(f"Для поиска по справочнику требуется ввести текст", category="empty-text-error")
    else:
        content = request.args.get('q')

    if content:
        processed_terms = string_processing(content)
        
        all_results = []
        all_queries = []
        
        for term in processed_terms:
            response = user_request_agent(content=term)
            if response["message"] is not None:
                try:
                    if len(response["message"]) == 0:
                        flash(f"По вашему запросу ничего не найдено", category="empty-result-error")
                        return render_template("requests.html")
                    results = [{
                        'term': item.term,
                        'content': item.content,
                        'related_concepts': item.related_concepts,
                        'related_articles': item.related_articles
                    } for item in response["message"]]
                except AttributeError as e:
                    print(f"Ошибка формата данных: {e}")
                    results = []

                all_results.extend(results)
                all_queries.append(term)
        
        if all_results:
            session['search_query'] = ", ".join(all_queries)
            session['search_results'] = all_results
            return redirect(url_for('main.requests_results'))
        
        return render_template("requests.html")
    
    return render_template("requests.html")

@main.route("/requests_results")
@login_required
def requests_results():
    """
    Метод для реализации эндпоинта просмотра результатов юридических запросов
    :return: Разметка страницы
    """
    query = session.get('search_query', '')
    results = session.get('search_results', [])

    return render_template("requests-results.html", 
                         query=query, 
                         results=results)

@main.route("/directory", methods=['GET', 'POST'])
@login_required
def directory():
    """
    Метод для реализации эндпоинта поиска
    :return: Разметка страницы
    """
    term_titles = get_term_titles()
    if request.method == 'POST':
        content = request.form.get("directory_entry")
        if content == '':
            flash(f"Для поиска по справочнику требуется ввести текст", category="empty-text-error")
            return render_template("directory.html", term_titles=term_titles)
        print(content)
        asked = directory_agent(content=content)

        if asked["message"] is not None:
            session['search_query'] = content
            session['search_results'] = asked["message"]
            return redirect(url_for('main.directory_results'))
        else:
            flash('Ничего не найдено', 'warning')
            return render_template("directory.html", term_titles=term_titles)

    return render_template("directory.html", term_titles=term_titles)

@main.route("/directory_results")
@login_required
def directory_results():
    """
    Метод для реализации эндпоинта просмотра результатов поиска
    :return: Разметка страницы
    """
    query = session.get('search_query', '')
    results = session.get('search_results', [])
    return render_template("directory-results.html", query=query, results=results)

@main.route("/templates")
@login_required
def templates():
    """
    Метод для реализации эндпоинта шаблонов
    :return: Разметка страницы
    """
    return render_template("templates.html")

# ============ TEST ROUTES ============

def get_user_login_from_current_user():
    """Получает email текущего пользователя"""
    # Если current_user.username это уже строка (email) - возвращаем её
    if isinstance(current_user.username, str):
        return current_user.username
    
    # Если это ScAddr - получаем email из SC-памяти
    from sc_client.client import get_link_content
    from sc_client.models import ScAddr
    
    if isinstance(current_user.username, ScAddr):
        link_content_list = get_link_content(current_user.username)
        return link_content_list[0].data
    
    # Fallback
    return str(current_user.username)

@main.route("/test")
@login_required
def test_page():
    """Страница с тестом"""
    return render_template("test.html")

@main.route('/api/test/start', methods=['POST'])
@login_required
def test_start():
    """API для запуска теста"""
    try:
        # Получаем email пользователя
        user_email = get_user_login_from_current_user()
        
        print(f"DEBUG: user_email = {user_email}")
        
        # Передаем email в агент
        result = test_agent_delete_old_data(user_email)
        
        if result['status'] == 'valid':
            return {'success': True, 'message': 'Тест запущен'}
        return {'success': False, 'message': result.get('message', 'Ошибка')}, 400
        
    except Exception as e:
        print(f"ERROR in test_start: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'message': str(e)}, 500

@main.route('/api/test/question', methods=['GET'])
@login_required
def test_get_question():
    """API для получения вопроса"""
    try:
        user_email = get_user_login_from_current_user()
        result = test_agent_get_question(user_email)
        
        print(f"DEBUG test_get_question result: {result}")
        
        if result['status'] == 'valid':
            question_addr = result.get('question_addr')
            if not question_addr:
                return {'success': False, 'message': 'Нет вопросов'}, 404
            
            import sc_client.client as client
            from sc_client.models import ScIdtfResolveParams, ScTemplate
            from sc_client.constants import sc_types
            
            # Получаем nrel_content
            nrel_content = client.resolve_keynodes(
                ScIdtfResolveParams(idtf="nrel_content", type=sc_types.NODE_CONST_NOROLE)
            )[0]
            
            # Шаблон для получения текста вопроса
            content_template = ScTemplate()
            content_template.quintuple(
                question_addr,
                sc_types.EDGE_D_COMMON_VAR,
                sc_types.LINK_VAR >> "content_link",
                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                nrel_content
            )
            
            content_result = client.template_search(content_template)
            question_text = str(question_addr.value)  # По умолчанию ID
            
            if content_result and len(content_result) > 0:
                content_link = content_result[0].get("content_link")
                content_data = client.get_link_content(content_link)
                if content_data:
                    question_text = content_data[0].data
            
            return {
                'success': True,
                'question': {
                    'id': str(question_addr.value),
                    'text': question_text,
                    'addr': str(question_addr.value)
                }
            }, 200
        else:
            return {'success': False, 'message': result.get('message', 'Ошибка')}, 404
            
    except Exception as e:
        print(f"ERROR in test_get_question: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'message': str(e)}, 500

@main.route('/api/test/answer', methods=['POST'])
@login_required
def test_save_answer():
    """API для сохранения ответа"""
    try:
        data = request.get_json()
        question_id = data.get('question_id')
        answer_id = data.get('answer_id')
        user_email = get_user_login_from_current_user()

        from sc_client.models import ScAddr
        answer_addr = ScAddr(int(answer_id))

        # Сохраняем ответ
        save_result = test_agent_save_answer(answer_addr, user_email)
        
        if save_result['status'] == 'valid':
            question_addr = ScAddr(int(question_id))
            check_result = test_agent_check_answer(question_addr, user_email)
            
            # ✅ ИСПРАВЛЕНО: Используем is_correct из результата
            is_correct = check_result.get('is_correct', False)
            print(f"DEBUG: Question {question_id}, is_correct = {is_correct}")
            
            return {'success': True, 'is_correct': is_correct}, 200
        else:
            return {'success': False, 'message': 'Ошибка сохранения ответа'}, 400
    except Exception as e:
        print(f"Error in save_answer: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'message': str(e)}, 400

@main.route('/api/test/rating', methods=['GET'])
@login_required
def test_get_rating():
    """API для получения рейтинга"""
    user_email = get_user_login_from_current_user()
    result = test_agent_update_rating(user_email)
    
    if result['status'] == 'valid':
        return {'success': True, 'rating': result.get('rating', 0)}  # <- ИСПРАВЛЕНО
    return {'success': False, 'message': 'Ошибка получения рейтинга'}, 400

@main.route('/api/test/finish', methods=['POST'])
@login_required
def test_finish():
    """API для завершения теста"""
    user_email = get_user_login_from_current_user()
    result = test_agent_update_rating(user_email)
    
    if result['status'] == 'valid':
        return {
            'success': True, 
            'rating': result.get('rating', 0),
            'message': 'Тест завершен!'
        }, 200
    return {'success': False, 'message': 'Ошибка завершения теста'}, 400

@main.route("/api/test/answers/<question_id>", methods=["GET"])
@login_required
def test_get_answers(question_id):
    """API: Получить варианты ответов для вопроса"""
    try:
        import sc_client.client as client
        from sc_client.models import ScIdtfResolveParams, ScAddr, ScTemplate
        from sc_client.constants import sc_types
        
        question_addr = ScAddr(int(question_id))
        result = test_agent_get_answers(question_addr)
        
        print(f"DEBUG test_get_answers result: {result}")
        
        if result['status'] == 'valid':
            answers_list = []
            
            # Получаем nrel_content для текстов ответов
            nrel_content = client.resolve_keynodes(
                ScIdtfResolveParams(idtf='nrel_content', type=sc_types.NODE_CONST_NOROLE)
            )[0]
            
            for answer_item in result.get('answers', []):
                answer_addr = answer_item['answer_addr']
                
                # Ищем текст ответа через nrel_content
                answer_template = ScTemplate()
                answer_template.quintuple(
                    answer_addr,
                    sc_types.EDGE_D_COMMON_VAR,
                    sc_types.LINK_VAR >> "_answer_link",
                    sc_types.EDGE_ACCESS_VAR_POS_PERM,
                    nrel_content
                )
                
                answer_result = client.template_search(answer_template)
                
                answer_text = str(answer_addr.value)  # По умолчанию показываем ID
                if answer_result and len(answer_result) > 0:
                    answer_link = answer_result[0].get("_answer_link")
                    answer_content = client.get_link_content(answer_link)
                    if answer_content and len(answer_content) > 0:
                        answer_text = answer_content[0].data
                
                answers_list.append({
                    "id": str(answer_addr.value),
                    "text": answer_text,
                    "addr": str(answer_addr.value)
                })
            
            return {
                "success": True,
                "answers": answers_list
            }, 200
        else:
            return {"success": False, "message": "Не удалось получить ответы"}, 404
    except Exception as e:
        print(f"ERROR in test_get_answers: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": str(e)}, 500
    
# ========== ФОРУМ ==========

@main.route('/forum')
@login_required
def forum():
    """Главная страница форума - список топиков"""
    try:
        from .agents.ostis import Ostis
        from config import Config
        
        ostis_instance = Ostis(Config.OSTIS_URL)
        topics = ostis_instance.get_all_topics()
        
        return render_template('forum.html', topics=topics)
    except Exception as e:
        flash(f'Ошибка загрузки форума: {str(e)}', 'error')
        return render_template('forum.html', topics=[])


@main.route('/forum/create_topic')
@login_required
def forum_create_topic():
    """Страница создания нового топика"""
    return render_template('forum_create_topic.html')


@main.route('/forum/create_topic', methods=['POST'])
@login_required
def forum_create_topic_post():
    """Создание нового топика"""
    try:
        from .agents.ostis import Ostis, result
        from config import Config
        
        title = request.form.get('title')
        description = request.form.get('description')
        
        if not title or not description:
            flash('Заполните все поля', 'error')
            return redirect(url_for('main.forum_create_topic'))
        
        # ← ИСПРАВЛЕНО: используем готовую функцию
        username = get_user_login_from_current_user()
        if not username:
            flash('Пользователь не авторизован', 'error')
            return redirect(url_for('main.auth'))
        
        ostis_instance = Ostis(Config.OSTIS_URL)
        response = ostis_instance.call_add_topic_agent(
            action_name="action_add_topic",
            username=username,
            title=title,
            description=description
        )
        
        if response and response.get('message') == result.SUCCESS:
            flash('Топик успешно создан!', 'success')
            return redirect(url_for('main.forum'))
        else:
            flash('Ошибка создания топика', 'error')
            return redirect(url_for('main.forum_create_topic'))
            
    except Exception as e:
        flash(f'Ошибка: {str(e)}', 'error')
        return redirect(url_for('main.forum_create_topic'))


@main.route('/forum/topic/<int:topic_addr>')
@login_required
def forum_topic(topic_addr):
    try:
        from .agents.ostis import Ostis
        from config import Config
        
        
        topic_sc_addr = ScAddr(topic_addr)
        ostis_instance = Ostis(Config.OSTIS_URL)
        
        topic_details = ostis_instance.get_topic_details(topic_sc_addr)
        messages = ostis_instance.get_topic_messages(topic_sc_addr)
        
        return render_template(
            'forum_topic.html',
            topic=topic_details,
            messages=messages,
            topic_addr=topic_addr
        )
    except Exception as e:
        flash(f'Ошибка загрузки топика: {str(e)}', 'error')
        return redirect(url_for('main.forum'))

@main.route('/forum/topic/<int:topic_addr>/add_message', methods=['POST'])
@login_required
def forum_add_message(topic_addr):
    """Добавление сообщения в топик"""
    try:
        from .agents.ostis import Ostis, result
        from config import Config
        
        
        message_text = request.form.get('message')
        
        if not message_text:
            flash('Сообщение не может быть пустым', 'error')
            return redirect(url_for('main.forum_topic', topic_addr=topic_addr))
        
        # ← ИСПРАВЛЕНО: используем готовую функцию
        username = get_user_login_from_current_user()
        if not username:
            flash('Пользователь не авторизован', 'error')
            return redirect(url_for('main.auth'))
        
        topic_sc_addr = ScAddr(topic_addr)
        
        ostis_instance = Ostis(Config.OSTIS_URL)
        response = ostis_instance.call_add_message_agent(
            action_name="action_add_message",
            username=username,
            topic_addr=topic_sc_addr,
            message_text=message_text
        )
        
        if response and response.get('message') == result.SUCCESS:
            flash('Сообщение добавлено!', 'success')
        else:
            flash('Ошибка добавления сообщения', 'error')
            
        return redirect(url_for('main.forum_topic', topic_addr=topic_addr))
        
    except Exception as e:
        flash(f'Ошибка: {str(e)}', 'error')
        return redirect(url_for('main.forum_topic', topic_addr=topic_addr))
