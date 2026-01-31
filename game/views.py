from django.shortcuts import render, redirect, get_object_or_404
from .models import Game, Player
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm



def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()

    return render(request, 'games/register.html', {'form': form})
        
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username = username, password = password)
        if user:
            login(request, user)
            return redirect('game_lobby')

        else:
            return render(request, 'game/login.html', {'error': 'incorrect password or username' })
        
    return render(request, 'game/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

    



@login_required
def game_lobby(request):
    available_games = Game.objects.filter(status="waiting")
    context = {"available_games": available_games}
    return render(request, "game/gamelobby.html", context)

@login_required
def game_view(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    player = get_object_or_404(Player, user=request.user, game=game)
    context = {"game": game, "player": player}
    return render(request, "game/game.html", context)

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



