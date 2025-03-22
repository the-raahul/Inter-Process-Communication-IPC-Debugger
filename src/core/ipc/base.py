from abc import ABC, abstractmethod

class IPCBase(ABC):
    @abstractmethod
    def send(self, data):
        pass

    @abstractmethod
    def receive(self):
        pass