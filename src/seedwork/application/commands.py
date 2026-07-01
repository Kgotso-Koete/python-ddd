from seedwork.foundation import Command as FoundationCommand
from pydantic import ConfigDict


class Command(FoundationCommand):
    """Abstract base class for all commands"""
    model_config = ConfigDict(arbitrary_types_allowed=True)