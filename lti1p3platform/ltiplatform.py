from __future__ import annotations
from abc import ABCMeta, abstractmethod
from .registration import Registration


class LTI1P3PlatformConfAbstract:
    __metaclass__ = ABCMeta
    _registration = None
    
    """
    LTI 1.3 Platform Data storage abstract class
    """
    @abstractmethod
    def __init__(self, **kwargs):
        pass

    @abstractmethod
    def get_registration_by_params(self, iss, client_id, **kwargs) -> Registration | None:
        raise NotImplementedError()

    @abstractmethod
    def set_user_data(self):
        raise NotImplementedError

    def get_registration(self, **kwargs) -> Registration | None:
        if not self._registration:
            self._registration = self.get_registration_by_params(**kwargs)
        
        return self._registration
    
    def get_jwks(self):
        """
        Get JWKS
        """
        return self._registration.get_jwks()
    