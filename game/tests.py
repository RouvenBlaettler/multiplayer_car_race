from unittest.mock import patch

from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from django.test import TestCase

from .game_service import (
    can_ram,
    crash,
    handle_accelerate,
    handle_brake,
    handle_nitro,
    handle_ram,
)
from .models import Game, Player

# The handlers are async (database_sync_to_async); async_to_sync lets us call them from a normal test.
accelerate = async_to_sync(handle_accelerate)
brake = async_to_sync(handle_brake)
nitro = async_to_sync(handle_nitro)
ram = async_to_sync(handle_ram)
check_can_ram = async_to_sync(can_ram)

# Patching random.randint makes crash outcomes deterministic.
NO_CRASH_ROLL = 100
CRASH_ROLL = 1


class GameTestBase(TestCase):
    def setUp(self):
        User = get_user_model()
        self.game = Game.objects.create(status='active', danger_fields=[])
        self.p1 = Player.objects.create(
            user=User.objects.create_user('alice', password='pw'), game=self.game, is_online=True
        )
        self.p2 = Player.objects.create(
            user=User.objects.create_user('bob', password='pw'), game=self.game, is_online=True
        )
        self.game.current_turn = self.p1
        self.game.save()


@patch('game.game_service.random.randint', return_value=NO_CRASH_ROLL)
class ActionTests(GameTestBase):
    def test_accelerate_increases_speed_then_moves(self, _):
        self.p1.speed = 2
        accelerate(self.p1, self.game, [])
        self.assertEqual(self.p1.speed, 3)
        self.assertEqual(self.p1.position, 3)

    def test_brake_reduces_speed(self, _):
        self.p1.speed = 3
        brake(self.p1, self.game)
        self.assertEqual(self.p1.speed, 2)
        self.assertEqual(self.p1.position, 2)

    def test_brake_never_goes_below_zero(self, _):
        self.p1.speed = 0
        brake(self.p1, self.game)
        self.assertEqual(self.p1.speed, 0)
        self.assertEqual(self.p1.position, 0)

    def test_nitro_boosts_and_uses_a_charge(self, _):
        nitro(self.p1, self.game, [])
        self.assertEqual(self.p1.position, 10)
        self.assertEqual(self.p1.nitro, 2)

    def test_nitro_without_charges_does_nothing(self, _):
        self.p1.nitro = 0
        nitro(self.p1, self.game, [])
        self.assertEqual(self.p1.position, 0)
        self.assertEqual(self.p1.nitro, 0)

    def test_ram_damages_opponent_in_range(self, _):
        self.p1.speed = 5
        self.p2.position = 3
        self.p2.save()
        self.assertTrue(check_can_ram(self.p1, self.game))
        ram(self.p1, self.game, [])
        self.p2.refresh_from_db()
        self.assertEqual(self.p2.hp, 80)

    def test_ram_misses_opponent_out_of_range(self, _):
        self.p1.speed = 2
        self.p2.position = 50
        self.p2.save()
        self.assertFalse(check_can_ram(self.p1, self.game))
        ram(self.p1, self.game, [])
        self.p2.refresh_from_db()
        self.assertEqual(self.p2.hp, 100)

    def test_action_passes_turn_to_opponent(self, _):
        brake(self.p1, self.game)
        self.assertEqual(self.game.current_turn, self.p2)


class CrashTests(GameTestBase):
    @patch('game.game_service.random.randint', return_value=CRASH_ROLL)
    def test_crash_in_danger_field_costs_hp(self, _):
        self.p1.position, self.p1.speed = 10, 5
        self.assertTrue(crash(self.p1, danger_fields=[12]))
        self.assertEqual(self.p1.hp, 60)

    @patch('game.game_service.random.randint', return_value=NO_CRASH_ROLL)
    def test_no_crash_on_high_roll(self, _):
        self.p1.position, self.p1.speed = 10, 5
        self.assertFalse(crash(self.p1, danger_fields=[12]))
        self.assertEqual(self.p1.hp, 100)


class TurnTests(GameTestBase):
    def test_turns_alternate(self):
        self.game.advance_turn()
        self.assertEqual(self.game.current_turn, self.p2)
        self.game.advance_turn()
        self.assertEqual(self.game.current_turn, self.p1)

    def test_offline_player_is_skipped(self):
        self.p2.is_online = False
        self.p2.save()
        self.game.advance_turn()
        self.assertEqual(self.game.current_turn, self.p1)

    def test_advancing_sets_turn_deadline(self):
        self.game.advance_turn()
        self.assertIsNotNone(self.game.turn_deadline)
