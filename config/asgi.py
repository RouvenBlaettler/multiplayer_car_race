"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

#ASGI is a asynchrounous interface between the web server and python webapp. ASGI is for handling request asynchronous.

import os
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
import game.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings') #tells django which settings to use(in this case cofnig/settings)

application = ProtocolTypeRouter({
    "http": get_asgi_application(),    #if http request: send to django application(django view)
    "websocket": AuthMiddlewareStack(  #if WS: send to WS routing(channels conusmer)
        URLRouter(
            game.routing.websocket_urlpatterns
        )
    ),
})