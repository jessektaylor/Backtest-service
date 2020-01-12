from .wsgi import *
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import historical.routing
import live.routing

application = ProtocolTypeRouter({
    # (http->django views is added by default)
    'websocket': AuthMiddlewareStack(
        URLRouter(
            live.routing.websocket_urlpatterns +
            # second  connection
            historical.routing.websocket_urlpatterns
        
        )
    ),
})

