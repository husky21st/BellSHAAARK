import os
import json
from collections import OrderedDict
import rlcard
from rlcard.games.algoriuno.card import UnoCard as Card

# Read required docs
# ROOT_PATH = rlcard.__path__[0]

# a map of abstract action to its index and a list of abstract action
# with open(os.path.join(ROOT_PATH, 'games/algoriuno/jsondata/action_space.json'), 'r') as file:
#     ACTION_SPACE = json.load(file, object_pairs_hook=OrderedDict)
#     ACTION_LIST = list(ACTION_SPACE.keys())

ACTION_SPACE = {'r-0': 0, 'r-1': 1, 'r-2': 2, 'r-3': 3, 'r-4': 4, 'r-5': 5, 'r-6': 6, 'r-7': 7, 'r-8': 8, 'r-9': 9, 'r-skip': 10, 'r-reverse': 11, 'r-draw_2': 12, 'r-wild': 13, 'r-wild_draw_4': 14, 'g-0': 15, 'g-1': 16, 'g-2': 17, 'g-3': 18, 'g-4': 19, 'g-5': 20, 'g-6': 21, 'g-7': 22, 'g-8': 23, 'g-9': 24, 'g-skip': 25, 'g-reverse': 26, 'g-draw_2': 27, 'g-wild': 28, 'g-wild_draw_4': 29, 'b-0': 30, 'b-1': 31, 'b-2': 32, 'b-3': 33, 'b-4': 34, 'b-5': 35, 'b-6': 36, 'b-7': 37, 'b-8': 38, 'b-9': 39, 'b-skip': 40, 'b-reverse': 41, 'b-draw_2': 42, 'b-wild': 43, 'b-wild_draw_4': 44, 'y-0': 45, 'y-1': 46, 'y-2': 47, 'y-3': 48, 'y-4': 49, 'y-5': 50, 'y-6': 51, 'y-7': 52, 'y-8': 53, 'y-9': 54, 'y-skip': 55, 'y-reverse': 56, 'y-draw_2': 57, 'y-wild': 58, 'y-wild_draw_4': 59, 'w-white_wild': 60, 'w-shuffle_wild': 61, 'draw': 62, 'pass': 63}
ACTION_LIST = ['r-0', 'r-1', 'r-2', 'r-3', 'r-4', 'r-5', 'r-6', 'r-7', 'r-8', 'r-9', 'r-skip', 'r-reverse', 'r-draw_2', 'r-wild', 'r-wild_draw_4', 'g-0', 'g-1', 'g-2', 'g-3', 'g-4', 'g-5', 'g-6', 'g-7', 'g-8', 'g-9', 'g-skip', 'g-reverse', 'g-draw_2', 'g-wild', 'g-wild_draw_4', 'b-0', 'b-1', 'b-2', 'b-3', 'b-4', 'b-5', 'b-6', 'b-7', 'b-8', 'b-9', 'b-skip', 'b-reverse', 'b-draw_2', 'b-wild', 'b-wild_draw_4', 'y-0', 'y-1', 'y-2', 'y-3', 'y-4', 'y-5', 'y-6', 'y-7', 'y-8', 'y-9', 'y-skip', 'y-reverse', 'y-draw_2', 'y-wild', 'y-wild_draw_4', 'w-white_wild', 'w-shuffle_wild', 'draw', 'pass']

WILD = ['r-wild', 'g-wild', 'b-wild', 'y-wild']

WILD_DRAW_4 = ['r-wild_draw_4', 'g-wild_draw_4', 'b-wild_draw_4', 'y-wild_draw_4']

INFO = {'type': ['number', 'action', 'wild'],
        'color': ['r', 'g', 'b', 'y'],
        'trait': ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
                  'skip', 'reverse', 'draw_2', 'wild', 'wild_draw_4', 'white_wild', 'shuffle_wild']
        }


def init_deck():
    ''' Generate uno deck of 112 cards
    '''
    deck = []
    for color in INFO['color']:
        # init number cards
        for num in INFO['trait'][:10]:
            deck.append(Card('number', color, num))
            if num != '0':
                deck.append(Card('number', color, num))
        # init action cards
        for action in INFO['trait'][10:13]:
            deck.append(Card('action', color, action))
            deck.append(Card('action', color, action))

    # init wild cards
    for _ in range(3):
        deck.append(Card('wild', 'w', 'white_wild'))
    deck.append(Card('wild', 'w', 'shuffle_wild'))
    for _ in range(4):
        deck.append(Card('wild', 'w', 'wild_draw_4'))
        deck.append(Card('wild', 'w', 'wild'))
    # print(f'num of deck is {len(deck)}')
    return deck


def cards2list(cards):
    cards_list = []
    for card in cards:
        cards_list.append(card.get_str())
    return cards_list


def hand2dict(hand):
    hand_dict = {}
    for card in hand:
        if card not in hand_dict:
            hand_dict[card] = 1
        else:
            hand_dict[card] += 1
    return hand_dict


def max_color(hand):
    color_nums = {'r': 0.4, 'g': 0.3, 'b': 0.2, 'y': 0.1, 'w': -63}
    for card in hand:
        color = card.color
        # if color not in color_nums:
        #     print('color error')
        #     color_nums[color] = 0
        color_nums[color] += 1
    return max(color_nums, key=color_nums.get)
