from abc import ABC, abstractmethod
from argparse import ArgumentParser

class NaqTool(ABC):
    def __init__(self, parser: ArgumentParser):
        self.parser = parser
        self._populate_parser()

    @abstractmethod
    def _populate_parser(self):
        """Populate the argument parser with tool-specific arguments."""
        ...

    @abstractmethod
    def main(self):
        """Execute the main functionality of the tool."""
        ...
