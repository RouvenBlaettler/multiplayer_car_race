from channels.db import database_sync_to_async
import random


@database_sync_to_async
def handle_accelerate(player, game):
    player.speed += 1
    player.position += player.speed
    crashed = crash(player)
    player.save()

    game.advance_turn()
    game.save()
    return crashed

@database_sync_to_async
def handle_brake(player, game):
    player.speed = max(0, player.speed - 1)
    player.position += player.speed
    player.save()
    crashed = False
    game.advance_turn()
    game.save()
    return crashed

@database_sync_to_async
def handle_nitro(player, game):
    if player.nitro > 0:
        player.position += 10
        player.nitro -= 1
    crashed = crash(player)
    player.save()
    game.advance_turn()
    game.save()
    return crashed

@database_sync_to_async
def handle_ram(player, game):
    for p in game.players.all():
        if p != player:
            if player.position <= p.position <= player.position + player.speed:
                p.hp -= 20
                p.save()
    player.position += player.speed
    crashed = crash(player)
    player.save()
    game.advance_turn()
    game.save()
    return crashed

def crash(player):
    rand_num = random.randint(1, 100)
    if rand_num < player.speed:
        player.hp -= 40
        return True
    return False

@database_sync_to_async
def can_ram(player, game):
    for p in game.players.all():
        if p != player:
            if player.position <= p.position <= player.position + player.speed:
                return True
    return False

    


