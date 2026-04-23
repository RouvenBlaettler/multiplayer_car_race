from channels.generic.websocket import AsyncWebsocketConsumer
import json
from .models import Player, Game
from .game_service import handle_accelerate, handle_brake, handle_nitro, handle_ram, can_ram
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
import datetime

class GameConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        #ASGI server accepts WS and creates scope dic with data about connection
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.user = self.scope["user"]

        if isinstance(self.user, AnonymousUser):
            #terminate WS connection
            await self.close()   #await means until DB is ready server can start processing other consumers
            return
        
        self.player = await self.get_player(self.user, self.game_id)
        if not self.player:
            await self.close()
            return

        game = await self.get_game(self.game_id)
        if not game:
            await self.close()
            return
        
        now = timezone.now()

        # Reconnect grace: player disconnected less than 30s ago.
        if self.player.disconnected_at and (now - self.player.disconnected_at) <= datetime.timedelta(seconds=30):
            if game.status == 'active' and game.current_turn_id == self.player.id:
                game.turn_deadline = now + datetime.timedelta(seconds=30)
                await self.save_game(game)

        await self.mark_player_connected(self.player)

        self.room_group_name = f'game_{self.game_id}'

        await self.channel_layer.group_add(  #channel layer is the messaging system behind WS consumer
            self.room_group_name,
            self.channel_name   #name/ID of specific WS connection
        )

        await self.accept()   #accept WS connection
        
        # Send initial game state
        state = await self.serialize_game(game)
        state['can_ram'] = await can_ram(self.player, game)
        state['danger_fields'] = game.danger_fields
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'game_state',
                'state': state
            }
        )


    async def disconnect(self, close_code):   #close_code = code explaining why WS closed
        game = await self.get_game(self.game_id)
        if game.current_turn_id == self.player.id:
            await self.call_advance_turn(game)
        try:     #check if player and group were even created before disconnecting
            if self.player:
                await self.mark_player_disconnected(self.player)
        except AttributeError:
            pass
        try:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        except AttributeError:
            pass





    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if not action:
            return
        
        # Refresh player data to avoid stale cached values
        self.player = await self.get_player(self.user, self.game_id)
        if not self.player:
            await self.close()
            return

        game = await self.get_game(self.game_id)
        if not game:
            await self.close()
            return

        now = timezone.now()

        if game.turn_deadline and now > game.turn_deadline:
            await self.call_advance_turn(game)
            # Broadcast updated game state to all players
            state = await self.serialize_game(game)
            state['timeout'] = True
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'game_state',
                    'state': state
                }
            )
            return

        if game.status == 'finished':
            await self.send(text_data=json.dumps({'error': 'Game is finished'}))
            return

        if game.current_turn_id != self.player.id:
            await self.send(text_data=json.dumps({'error': 'Not your turn'}))
            return
        
        danger_fields = game.danger_fields

        if action == 'accelerate':
            crashed = await handle_accelerate(self.player, game, danger_fields)
            
        elif action == 'brake':
            crashed = await handle_brake(self.player, game)

        elif action == 'nitro':
            crashed = await handle_nitro(self.player, game, danger_fields)

        elif action == 'ram':
            crashed = await handle_ram(self.player, game, danger_fields)
        else:
            await self.send(text_data=json.dumps({'error': 'Invalid action'}))
            return
        
        game_ended = await self.game_end_check(game)

        
        state = await self.serialize_game(game)
        state['game_ended'] = game_ended
        state['crashed'] = crashed
        state['danger_fields'] = game.danger_fields

        if game_ended:
            state['winner_id'] = game.winner_id
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'game_state',
                'state': state,
                'game_ended': game_ended
            }
        )

    async def game_state(self, event):
        game = await self.get_game(self.game_id)
        if not game:
            await self.close()
            return

        event['state']['can_ram'] = await can_ram(self.player, game)
        await self.send(text_data=json.dumps(event['state']))

    

    @database_sync_to_async
    def get_player(self, user, game_id):
        try:
            return Player.objects.get(user=user, game_id=game_id)
        except Player.DoesNotExist:
            return None
        
    @database_sync_to_async
    def get_game(self, game_id):
        try:
            #get game model field named id where it is equal to funcarg game_id(e.g 7)
            return Game.objects.get(id=game_id)
        except Game.DoesNotExist:
            return None

    @database_sync_to_async
    def mark_player_connected(self, player):
        player.is_online = True
        player.last_seen = timezone.now()
        player.disconnected_at = None
        player.save()

    @database_sync_to_async
    def mark_player_disconnected(self, player):
        now = timezone.now()
        player.is_online = False
        player.last_seen = now
        player.disconnected_at = now
        player.save()

    @database_sync_to_async    #becasue of the wrapper the DB task get's sent to worker thread instead of main loop thread
    def save_game(self, game):
        game.save()
    
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
            if p.position >= game.track_length:
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
    
    @database_sync_to_async
    def call_advance_turn(self, game):
        game.advance_turn()



