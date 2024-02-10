from flask import Flask, request, jsonify
import engine

from errors import RequestValidationError, OpenAIError

app = Flask(__name__)


def validate_huberman_request(data):
    """
    Validates the request payload for the /ask_huberman endpoint.

    Parameters:
    - data (dict): The JSON payload of the request.

    Raises:
    - RequestValidationError: If the validation checks fail.
    """
    if not data or "message" not in data:
        raise RequestValidationError("Request must contain a 'message' field.")
    if not isinstance(data["message"], str):
        raise RequestValidationError("The 'message' field must be a string.")
    if "history" not in data:
        raise RequestValidationError("Request must contain a 'history' field.")
    if not isinstance(data["history"], list):
        raise RequestValidationError("The 'history' field must be a list.")


@app.errorhandler(404)
def not_found_error(error):
    """Handles 404 Not Found errors."""
    return jsonify({"error": "Resource not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handles 500 Internal Server Error."""
    return jsonify({"error": "Internal server error"}), 500


@app.errorhandler(OpenAIError)
def handle_openai_error(error):
    """Handles errors specifically thrown by OpenAI API interactions."""
    return jsonify({"meta": {}, "errors": {"message": str(error)}}), 500


@app.errorhandler(RequestValidationError)
def handle_request_validation_error(error):
    """Handles request validation errors for the API."""
    return jsonify({"meta": {}, "errors": {"message": error.message}}), 400


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    """Handles any unexpected errors that occur within the application."""
    return (
        jsonify({"meta": {}, "errors": {"message": "An unexpected error occurred."}}),
        500,
    )


@app.route("/health_check", methods=["GET"])
def health_check():
    """
    A health check endpoint to verify the application and OpenAI API are operational.

    Returns:
    - A JSON response indicating the health status.
    """
    try:
        engine.openai_health_check()
        return jsonify({"meta": {"ok": True}}), 200
    except Exception as e:
        return jsonify({"meta": {"ok": False}}), 500


@app.route("/ask_huberman", methods=["POST"])
def ask_huberman():
    """
    The main endpoint to process questions and return responses based on Huberman's podcast content.

    Returns:
    - A JSON response containing the OpenAI response and related context responses.
    """
    data = request.json
    validate_huberman_request(data)

    message = data["message"]
    history = data["history"]
    response_data = engine.get_humberman_response(message, history)

    return jsonify({"meta": {}, "data": response_data}), 200


if __name__ == "__main__":
    app.run(debug=True)
