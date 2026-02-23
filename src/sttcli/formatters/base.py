from abc import ABC, abstractmethod

from sttcli.models import TranscriptResult


class BaseFormatter(ABC):
    @abstractmethod
    def format(self, result: TranscriptResult) -> str: ...
