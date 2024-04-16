''' UNO rule models
'''

import numpy as np

import rlcard
from rlcard.models.model import Model


class UNORuleAgentV1(object):
    ''' UNO Rule agent version 1
    '''

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
        self.trait_point = {'0': 4, '1': 8, '2': 8, '3': 8, '4': 8, '5': 8, '6': 8, '7': 8, '8': 8, '9': 8, 'skip': 8,
                            'reverse': 8, 'draw_2': 8, 'wild': 4, 'wild_draw_4': 4, 'white_wild': 3, 'shuffle_wild': 1}

    def step(self, state):
        raw_state = state['raw_obs']
        legal_actions = raw_state['legal_actions']
        if len(legal_actions) == 1:
            return legal_actions[0]
        hand = raw_state['hand']
        legal_number_actions, legal_symbol_actions, legal_wild_actions = self.action_check(legal_actions)
        have_color_nums = {'r': 0, 'g': 0, 'b': 0, 'y': 0}
        for card in hand:
            color = self.make_info(card)[0]
            if color == 'w':
                continue
            have_color_nums[color] += 1
        have_color_nums = sorted(have_color_nums.items(), key=lambda x: x[1], reverse=True)
        have_wilds = self.check_have_wilds(hand)
        if raw_state['play_type'] == 0:
            uni_legal_actions = legal_actions[:-1]
            if not legal_wild_actions:
                if not legal_symbol_actions:
                    # number only
                    for c, _ in have_color_nums:
                        for a in legal_number_actions:
                            color = self.make_info(a)[0]
                            if c == color:
                                return a
                    return None
                else:
                    # number and symbol
                    for c, _ in have_color_nums:
                        for a in legal_symbol_actions:
                            color = self.make_info(a)[0]
                            if c == color:
                                return a
                    return None
            else:
                # wild True
                if have_wilds['wild_draw_4']:
                    color_nums = self.count_colors(self.filter_wild(hand))
                    action = max(color_nums, key=color_nums.get) + '-wild_draw_4'
                    return action
                if have_wilds['wild']:
                    color_nums = self.count_colors(self.filter_wild(hand))
                    action = max(color_nums, key=color_nums.get) + '-wild'
                    return action
                if have_wilds['shuffle_wild']:
                    return 'w-shuffle_wild'
                if have_wilds['white_wild']:
                    return 'w-white_wild'

        else:
            uni_legal_actions = legal_actions[1:]
            if len(uni_legal_actions) == 1:
                return uni_legal_actions[0]
            else:
                for action in uni_legal_actions:
                    if action.split('-')[1] == 'wild_draw_4':
                        color_nums = self.count_colors(self.filter_wild(hand))
                        action = max(color_nums, key=color_nums.get) + '-wild_draw_4'
                        return action
                    if action.split('-')[1] == 'wild':
                        color_nums = self.count_colors(self.filter_wild(hand))
                        action = max(color_nums, key=color_nums.get) + '-wild'
                        return action
                    else:
                        return action
        return None

    def check_have_wilds(self, hand):
        have_wilds = {'wild': False, 'wild_draw_4': False, 'white_wild': False, 'shuffle_wild': False}
        for card in hand:
            card_info = card.split('-')
            if card_info[1] in self.wild_trait:
                have_wilds[card_info[1]] = True
        return have_wilds

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

    def max_color(self, hands, played_cards):
        color_nums = {'r': 0.4, 'g': 0.3, 'b': 0.2, 'y': 0.1, 'w': -99999}
        for card in hands:
            color = self.make_info(card)[0]
            color_nums[color] += 100
        for card in played_cards:
            card_info = self.make_info(card)
            if card_info[1] in self.wild_trait[2:]:
                continue
            color_nums[card_info[0]] += 1
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

    def make_info(self, card):
        return card.split('-')

    def eval_step(self, state):
        ''' Step for evaluation. The same to step
        '''
        return self.step(state), []

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

    @staticmethod
    def count_colors(hand):
        color_nums = {'r': 0, 'g': 0, 'b': 0, 'y': 0, 'w': -99999}
        for card in hand:
            color = card[0]
            color_nums[color] += 1

        return color_nums


class UNORuleModelV1(Model):
    ''' UNO Rule Model version 1
    '''

    def __init__(self):
        ''' Load pretrained model
        '''
        env = rlcard.make('uno')

        rule_agent = UNORuleAgentV1()
        self.rule_agents = [rule_agent for _ in range(env.num_players)]

    @property
    def agents(self):
        ''' Get a list of agents for each position in a the game

        Returns:
            agents (list): A list of agents

        Note: Each agent should be just like RL agent with step and eval_step
              functioning well.
        '''
        return self.rule_agents

    @property
    def use_raw(self):
        ''' Indicate whether use raw state and action

        Returns:
            use_raw (boolean): True if using raw state and action
        '''
        return True



