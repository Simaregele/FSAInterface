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