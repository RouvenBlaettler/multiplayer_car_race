from django.shortcuts import render, redirect, get_object_or_404
from .models import Game, Player
from django.contrib.auth.decorators import login_required

@login_required
def game_lobby(request):
    available_games = Game.objects.filter(status="waiting")
    context = {"available_games": available_games}
    return render(request, "game/gamelobby.html", context)


def game_view(request, game_id):
    game = get_object_or_404(Game, id = game_id, player = request.player)

@login_required
def join_game(request, game_id):
    game = get_object_or_404(Game, id = game_id, status = 'waiting')
    if not Player.objects.filter(user=request.user, game=game).exists():
        Player.objects.create(user=request.user, game=game)
    game.refresh_from_db()
    players = list(game.players.all())
    if len(players) == 2:
        game.status = 'active'
        game.current_turn = players[0]
        game.save()

    return redirect('game_view', game_id=game.id)

