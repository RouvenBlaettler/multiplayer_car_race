from channels.db import database_sync_to_async

@database_sync_to_async
def handle_accelerate(player, game):
    player.speed += 1
    player.position += player.speed
    player.save()

    game.advance_turn()
    game.save()

@database_sync_to_async
def handle_brake(player, game):
    player.speed = max(0, player.speed - 1)
    player.position += player.speed
    player.save()

    game.advance_turn()
    game.save()

@database_sync_to_async
def handle_nitro(player, game):
    if player.nitro > 0:
        player.position += 10
        player.nitro -= 1
    player.save()
    game.advance_turn()
    game.save()

@database_sync_to_async
def handle_ram(player, game):
    for p in game.players.all():
        if p != player:
            if abs(p.position - player.position) <= 1:
                p.hp -= 20
                p.save()

    player.position += player.speed
    player.save()
    game.advance_turn()
    game.save()

