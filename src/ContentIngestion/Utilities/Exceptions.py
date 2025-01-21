class DocumentNotFoundException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

class PDFParsingException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

class AccessTokenNotFoundException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message
        
class ConfigurationLoadException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

class OpenAIConnectionError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

class NoResultFound(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

class IndexNotSupported(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message
        
class QueryTypeInvalidOrNotSupported(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message