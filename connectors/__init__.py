# Service connectors: Talk to external systems
# Each connector provides HTTP/RPC/SDK access to external services
# (APIs, databases, cloud platforms, etc)

from .arr_stack import ArrStackConnector
from .home_assistant import HomeAssistantConnector
from .plex import PlexConnector
from .qnap import QNAPConnector
from .seedbox import SeedboxConnector
