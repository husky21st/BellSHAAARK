import numpy as np

from rlcard.games.algoriuno import Dealer
from rlcard.games.algoriuno import Player
from rlcard.games.algoriuno import Round

isTest = False


class UnoGame:

    def __init__(self, allow_step_back=False, num_players=4):
        self.dealer = None
        self.players = None
        self.round = None
        self.allow_step_back = allow_step_back
        self.np_random = np.random.RandomState()
        self.num_players = num_players
        self.payoffs = [0 for _ in range(self.num_players)]

    def configure(self, game_config):
        ''' Specifiy some game specific parameters, such as number of players
        '''
        self.num_players = game_config['game_num_players']

    def init_game(self, action_recorder):
        ''' Initialize players and state

        Returns:
            (tuple): Tuple containing:

                (dict): The first state in one game
                (int): Current player's id
        '''
        # Initialize payoffs
        self.payoffs = [0 for _ in range(self.num_players)]

        # Initialize a dealer that can deal cards
        self.dealer = Dealer(self.np_random)

        # Initialize four players to play the game
        self.players = [Player(i, self.np_random) for i in range(self.num_players)]

        # Deal 7 cards to each player to prepare for the game
        for player in self.players:
            for _ in range(7):
                self.dealer.deal_cards(player)

        # Initialize a Round
        self.round = Round(self.dealer, self.num_players, self.np_random)

        # flip and perform top card
        top_card = self.round.flip_top_card(self.players[0].hand)
        self.round.perform_top_card(self.players, top_card)

        action_recorder.append((-1, top_card.str))

        player_id = self.round.current_player
        state = self.get_state(player_id)
        return state, player_id

    def step(self, action, action_recorder):
        action_player = self.round.current_player
        shuffle_check = self.round.proceed_round(self.players, action)
        if shuffle_check is not None:
            action = shuffle_check
        action_recorder.append((action_player, action))

        # if len(action_recorder) >= 4096:
        #     self.round.is_over = True
        #     print('FORCE STOP')

        player_id = self.round.current_player
        state = self.get_state(player_id)
        return state, player_id

    # def step_back(self):
    #     # ''' Return to the previous state of the game
    #     #
    #     # Returns:
    #     #     (bool): True if the game steps back successfully
    #     # '''
    #     # if not self.history:
    #     #     return False
    #     # self.dealer, self.players, self.round = self.history.pop()
    #     # return True
    #     return True

    def get_state(self, player_id):
        state = self.round.get_state(self.players, player_id)
        state['num_players'] = self.get_num_players()
        state['current_player'] = self.round.current_player
        return state

    def calculate_point(self, player_id):
        point = 0
        if not self.players[player_id].hand:
            return 0
        for card in self.players[player_id].hand:
            if card.type == 'wild':
                if card.trait == 'white_wild' or card.trait == 'shuffle_wild':
                    point -= 40
                else:
                    point -= 50
            elif card.type == 'action':
                point -= 20
            elif card.type == 'number':
                point -= int(card.trait)
        return point

    def get_payoffs(self):
        if self.round.winner is not None:
            winner_point = 0
            for p in range(self.num_players):
                self.payoffs[p] = self.calculate_point(p)
                winner_point -= self.payoffs[p]
            self.payoffs[self.round.winner] = winner_point
        else:
            print('WINNER NOT FOUND')
            for p in range(self.num_players):
                self.payoffs[p] = self.calculate_point(p)
            print(f'PAYOFF : {[p for p in self.payoffs]}')
        return self.payoffs

    def get_legal_actions(self):
        return self.round.get_legal_actions(self.players, self.round.current_player)

    def get_num_players(self):
        ''' Return the number of players in Limit Texas Hold'em

        Returns:
            (int): The number of players in the game
        '''
        return self.num_players

    @staticmethod
    def get_num_actions():
        ''' Return the number of applicable actions

        Returns:
            (int): The number of actions. There are 61 actions
        '''
        return 64

    def get_player_id(self):
        ''' Return the current player's id

        Returns:
            (int): current player's id
        '''
        return self.round.current_player

    def is_over(self):
        ''' Check if the game is over

        Returns:
            (boolean): True if the game is over
        '''
        return self.round.is_over
