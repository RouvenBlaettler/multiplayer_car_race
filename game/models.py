from django.conf import settings
from django.db import models

class Game(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'Waiting'),
        ('active', 'Active'),
        ('finished', 'Finished'),
    ]

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='waiting') 
    track_length = models.PositiveIntegerField(default=100)  # in meters
    turn_number = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    current_turn = models.OneToOneField('Player', null=True, blank=True, on_delete=models.SET_NULL, related_name='current_turn_games')

    def __str__(self):
        return f'Game {self.id} - Status: {self.status}'

    def advance_turn(self):
        players = list(self.players.order_by('id'))
        if not players:
            self.current_turn = None
            return

        if not self.current_turn or self.current_turn not in players:
            self.current_turn = players[0]
            return

        current_index = players.index(self.current_turn)
        next_index = (current_index + 1) % len(players)
        self.current_turn = players[next_index]
    

class Player(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, related_name='players', on_delete=models.CASCADE)

    position = models.IntegerField(default=0)  # in meters
    speed = models.IntegerField(default=0)  # in meters per turn
    nitro = models.IntegerField(default=3)  # number of nitro boosts available
    hp = models.IntegerField(default=100)  # health points

    def __str__(self):
        return f'{self.user} in Game {self.game.id}'
    
class TurnAction(models.Model):
    ACTION_CHOICES = [
        ('accelerate', 'Accelerate'),
        ('brake', 'Brake'),
        ('nitro', 'Nitro'),
        ('ram', 'Ram'),
    ]

    player = models.ForeignKey(Player, related_name='actions', on_delete=models.CASCADE)
    turn_number = models.PositiveIntegerField()
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('player', 'turn_number')

    def __str__(self):
        return f'Action: {self.action} by {self.player} on Turn {self.turn_number}'