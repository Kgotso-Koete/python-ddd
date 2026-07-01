from typing import Union

from seedwork.foundation.message import Message

HandlerAlias = Union[type[Message], str]
DependencyIdentifier = Union[type, str]
