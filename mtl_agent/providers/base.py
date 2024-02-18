from abc import ABC, abstractmethod

class BaseProvider(ABC):
    def __init__(self, config):
        self.config = config
    
    # @abstractmethod
    async def upload(self):
        """Uploads a video to the provider"""
        pass
    
    # @abstractmethod
    def get_cookies(self) -> list[dict]:
        """Provides the cookies for the provider"""
        pass
    
    # @abstractmethod
    async def get_video_url(self) -> str:
        """Returns the video url"""
        pass