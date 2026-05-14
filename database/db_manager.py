# -*- coding: utf-8 -*-
# Façade conservée pour compatibilité — la logique est dans database/repositories/.
from database.connection import Database
from database.repositories.game_repository import GameRepository
from database.repositories.turn_repository import TurnRepository


class DatabaseManager:
    def __init__(self, database_url):
        self._db        = Database(database_url)
        self._db.init()
        self._games     = GameRepository(self._db)
        self._turns     = TurnRepository(self._db)

    def create_game(self, player_name, player_type):
        return self._games.create(player_name, player_type)

    def update_game_winner(self, game_id, winner):
        self._games.update_winner(game_id, winner)

    def update_game_trust(self, game_id, trust_score):
        self._games.update_trust(game_id, trust_score)

    def update_game_trust_final(self, game_id, detected):
        self._games.update_trust_final(game_id, detected)

    def save_full_turn(self, game_id, turn_number, bot_quota, trust_score, bot_shots):
        return self._turns.save(game_id, turn_number, bot_quota, trust_score, bot_shots)

    def update_turn_trust(self, turn_id, trust_score):
        self._turns.update_trust(turn_id, trust_score)
