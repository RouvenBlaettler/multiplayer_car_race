from django.contrib import admin
from .models import Game, Player, TurnAction

admin.site.register(Game)
admin.site.register(Player)     #register models in admin panel to edit them there
admin.site.register(TurnAction)
