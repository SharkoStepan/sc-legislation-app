from flask import Blueprint, request, render_template, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from sc_client.client import get_link_content, search_by_template

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

@main.route("/auth", methods=['GET','POST'])
def auth():
    """
    Метод для реализации эндпоинта аутентификации
    :return: Разметка страницы
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.directory'))
    form = LoginForm()
    if form.validate_on_submit():
        user = find_user_by_username(form.username.data)
        auth_response = auth_agent(form.username.data, form.password.data)
        if auth_response["status"] == "Valid":
            login_user(user)
            return redirect(url_for('main.directory'))
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
        reg_response = reg_agent(
            gender=form.gender.data,
            surname=form.surname.data,
            name=form.name.data,
            fname=form.patronymic.data,
            reg_place=form.reg_place.data,
            birthdate=form.birthdate.data,
            username=form.username.data,
            password=form.password.data
        )
        if reg_response["status"] == "Valid":
            user = find_user_by_username(form.username.data)
            login_user(user)
            return redirect(url_for('main.directory'))
    return render_template('registration.html', form=form)

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
    """Получить строку логина из current_user"""
    from sc_client.client import get_link_content
    link_content_list = get_link_content(current_user.username)
    return link_content_list[0].data


@main.route("/test")
@login_required
def test_page():
    """Страница с тестом"""
    return render_template("test.html")


@main.route("/api/test/start", methods=["POST"])
@login_required
def test_start():
    """API: Начать новый тест"""
    user_login = get_user_login_from_current_user()
    result = test_agent_delete_old_data(user_login)
    
    if result['status'] == 'valid':
        return {"success": True, "message": "Тест начат"}
    return {"success": False, "message": result.get('message', 'Ошибка')}, 400

@main.route("/api/test/question", methods=["GET"])
@login_required
def test_get_question():
    """API: Получить следующий вопрос"""
    try:
        user_login = get_user_login_from_current_user()
        result = test_agent_get_question(user_login)

        print(f"DEBUG test_get_question result: {result}")

        if result['status'] == 'valid':
            question_addr = result.get('question_addr')

            if not question_addr:
                return {"success": False, "message": "Вопрос не найден"}, 404

            import sc_client.client as client
            from sc_client.models import ScIdtfResolveParams, ScTemplate
            from sc_client.constants import sc_types

            # Ищем текст вопроса через nrel_content
            nrel_content = client.resolve_keynodes(
                ScIdtfResolveParams(idtf='nrel_content', type=sc_types.NODE_CONST_NOROLE)
            )[0]
            
            # Шаблон для поиска контента вопроса
            content_template = ScTemplate()
            content_template.quintuple(
                question_addr,
                sc_types.EDGE_D_COMMON_VAR,
                sc_types.LINK_VAR >> "_content_link",
                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                nrel_content
            )
            
            content_result = client.template_search(content_template)
            
            question_text = str(question_addr.value)  # По умолчанию
            if content_result and len(content_result) > 0:
                content_link = content_result[0].get("_content_link")
                content_data = client.get_link_content(content_link)
                if content_data:
                    question_text = content_data[0].data

            return {
                "success": True,
                "question": {
                    "id": str(question_addr.value),
                    "text": question_text,
                    "addr": str(question_addr.value)
                }
            }, 200
        else:
            return {"success": False, "message": result.get('message', 'Не удалось получить вопрос')}, 404
    except Exception as e:
        print(f"ERROR in test_get_question: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": str(e)}, 500

@main.route("/api/test/answer", methods=["POST"])
@login_required
def test_save_answer():
    """API: Сохранить ответ пользователя"""
    try:
        data = request.get_json()
        question_id = data.get('question_id')
        answer_id = data.get('answer_id')
        
        user_login = get_user_login_from_current_user()
        
        # Преобразуем answer_id в ScAddr
        from sc_client.models import ScAddr
        answer_addr = ScAddr(int(answer_id))
        
        # Сохраняем ответ - передаём напрямую ScAddr
        save_result = test_agent_save_answer(answer_addr, user_login)
        
        if save_result['status'] == 'valid':
            # Проверяем правильность
            question_addr = ScAddr(int(question_id))
            check_result = test_agent_check_answer(question_addr, user_login)
            
            is_correct = check_result.get('status') == 'valid'
            
            return {
                "success": True,
                "is_correct": is_correct
            }, 200
        else:
            return {"success": False, "message": "Ошибка сохранения"}, 400
    except Exception as e:
        print(f"Error in save_answer: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": str(e)}, 400


@main.route("/api/test/rating", methods=["GET"])
@login_required
def test_get_rating():
    """API: Получить рейтинг"""
    user_login = get_user_login_from_current_user()
    result = test_agent_update_rating(user_login)
    
    if result['status'] == 'valid':
        return {
            "success": True,
            "rating": result.get('rating', 0)
        }
    
    return {"success": False, "message": "Ошибка получения рейтинга"}, 400


@main.route("/api/test/finish", methods=["POST"])
@login_required
def test_finish():
    """API: Завершить тест"""
    user_login = get_user_login_from_current_user()
    result = test_agent_update_rating(user_login)
    
    if result['status'] == 'valid':
        return {
            "success": True,
            "rating": result.get('rating', 0),
            "message": "Тест завершен!"
        }
    
    return {"success": False, "message": "Ошибка завершения"}, 400

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

