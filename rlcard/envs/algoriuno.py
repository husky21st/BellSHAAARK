import numpy as np
from collections import OrderedDict

from rlcard.envs import Env
from rlcard.games.algoriuno import Game
from rlcard.games.algoriuno.utils import ACTION_SPACE, ACTION_LIST
from rlcard.games.algoriuno.encode import encode_hand, encode_hide_card, encode_target, encode_another_num_cards_left, encode_action_record, encode_another_skip_turn, encode_another_last_play_action


class UnoEnv(Env):

    def __init__(self, config):
        print('!ALGORI UNO playing!')
        self.name = 'uno'
        self.default_game_config = {'game_num_players': 4}
        self.game = Game()
        super().__init__(config)
        self.state_shape = [[603] for _ in range(self.num_players)]
        self.action_shape = [[64] for _ in range(self.num_players)]

    def _extract_state(self, state):
        player_id = state['current_player']
        # player_id_vec = np.zeros(4, dtype=np.int8)
        # player_id_vec[player_id] = 1
        current_hand = encode_hand(state['hand'])
        # print(state['hand'])
        # print(state['played_cards'])
        # print(self.action_recorder)
        # print(state['all_last_action'])
        hidden_cards = encode_hide_card(state['hand'] + state['played_cards'])
        target_card = encode_target(state['target'])
        another_last_play_card = encode_another_last_play_action(state['all_last_action'])
        another_num_cards_left = encode_another_num_cards_left(player_id, self.num_players, state['num_cards'])
        another_skip_turn = encode_another_skip_turn(player_id, self.num_players, state['skip_turn'])
        direction_vec = np.zeros(2, dtype=np.int8)
        if self.game.round.direction == 1:
            direction_vec[0] = 1
        else:
            direction_vec[1] = 1
        play_type_vsc = np.zeros(2, dtype=np.int8)
        play_type_vsc[state['play_type']] = 1
        obs = np.concatenate((current_hand, hidden_cards, target_card, another_num_cards_left, direction_vec, another_skip_turn, play_type_vsc, another_last_play_card))
        obs_history = encode_action_record(self.action_recorder)
        # extracted_state = {'obs': obs, 'obs_history': obs_history, 'legal_actions': self._get_legal_actions(), 'raw_obs': state,
        #                    'raw_legal_actions': [a for a in state['legal_actions']],
        #                    'action_record': self.action_recorder}
        extracted_state = {'obs': obs, 'obs_history': obs_history, 'legal_actions': self._get_legal_actions(),
                           'raw_obs': state}
        return extracted_state

    def get_payoffs(self):
        return np.array(self.game.get_payoffs())

    def _decode_action(self, action_id):
        return ACTION_LIST[action_id]
        # legal_ids = self._get_legal_actions()
        # if action_id in legal_ids:
        #     return ACTION_LIST[action_id]
        # print('ILLEGAL ACTION ERROR')
        # return None
        # return ACTION_LIST[np.random.choice(legal_ids)]

    def _get_legal_actions(self):
        legal_actions = self.game.get_legal_actions()
        legal_ids = {}
        for action in legal_actions:
            plane = np.zeros(64, dtype=np.int8)
            action_id = ACTION_SPACE[action]
            plane[action_id] = 1
            legal_ids[action_id] = plane
        # def make_action_array(action_id):
        #     plane = np.zeros(64, dtype=np.int8)
        #     plane[action_id] = 1
        #     return plane
        # legal_ids = {ACTION_SPACE[action]: make_action_array(action) for action in legal_actions}
        return OrderedDict(legal_ids)

    # def get_perfect_information(self):
    #     ''' Get the perfect information of the current state
    #
    #     Returns:
    #         (dict): A dictionary of all the perfect information of the current state
    #     '''
    #     state = {}
    #     state['num_players'] = self.num_players
    #     state['hand_cards'] = [cards2list(player.hand)
    #                            for player in self.game.players]
    #     state['played_cards'] = cards2list(self.game.round.played_cards)
    #     state['target'] = self.game.round.target.str
    #     state['current_player'] = self.game.round.current_player
    #     state['legal_actions'] = self.game.round.get_legal_actions(
    #         self.game.players, state['current_player'])
    #     return state

