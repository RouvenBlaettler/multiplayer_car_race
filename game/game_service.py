from channels.db import database_sync_to_async
import random


@database_sync_to_async
def handle_accelerate(player, game, danger_fields):
    player.speed += 1
    player.position += player.speed
    crashed = crash(player, danger_fields)
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
def handle_nitro(player, game, danger_fields):
    if player.nitro > 0:
        player.position += 10
        player.nitro -= 1
    crashed = crash(player, danger_fields)
    player.save()
    game.advance_turn()
    game.save()
    return crashed

@database_sync_to_async
def handle_ram(player, game, danger_fields):
    for p in game.players.all():
        if p != player:
            if player.position <= p.position <= player.position + player.speed:
                p.hp -= 20
                p.save()
    player.position += player.speed
    crashed = crash(player, danger_fields)
    player.save()
    game.advance_turn()
    game.save()
    return crashed

def crash(player, danger_fields):
    rand_num = random.randint(1, 100)
    if player.position in danger_fields:
        if rand_num < (player.speed * 3):
            player.hp -= 40
            player.save()
            return True
    else:    
        if rand_num < player.speed:
            player.hp -= 40
            player.save()
            return True
    return False

@database_sync_to_async
def can_ram(player, game):
    for p in game.players.all():
        if p != player:
            if player.position <= p.position <= player.position + player.speed:
                return True
    return False

def danger_zones(game):
    danger_field_1 = random.randint(1, 100)
    danger_field_2 = random.randint(1, 100)
    danger_field_3 = random.randint(1, 100)
    danger_fields = (danger_field_1, danger_field_2, danger_field_3)
    return danger_fields

    


