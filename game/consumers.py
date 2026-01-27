from channels.generic.websocket import WebsocketConsumer
import json
from .models import Player, Game
from django.shortcuts import get_object_or_404

class GameConsumer(WebsocketConsumer):
    def connect(self):
        user = self.scope['user']
        if not user.is_authenticated:
            self.close()
            return
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.player = get_object_or_404(Player, user=user, game_id=self.game_id)
        self.accept()

    def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if action == 'accelerate':
            self.handle_accelerate()

    def handle_accelerate(self):
        player = self.player
        player.speed += 1
        player.position += player.speed
        if player.position > 100:
            player.position = 100

        player.save()

        self.send(text_data=json.dumps({
            'type': 'state',
            'position': player.position,
            'speed': player.speed,
        }))

    