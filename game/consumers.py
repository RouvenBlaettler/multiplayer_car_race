from channels.generic.websocket import AsyncWebsocketConsumer
import json
from .models import Player, Game
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
            await self.handle_accelerate(game)
            
        elif action == 'brake':
            await self.handle_brake(game)

        else:
            await self.send_json({'error': 'Invalid action'})
            return
        
        state = await self.serialize_game(game)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'game_state',
                'state': state
            }
        )

    async def game_update(self, event):
        await self.send_json(event['state'])


    @database_sync_to_async
    def handle_accelerate(self, game):
        self.player.position += 1
        self.player.save()

        game.advance_turn()
        game.save()

    @database_sync_to_async
    def handle_brake(self, game):
        self.player.position = max(0, self.player.position - 1)
        self.player.save()

        game.advance_turn()
        game.save()

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
        players = list(game.players.all().values('id', 'user__username', 'position'))

                       
        return {
            'game_id': game.id,
            'current_turn': game.current_turn_id,
            'players': players,
        }
    
    
    