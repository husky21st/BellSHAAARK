from copy import copy
import random
import torch
import numpy as np
from collections import OrderedDict

from rlcard.games.algoriuno.utils import ACTION_SPACE
from rlcard.games.algoriuno.encode import encode_hand, encode_hide_card, encode_target, encode_another_num_cards_left, encode_action_record, encode_another_skip_turn, encode_another_last_play_action

class Agent(object):
    def __init__(self):
        self.WILD = ['r-wild', 'g-wild', 'b-wild', 'y-wild']
        self.WILD_DRAW_4 = ['r-wild_draw_4', 'g-wild_draw_4', 'b-wild_draw_4', 'y-wild_draw_4']
        self.WILD_OTHERS = ['w-white_wild', 'w-shuffle_wild']
        self.SKIP = ['r-skip', 'g-skip', 'b-skip', 'y-skip']
        self.REVERSE = ['r-reverse', 'g-reverse', 'b-reverse', 'y-reverse']
        self.DRAW_2 = ['r-draw_2', 'g-draw_2', 'b-draw_2', 'y-draw_2']
        self.wild_trait = ['wild', 'wild_draw_4', 'white_wild', 'shuffle_wild']
        self.symbol_trait = ['skip', 'reverse', 'draw_2']
        self.number_trait = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        self.trait_point = {'0': 4.1, '1': 8.1, '2': 8.1, '3': 8.1, '4': 8.1, '5': 8.1, '6': 8.1, '7': 8.1, '8': 8.1, '9': 8.1, 'skip': 8, 'reverse': 8, 'draw_2': 8, 'wild': 4, 'wild_draw_4': 4, 'white_wild': 3, 'shuffle_wild': 1}

        self.my_id = None
        self.num_players = 4
        self.send_wild_color = None
        self.current_player = None
        self.hand = []
        self.target = None
        self.played_cards = []
        self.direction = 1
        self.skip_turn = [0 for _ in range(4)]
        self.num_cards = [0 for _ in range(4)]
        self.play_type = 0
        self.player_ids = {}
        self.last_receive_cards = None
        self.action_recorder = []
        self.all_last_action = [None for _ in range(4)]

        self.chicken_trig = True
        self.agents = [0 for _ in range(4)]
        self.agents[0] = torch.load('weights/0_1467523200.pth', map_location='cpu')
        self.agents[1] = torch.load('weights/1_1467523200.pth', map_location='cpu')
        self.agents[2] = torch.load('weights/2_1467523200.pth', map_location='cpu')
        self.agents[3] = torch.load('weights/3_1467523200.pth', map_location='cpu')
        for agent in self.agents:
            agent.set_device('cpu')

    def reset(self):
        self.send_wild_color = None
        self.current_player = None
        self.hand = []
        self.target = None
        self.played_cards = []
        self.direction = 1
        self.skip_turn = [0 for _ in range(4)]
        self.num_cards = [0 for _ in range(4)]
        self.play_type = 0
        self.player_ids = {}
        self.last_receive_cards = None
        self.chicken_trig = True
        self.action_recorder = []
        self.all_last_action = [None for _ in range(4)]

    def set_id(self, my_id):
        self.my_id = my_id

    def set_target(self, target):
        self.target = target

    def update_target(self, color):
        c = color[0]
        trait = self.make_info(self.target)[1]
        self.target = c + '-' + trait

    def set_hand(self, hand):
        self.hand = hand

    def set_max_color(self):
        self.send_wild_color = self.max_color(self.hand, self.played_cards)

    def set_player(self, play_order):
        for i, _id in enumerate(play_order):
            self.player_ids[_id] = i
            if _id == self.my_id:
                self.current_player = i

    def add_play_card(self, card):
        trait = self.make_info(card)[1]
        if trait in self.wild_trait:
            card = 'w-' + trait
        self.played_cards.append(card)

    def set_skip_turn(self, ww_player_id):
        ww_player = self.player_ids[ww_player_id]
        next_id = (ww_player + self.direction) % 4
        self.skip_turn[next_id] = 2

    def get_my_skip_turn(self):
        return self.skip_turn[self.current_player]

    def decrease_skip_turn(self, player_id):
        t_player = self.player_ids[player_id]
        if self.skip_turn[t_player] > 0:
            self.skip_turn[t_player] -= 1

    def set_num_cards(self, num_card_of_player):
        if num_card_of_player is not None:
            for _id, num in num_card_of_player.items():
                self.num_cards[self.player_ids[_id]] = num

    def decrease_num_cards(self, player_id):
        if player_id is not None and self.num_cards[self.player_ids[player_id]] >= 1:
            self.num_cards[self.player_ids[player_id]] -= 1

    def get_num_cards(self, player_id):
        return self.num_cards[self.player_ids[player_id]]

    def action(self):
        _a = self.play_action()
        self.send_wild_color = self.make_info(_a)[0]
        return _a

    def play_action(self):
        legal_actions = self.get_legal_actions()
        hand = self.hand
        target = self.target
        played_cards = self.played_cards
        legal_actions_info_list = self.make_list_info(legal_actions)
        hand_info_list = self.make_list_info(hand)
        target_info = self.make_info(target)
        current_player = self.current_player
        opposite_player = (current_player + 2) % 4
        num_cards = self.num_cards
        min_card_num = min(num_cards)
        skip_turn = self.skip_turn
        direction = self.direction
        card_and_skips = []
        my_card_and_skips = None
        for i in range(4):
            if i == current_player:
                my_card_and_skips = num_cards[i] + skip_turn[i]
                card_and_skips.append(100*my_card_and_skips)
            else:
                card_and_skips.append(num_cards[i] + skip_turn[i])
        min_card_and_skips = min(card_and_skips)
        is_my_card_num_min = False if min_card_and_skips <= my_card_and_skips else True
        next_card_num, prev_card_num = self.both_side_card_num(current_player, direction, num_cards)
        opposite_card_num = num_cards[opposite_player]
        legal_number_actions, legal_symbol_actions, legal_wild_actions = self.action_check(legal_actions)
        hand_number_num, hand_symbol_num, hand_wild_num = self.number_check(hand)
        open_color, open_trait = self.open_count(hand, played_cards)
        hand_trait = [c[1] for c in hand_info_list]
        legal_actions_trait = [a[1] for a in legal_actions_info_list]
        have_wilds = self.check_have_wilds(hand)  # 'shuffle_wild', 'wild', 'white_wild',  'wild_draw_4'
        action = None
        row_state = dict()
        # hand ['y-reverse', 'g-5', 'g-0', 'y-3', 'g-skip', 'b-8']
        # target r-draw_2
        # played_cards ['r-9', 'r-reverse', 'r-skip', 'r-5', 'r-3', 'r-5', 'r-reverse', 'r-draw_2']
        # legal_actions ['draw']
        # all_last_action ['r-3', 'r-5', 'r-reverse', 'r-draw_2']
        # direction 1
        # play_type 0
        # num_cards [7, 6, 6, 4]
        # skip_turn [0, 0, 0, 0]
        # num_players 4
        # current_player 1
        row_state['hand'] = self.hand
        row_state['target'] = self.target
        row_state['played_cards'] = self.played_cards
        row_state['legal_actions'] = legal_actions
        row_state['all_last_action'] = self.all_last_action
        row_state['direction'] = self.direction
        row_state['play_type'] = self.play_type
        row_state['num_cards'] = self.num_cards
        row_state['skip_turn'] = self.skip_turn
        row_state['num_players'] = self.num_players
        row_state['current_player'] = self.current_player
        state = self._extract_state(row_state)

        action, _ = self.agents[self.current_player].eval_step(state)
        print(action)

        if action is not None and action in legal_actions:
            return action
        else:
            return random.choice(legal_actions)

    def pprint(self):
        print('MODEL DATA')
        print(self.send_wild_color)
        print(self.current_player)
        print(self.hand)
        print(self.target)
        print(self.played_cards)
        print(self.direction)
        print(self.skip_turn)
        print(self.num_cards)
        print(self.play_type)
        print(self.player_ids)
        print(self.last_receive_cards)
        print(self.get_legal_actions())

    def number_check(self, cards):
        number = 0
        symbol = 0
        wild = 0
        for card in cards:
            card_info = card.split('-')
            if card_info[1] in self.number_trait:
                number += 1
            elif card_info[1] in self.symbol_trait:
                symbol += 1
            else:
                wild += 1
        return number, symbol, wild

    def action_check(self, actions):
        number_actions = []
        symbol_actions = []
        wild_actions = []
        for a in actions:
            if a == 'draw' or a == 'pass':
                continue
            a_info = self.make_info(a)
            if a_info[1] in self.number_trait:
                number_actions .append(a)
            elif a_info[1] in self.symbol_trait:
                symbol_actions.append(a)
            else:
                wild_actions.append(a)
        return number_actions, symbol_actions, wild_actions

    def both_side_card_num(self, player_id, direction, num_cards):
        next_id = (player_id + direction) % 4
        prev_id = (player_id - direction) % 4
        return num_cards[next_id], num_cards[prev_id]

    def make_info(self, card):
        return card.split('-')

    def make_list_info(self, cards):
        hand_info = []
        for card in cards:
            if card == 'draw' or card == 'pass':
                continue
            hand_info.append(self.make_info(card))
        return hand_info

    def max_color(self, hands, played_cards):
        color_nums = {'r': 0.04, 'g': 0.03, 'b': 0.02, 'y': 0.01, 'w': -999999}
        for card in hands:
            color = self.make_info(card)[0]
            color_nums[color] += 1000
        for card in played_cards:
            card_info = self.make_info(card)
            if card_info[1] in self.wild_trait[2:]:
                continue
            color_nums[card_info[0]] += 0.1
        return max(color_nums, key=color_nums.get)

    def action_wild(self, action_trait, hand, played_cards):
        if action_trait == self.wild_trait[0]:
            action = self.max_color(hand, played_cards) + '-' + self.wild_trait[0]
        elif action_trait == self.wild_trait[1]:
            action = self.max_color(hand, played_cards) + '-' + self.wild_trait[1]
        elif action_trait == self.wild_trait[2]:
            action = 'w-white_wild'
        else:
            action = 'w-shuffle_wild'
        return action

    def open_count(self, hand, played_cards):
        open_color = {'r': 0, 'g': 0, 'b': 0, 'y': 0, 'w': 0}
        open_trait = {'0': 0, '1': 0, '2': 0, '3': 0, '4': 0, '5': 0, '6': 0, '7': 0, '8': 0, '9': 0, 'skip': 0, 'reverse': 0, 'draw_2': 0, 'wild': 0, 'wild_draw_4': 0, 'white_wild': 0, 'shuffle_wild': 0}
        for card in hand:
            card_info = self.make_info(card)
            open_color[card_info[0]] += 1
            open_trait[card_info[1]] += 1
        for card in played_cards:
            card_info = self.make_info(card)
            if card_info[1] in self.wild_trait:
                open_color['w'] += 1
                open_trait[card_info[1]] += 1
            else:
                open_color[card_info[0]] += 1
                open_trait[card_info[1]] += 1
        return open_color, open_trait

    def check_have_wilds(self, hand):
        have_wilds = {'wild': False, 'wild_draw_4': False, 'white_wild': False, 'shuffle_wild': False}
        for card in hand:
            trait = self.make_info(card)[1]
            if trait in self.wild_trait:
                have_wilds[trait] = True
        return have_wilds

    def point_actions(self, actions, open_color, open_trait):
        # not wild
        action_point = {}
        for a in actions:
            a_info = self.make_info(a)
            color_point = 24 - open_color[a_info[0]]
            trait_point = self.trait_point[a_info[1]] - open_trait[a_info[1]]
            action_point[a] = color_point + trait_point
        return sorted(action_point.items(), key=lambda x: x[1])

    def symbol_action(self, symbol, legal_symbol_actions, open_color):
        can_action_list = []
        open_color = copy(open_color)
        if symbol == 'reverse':
            for a in legal_symbol_actions:
                if a in self.REVERSE:
                    can_action_list.append(a)
        elif symbol == 'skip':
            for a in legal_symbol_actions:
                if a in self.SKIP:
                    can_action_list.append(a)
        else:
            for a in legal_symbol_actions:
                if a in self.DRAW_2:
                    can_action_list.append(a)
        color_point = sorted(open_color.items(), key=lambda x: x[1], reverse=True)
        for c, _ in color_point:
            for _a in can_action_list:
                a_color = self.make_info(_a)[0]
                if c == a_color:
                    return _a
        return None

    def get_legal_actions(self):
        if self.play_type == 0:
            return self.normal_legal_actions()
        else:
            return self.draw_legal_actions(self.last_receive_cards[0])

    def normal_legal_actions(self):
        wild_flag = True
        wild_draw_4_flag = True
        white_wild_flag = True
        legal_actions = []
        wild_4_actions = []
        target_info = self.make_info(self.target)
        target_type = True if target_info[1] in self.wild_trait else False
        if target_type:
            for card in self.hand:
                card_info = self.make_info(card)
                card_type = True if card_info[1] in self.wild_trait else False
                if card_type:
                    if card_info[1] == 'wild_draw_4':
                        if wild_draw_4_flag:
                            wild_draw_4_flag = False
                            wild_4_actions.extend(self.WILD_DRAW_4)
                    elif card_info[1] == 'wild':
                        if wild_flag:
                            wild_flag = False
                            legal_actions.extend(self.WILD)
                    elif card_info[1] == 'white_wild':
                        if white_wild_flag:
                            white_wild_flag = False
                            legal_actions.append('w-white_wild')
                    elif card_info[1] == 'shuffle_wild':
                        legal_actions.append('w-shuffle_wild')
                elif card_info[0] == target_info[0]:
                    legal_actions.append(card)
        # target is action card or number card
        else:
            for card in self.hand:
                card_info = self.make_info(card)
                card_type = True if card_info[1] in self.wild_trait else False
                if card_type:
                    if card_info[1] == 'wild_draw_4':
                        if wild_draw_4_flag:
                            wild_draw_4_flag = False
                            wild_4_actions.extend(self.WILD_DRAW_4)
                    elif card_info[1] == 'wild':
                        if wild_flag:
                            wild_flag = False
                            legal_actions.extend(self.WILD)
                    elif card_info[1] == 'white_wild':
                        if white_wild_flag:
                            white_wild_flag = False
                            legal_actions.append('w-white_wild')
                    elif card_info[1] == 'shuffle_wild':
                        legal_actions.append('w-shuffle_wild')
                elif card_info[0] == target_info[0] or card_info[1] == target_info[1]:
                    legal_actions.append(card)
        if not legal_actions:
            legal_actions = wild_4_actions
        if len(self.hand) == 1 and legal_actions:
            return legal_actions
        unique_legal_actions = list(set(legal_actions))
        unique_legal_actions.append('draw')
        return unique_legal_actions

    def draw_legal_actions(self, draw_card):
        legal_actions = ['pass']
        target_info = self.make_info(self.target)
        draw_card_info = self.make_info(draw_card)
        draw_card_type = True if draw_card[1] in self.wild_trait else False
        if draw_card_type:
            if draw_card_info[1] == 'wild_draw_4':
                legal_actions.extend(self.WILD_DRAW_4)
            elif draw_card_info[1] == 'wild':
                legal_actions.extend(self.WILD)
            elif draw_card_info[1] == 'white_wild':
                legal_actions.append('w-white_wild')
            elif draw_card_info[1] == 'shuffle_wild':
                legal_actions.append('w-shuffle_wild')
        elif draw_card_info[0] == target_info[0] or draw_card_info[1] == target_info[1]:
            draw_card_type = True if draw_card[1] in self.symbol_trait else False
            if draw_card_type:
                legal_actions.append(draw_card)
            else:
                return [draw_card]
        return legal_actions

    def _get_legal_actions(self):
        legal_actions = self.get_legal_actions()
        legal_ids = {}
        for action in legal_actions:
            plane = np.zeros(64, dtype=np.int8)
            action_id = ACTION_SPACE[action]
            plane[action_id] = 1
            legal_ids[action_id] = plane

        return OrderedDict(legal_ids)

    def _extract_state(self, state):
        player_id = state['current_player']
        current_hand = encode_hand(state['hand'])
        hidden_cards = encode_hide_card(state['hand'] + state['played_cards'])
        target_card = encode_target(state['target'])
        another_last_play_card = encode_another_last_play_action(state['all_last_action'])
        another_num_cards_left = encode_another_num_cards_left(player_id, self.num_players, state['num_cards'])
        another_skip_turn = encode_another_skip_turn(player_id, self.num_players, state['skip_turn'])
        direction_vec = np.zeros(2, dtype=np.int8)
        if self.direction == 1:
            direction_vec[0] = 1
        else:
            direction_vec[1] = 1
        play_type_vsc = np.zeros(2, dtype=np.int8)
        play_type_vsc[state['play_type']] = 1
        obs = np.concatenate((current_hand, hidden_cards, target_card, another_num_cards_left, direction_vec, another_skip_turn, play_type_vsc, another_last_play_card))
        obs_history = encode_action_record(self.action_recorder)
        extracted_state = {'obs': obs, 'obs_history': obs_history, 'legal_actions': self._get_legal_actions(),
                           'raw_obs': state}
        return extracted_state


if __name__ == '__main__':
    a = Agent()
    a.play_action()
