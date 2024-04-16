import numpy as np
from copy import copy
from collections import OrderedDict


class UNOCustomAgentV1(object):

    def __init__(self):
        self.use_raw = True
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

    def step(self, state):
        raw_state = state['raw_obs']
        legal_actions = raw_state['legal_actions']
        if len(legal_actions) == 1:
            # win card or draw or play number card then draw or pass
            return legal_actions[0]
        hand = raw_state['hand']
        target = raw_state['target']
        played_cards = raw_state['played_cards']
        legal_actions_info_list = self.make_list_info(legal_actions)
        hand_info_list = self.make_list_info(hand)
        target_info = self.make_info(target)
        current_player = raw_state['current_player']
        num_cards = raw_state['num_cards']
        min_card_num = min(num_cards)
        skip_turn = raw_state['skip_turn']
        direction = raw_state['direction']
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
        legal_number_actions, legal_symbol_actions, legal_wild_actions = self.action_check(legal_actions)
        hand_number_num, hand_symbol_num, hand_wild_num = self.number_check(hand)
        open_color, open_trait = self.open_count(hand, played_cards)
        hand_trait = [c[1] for c in hand_info_list]
        legal_actions_trait = [a[1] for a in legal_actions_info_list]
        have_wilds = self.check_have_wilds(hand)  # 'shuffle_wild', 'wild', 'white_wild',  'wild_draw_4'
        action = None
        if raw_state['play_type'] == 0:
            # play_type is 0
            if len(hand) == 1:
                # wild card
                action = legal_actions[0]
            else:
                uni_legal_actions = legal_actions[:-1]
                if len(uni_legal_actions) == 1:
                    action_info = self.make_info(uni_legal_actions[0])
                    if action_info[1] in self.symbol_trait:
                        # action card
                        if action_info[1] == self.symbol_trait[1]:
                            # reverse
                            if min_card_and_skips <= 2 or next_card_num < prev_card_num - 1:
                                action = uni_legal_actions[0]
                            elif min_card_and_skips <= hand_symbol_num + hand_wild_num + 1 and next_card_num <= prev_card_num:
                                action = uni_legal_actions[0]
                            else:
                                action = 'draw'
                        else:
                            # skip, draw_2
                            action = uni_legal_actions[0]
                    else:
                        # number card
                        action = uni_legal_actions[0]
                else:
                    if have_wilds['shuffle_wild']:
                        if min_card_and_skips <= 2 or hand_wild_num <= 1:
                            action = self.action_wild('shuffle_wild', hand, played_cards)
                            return action
                    if have_wilds['wild']:
                        if min_card_and_skips <= 2 or min_card_and_skips <= hand_wild_num + 1:
                            action = self.action_wild('wild', hand, played_cards)
                            return action
                    if have_wilds['white_wild']:
                        if min_card_and_skips <= 2 or min_card_and_skips <= hand_wild_num + 1:
                            action = self.action_wild('white_wild', hand, played_cards)
                            return action
                    if have_wilds['wild_draw_4']:
                        if min_card_and_skips <= 2 or min_card_and_skips <= hand_wild_num:
                            action = self.action_wild('wild_draw_4', hand, played_cards)
                            return action
                    # if not legal_wild_actions:
                    if legal_number_actions or legal_symbol_actions:
                        if not legal_symbol_actions:
                            # number (and wild)
                            action_point = self.point_actions(legal_number_actions, open_color, open_trait)
                            action = action_point[0][0]
                        else:
                            if not legal_number_actions:
                                # symbol (and wild)
                                if 'skip' in legal_actions_trait and next_card_num == 1:
                                    action = self.symbol_action('skip', hand)
                                    return action
                                if 'draw_2' in legal_actions_trait and next_card_num == 1:
                                    action = self.symbol_action('draw_2', hand)
                                    return action
                                if 'reverse' in legal_actions_trait and next_card_num <= 4 and next_card_num < prev_card_num - 2:
                                    action = self.symbol_action('reverse', hand)
                                    return action
                                action_point = self.point_actions(legal_symbol_actions, open_color, open_trait)
                                min_action = action_point[0][0]
                                if min_action in self.REVERSE and len(legal_symbol_actions) >= 2:
                                    # reverse
                                    if action_point[0][1] <= action_point[1][1] - 8:
                                        action = min_action
                                    elif min_card_and_skips <= 2 or next_card_num < prev_card_num - 1:
                                        action = min_action
                                    elif min_card_and_skips <= 4 and min_card_and_skips <= hand_symbol_num + hand_wild_num + 1 and next_card_num <= prev_card_num:
                                        action = min_action
                                    else:
                                        action = action_point[1][0]
                                else:
                                    # skip, draw_2 or legal_symbol_actions num is 1
                                    action = min_action
                            else:
                                # number and symbol (and wild)
                                if 'skip' in legal_actions_trait and next_card_num == 1:
                                    action = self.symbol_action('skip', hand)
                                    return action
                                if 'draw_2' in legal_actions_trait and next_card_num == 1:
                                    action = self.symbol_action('draw_2', hand)
                                    return action
                                if 'reverse' in legal_actions_trait and next_card_num <= 4 and next_card_num < prev_card_num - 2:
                                    action = self.symbol_action('reverse', hand)
                                    return action
                                action_point = self.point_actions(legal_number_actions + legal_symbol_actions, open_color, open_trait)
                                min_action = action_point[0][0]
                                if min_action in self.REVERSE and len(legal_symbol_actions) >= 2:
                                    # reverse
                                    if action_point[0][1] <= action_point[1][1] - 8:
                                        action = min_action
                                    elif min_card_and_skips <= 2 or next_card_num < prev_card_num - 1:
                                        action = min_action
                                    elif min_card_and_skips <= hand_symbol_num + hand_wild_num + 1 and next_card_num <= prev_card_num:
                                        action = min_action
                                    else:
                                        action = action_point[1][0]
                                elif min_action in self.SKIP or min_action in self.DRAW_2:
                                    # skip, draw_2
                                    action = min_action
                                else:
                                    # number
                                    action = min_action
                    else:
                        # wild only
                        action = 'draw'
                    # else:
                    #
                    #     if not legal_symbol_actions:
                    #         if not legal_number_actions:
                    #             # wild only
                    #             pass
                    #         else:
                    #             # number and wild
                    #             pass
                    #         pass
                    #     else:
                    #         if not legal_number_actions:
                    #             # symbol and wild
                    #             pass
                    #         else:
                    #             # number and symbol and wild
                    #             pass
        else:
            # play_type is 1
            draw_card_info = self.make_info(hand[-1])
            if draw_card_info[1] in self.wild_trait:
                # wild card
                if min_card_and_skips <= hand_wild_num + 1:
                    action = self.action_wild(draw_card_info[1], hand, played_cards)
                else:
                    action = 'pass'
            else:
                # action card
                if draw_card_info[1] == 'reverse':
                    # reverse
                    if min_card_and_skips <= 2 or next_card_num < prev_card_num - 1:
                        action = legal_actions[1]
                    elif min_card_and_skips <= hand_symbol_num + hand_wild_num + 1 and next_card_num <= prev_card_num:
                        action = legal_actions[1]
                    else:
                        action = 'pass'
                else:
                    # skip, draw_2
                    action = legal_actions[1]

        if action is not None and action in legal_actions:
            return action
        else:
            return None

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

    def eval_step(self, state):
        return self.step(state), []

    def share_memory(self):
        pass

    def eval(self):
        pass

    def parameters(self):
        return None

    def load_state_dict(self, state_dict):
        return None

    def state_dict(self):
        return None

    def set_device(self, device):
        pass

    @staticmethod
    def filter_wild(hand):
        ''' Filter the wild cards. If all are wild cards, we do not filter

        Args:
            hand (list): A list of UNO card string

        Returns:
            filtered_hand (list): A filtered list of UNO string
        '''
        filtered_hand = []
        for card in hand:
            if not card[2:6] == 'wild':
                filtered_hand.append(card)

        if len(filtered_hand) == 0:
            filtered_hand = hand

        return filtered_hand

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

    @staticmethod
    def count_colors(hand):
        color_nums = {'r': 0, 'g': 0, 'b': 0, 'y': 0, 'w': 0}
        for card in hand:
            color = card[0]
            color_nums[color] += 1
        return color_nums

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

    def symbol_action(self, symbol, hand):
        if symbol == 'reverse':
            for card in hand:
                if card in self.REVERSE:
                    return card
        elif symbol == 'skip':
            for card in hand:
                if card in self.SKIP:
                    return card
        else:
            for card in hand:
                if card in self.DRAW_2:
                    return card
        return None
