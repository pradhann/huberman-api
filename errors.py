"""
errors.py

Defines custom exception classes for the Flask application to handle specific error conditions more gracefully.
These exceptions are used throughout the application to signal error states in a controlled manner, allowing
for consistent error responses and easier debugging.

Custom exceptions include:
- RequestValidationError: For errors related to request payload validation.
- ProcessingError: For errors that occur during the processing of a request, not related to external API calls.
- OpenAIError: For errors specifically related to interactions with the OpenAI API.

Each exception includes a message attribute that can be used to convey more information about the error to the client.
"""


class RequestValidationError(Exception):
    """
    Exception raised for validation errors in request payloads.

    Attributes:
    - message (str): Explanation of the error.
    """

    def __init__(self, message="Invalid request data"):
        self.message = message
        super().__init__(self.message)


class ProcessingError(Exception):
    """
    Exception raised for errors during processing of a request.

    Attributes:
    - message (str): Explanation of the error.
    """

    def __init__(self, message="A processing error occurred", error_type=None):
        super().__init__(message)
        self.error_type = error_type


class OpenAIError(Exception):
    """
    Exception raised for errors in OpenAI API calls.

    Attributes:
    - message (str): Explanation of the error.
    """

    def __init__(
        self, message="Error occurred while making the request to OpenAI", error_type=""
    ):
        super().__init__(message)
        self.error_type = error_type
