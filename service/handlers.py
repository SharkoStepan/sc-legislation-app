from flask import jsonify
from .exceptions import APIError, AgentError


def register_error_handlers(app):
    """
    Метод для отлавливания ошибок регистрации
    :param app: Приложение
    """
    @app.errorhandler(APIError)
    def handle_api_error(error):
        """
        Метод для отлавливания ошибки на стороне API
        :param error: Ошибка
        :return: Ошибка в виде JSON
        """
        response = jsonify(error.to_dict())
        response.status_code = error.code
        return response

    @app.errorhandler(404)
    def handle_not_found_error(error):
        """
        Метод для отлавливания ошибки 404
        :param error: Ошибка
        :return: Ошибка в виде JSON
        """
        return jsonify({
            "error": "not_found",
            "message": "The requested resource was not found."
        }), 404
    
    @app.errorhandler(AgentError)
    def handle_unexpected_error(error: AgentError):
        """
        Метод для отлавливания ошибки на стороне агента
        :param error: Ошибка
        :return: Ошибка в виде JSON
        """
        return jsonify({
            "error": "agent_error",
            "message": error.message
        }), error.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """
        Метод для отлавливания всех ошибок
        :param error: Ошибка
        :return: Ошибка в виде JSON
        """
        return jsonify({
            "error": "unexpected_error",
            "message": str(error)
        }), 500