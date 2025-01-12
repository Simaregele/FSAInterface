from abc import ABC, abstractmethod

class BaseAuthenticator(ABC):
    @abstractmethod
    def login(self, credentials: dict) -> bool:
        pass
    
    @abstractmethod
    def logout(self) -> None:
        pass
    
    @abstractmethod
    def is_authenticated(self) -> bool:
        pass
    
    @abstractmethod
    def get_token(self) -> str:
        pass

class JWTAuthenticator(BaseAuthenticator):
    def __init__(self, auth_url: str, token_field: str = "access"):
        self.auth_url = auth_url
        self.token_field = token_field
        
    def login(self, credentials: dict) -> bool:
        # Реализация JWT авторизации
        pass

class OAuth2Authenticator(BaseAuthenticator):
    # Реализация OAuth2 авторизации
    pass 