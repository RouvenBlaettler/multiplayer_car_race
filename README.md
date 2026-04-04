
# Multiplayer Car Race

Turn-based, two-player racing game built with Django and Channels. Each player chooses an action each turn, manages speed and risk, and races to the finish while trying to outplay the opponent.

## Highlights

- Real-time multiplayer with WebSockets (Django Channels)
- Turn-based game loop and state synchronization
- Action system: accelerate, brake, nitro, ram
- Crash risk system with per-game danger zones
- Dynamic UI updates for player stats and actions

## Tech Stack

- Django + Django Channels + Daphne
- SQLite (dev database)
- HTML/CSS/JavaScript

## How to Run

1. Create and activate a virtual environment.
2. Install dependencies.
3. Run migrations.
4. Start the server.

Example commands:

		pip install -r requirements.txt
		python manage.py migrate
		python manage.py runserver

If you are using a virtual environment, activate it before installing dependencies. The project uses SQLite for local development, so no separate database server is required.

Open the app in your browser and create/join a game.

## Gameplay Summary

- Each turn, the current player selects an action.
- Actions affect position, speed, and risk:
	- Accelerate: increase speed and move farther
	- Brake: reduce speed and avoid crash risk
	- Nitro: big position boost (limited uses)
	- Ram: damage opponent if in range
- Crash chance increases when crossing danger zones.

## Notes

- Game IDs auto-increment and are expected to grow.
- Danger zones are generated per game and stored on the `Game` model.

