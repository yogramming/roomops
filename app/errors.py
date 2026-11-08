from flask import jsonify
from werkzeug.exceptions import HTTPException


def register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        return jsonify(
            {
                "error": error.name.lower().replace(" ", "_"),
                "message": error.description,
            }
        ), error.code

    @app.errorhandler(Exception)
    def handle_unexpected_exception(error):
        app.logger.exception("Unhandled application exception")

        return jsonify(
            {
                "error": "internal_server_error",
                "message": "An unexpected error occurred",
            }
        ), 500
