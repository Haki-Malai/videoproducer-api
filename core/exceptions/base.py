from http import HTTPStatus


class CustomException(Exception):
    status_code = HTTPStatus.BAD_GATEWAY
    message = HTTPStatus.BAD_GATEWAY.description
    description = HTTPStatus.BAD_GATEWAY.description

    def __init__(self, message=None):
        if message:
            self.message = message


class NotFoundException(CustomException):
    status_code = HTTPStatus.NOT_FOUND
    message = HTTPStatus.NOT_FOUND.name
    description = HTTPStatus.NOT_FOUND.description


class BadRequestException(CustomException):
    status_code = HTTPStatus.BAD_REQUEST
    message = HTTPStatus.BAD_REQUEST.name
    description = HTTPStatus.BAD_REQUEST.description


class UnauthorizedException(CustomException):
    status_code = HTTPStatus.UNAUTHORIZED
    message = HTTPStatus.UNAUTHORIZED.name
    description = HTTPStatus.UNAUTHORIZED.description


class ForbiddenException(CustomException):
    status_code = HTTPStatus.FORBIDDEN
    message = HTTPStatus.FORBIDDEN.name
    description = HTTPStatus.FORBIDDEN.description
