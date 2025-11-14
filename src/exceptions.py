from fastapi import HTTPException


class NotFound(HTTPException):
    def __init__(self, message, **kwargs):
        self.status_code = 404
        self.detail = {'error': message, **kwargs}


class DuplicatedEvent(HTTPException):
    def __init__(self, message = 'Duplicated input event', **kwargs):
        self.status_code = 400
        self.detail = {'error': message, **kwargs}


class UnknownEventUser(HTTPException):
    def __init__(self, message = 'The user of event is unknown', **kwargs):
        self.status_code = 404
        self.detail = {'error': message, **kwargs}
