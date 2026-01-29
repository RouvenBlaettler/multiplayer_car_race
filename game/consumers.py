from channels.generic.websocket import AsyncWebsocketConsumer
import json
from .models import Player, Game
from .game_service import handle_accelerate, handle_brake, handle_nitro, handle_ram
from django.shortcuts import get_object_or_404
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.user = self.scope["user"]

        if isinstance(self.user, AnonymousUser):
            await self.close()
            return
        
        self.player = await self.get_player(self.user, self.game_id)
        if not self.player:
            await self.close()
            return

        self.room_group_name = f'game_{self.game_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()


    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )



    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if not action:
            return
        
        game = await self.get_game(self.game_id)

        if game.current_turn_id != self.player.id:
            await self.send_json({'error': 'Not your turn'})
            return
        
        if action == 'accelerate':
            await handle_accelerate(self.player, game)
            
        elif action == 'brake':
            await handle_brake(self.player, game)

        elif action == 'nitro':
            await handle_nitro(self.player, game)

        elif action == 'ram':
            await handle_ram(self.player, game)

        else:
            await self.send_json({'error': 'Invalid action'})
            return
        
        game_ended = await self.game_end_check(game)
        
        state = await self.serialize_game(game)
        state['game_ended'] = game_ended
        if game_ended:
            state['winner_id'] = game.winner_id
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'game_state',
                'state': state
            }
        )

    async def game_state(self, event):
        await self.send_json(event['state'])


    

    @database_sync_to_async
    def get_player(self, user, game_id):
        try:
            return Player.objects.get(user=user, game_id=game_id)
        except Player.DoesNotExist:
            return None
        
    @database_sync_to_async
    def get_game(self, game_id):
        return get_object_or_404(Game, id=game_id)
    
    @database_sync_to_async
    def serialize_game(self, game):
        players = list(game.players.all().values('id', 'user__username', 'position', 'speed', 'hp', 'nitro'))

                       
        return {
            'game_id': game.id,
            'current_turn': game.current_turn_id,
            'players': players,
        }
    
    @database_sync_to_async
    def game_end_check(self, game):
        players = list(game.players.all())

        # Check for position win first
        for p in players:
            if p.position >= 100:
                game.status = 'finished'
                game.winner = p
                game.save()
                return True

        # Check for HP elimination
        alive_players = [p for p in players if p.hp > 0]
        if len(alive_players) == 1:
            game.status = 'finished'
            game.winner = alive_players[0]
            game.save()
            return True

        return False







