from django.contrib import admin
from .models import Game, Player, TurnAction

admin.site.register(Game)
admin.site.register(Player)
admin.site.register(TurnAction)
