from django.shortcuts import render, redirect, get_object_or_404
from .models import Game, Player
# Create your views here.


def game_lobby(request):
    available_games = list(Game.objects.filter(status = "waiting"))

    context = {"available_games":available_games}
    return render(request, "gamelobby.html", context)


def game_view(request, game_id):
    game = get_object_or_404(Game, id = game_id, player = request.player)


"""Yes, exactly. For a minimal setup you need:

View 1: Game Lobby (create/join game)

List available games or create a new one
Join a game → redirects to game view
View 2: Game View (play the game)

Shows the game board
WebSocket connection
Action buttons
Updates in real-time
Simplest approach for testing:

Use Django admin to manually create a game and 2 players
Build only the "Game View" that loads an existing game by ID
Open it in 2 browser tabs (logged in as different users)
Want to start with the simple approach just to get something working?"""