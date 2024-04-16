import numpy as np
from rlcard.games.algoriuno.utils import hand2dict

# a map of color to its index
COLOR_MAP = {'r': 0, 'g': 1, 'b': 2, 'y': 3, 'w': 1001}

# a map of trait to its index
TRAIT_MAP = {'0': 0, '1': 1, '2': 3, '3': 5, '4': 7, '5': 9, '6': 11, '7': 13,
             '8': 15, '9': 17, 'skip': 19, 'reverse': 21, 'draw_2': 23,
             'wild': 25, 'wild_draw_4': 26, 'white_wild': 27, 'shuffle_wild': 28}

TARGET_MAP = {'0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
              '8': 8, '9': 9, 'skip': 10, 'reverse': 11, 'draw_2': 12,
              'wild': 13, 'wild_draw_4': 14, 'white_wild': 16, 'shuffle_wild': 15}


def encode_hand(hand):
    plane = np.zeros((4, 28), dtype=np.int8)
    hand_num = hand2dict(hand)
    for card, count in hand_num.items():
        card_info = card.split('-')
        color = COLOR_MAP[card_info[0]]
        trait = TRAIT_MAP[card_info[1]]
        if trait <= 23:
            for num in range(count):
                plane[color][trait + num] = 1
        elif trait <= 27:
            for num in range(count):
                plane[num][trait] = 1
        # elif trait == 27:
        #     for num in range(count):
        #         plane[num][27] = 1
        else:
            plane[3][27] = 1

    return plane.flatten()


def encode_hide_card(visible_cards):
    plane = np.ones((4, 28), dtype=np.int8)
    visible_cards_num = hand2dict(visible_cards)
    for card, count in visible_cards_num.items():
        card_info = card.split('-')
        color = COLOR_MAP[card_info[0]]
        trait = TRAIT_MAP[card_info[1]]
        # print('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$')
        # print(color, trait, count)
        if trait <= 23:
            for num in range(count):
                plane[color][trait + num] = 0
        elif trait <= 27:
            for num in range(count):
                plane[num][trait] = 0
        # elif trait == 27:
        #     for num in range(count):
        #         plane[num][27] = 0
        else:
            plane[3][27] = 0

    return plane.flatten()


def encode_target(target):
    plane = np.zeros((4, 17), dtype=np.int8)
    # plane_white_wild = np.zeros(1, dtype=np.int8)
    target_info = target.split('-')
    color = COLOR_MAP[target_info[0]]
    trait = TARGET_MAP[target_info[1]]
    plane[color][trait] = 1
    # if trait != 100:
    #     plane[color][trait] = 1
    # else:
    #     plane_white_wild[0] = 1

    # return np.concatenate((plane.flatten(), plane_white_wild.flatten()))
    return plane.flatten()


def encode_another_last_play_action(all_last_action):
    plane_action_record = []
    for a in all_last_action:
        plane = np.zeros((4, 16), dtype=np.int8)
        plane_others = np.zeros(3, dtype=np.int8)
        if a is None:
            plane_action_record.append(plane.flatten())
            plane_action_record.append(plane_others)
            continue
        if a == 'draw':
            plane_others[1] = 1
            plane_action_record.append(plane.flatten())
            plane_action_record.append(plane_others)
            continue
        if a == 'pass':
            plane_others[2] = 1
            plane_action_record.append(plane.flatten())
            plane_action_record.append(plane_others)
            continue
        target_info = a.split('-')
        color = COLOR_MAP[target_info[0]]
        trait = TARGET_MAP[target_info[1]]
        if trait <= 15:
            plane[color][trait] = 1
        # elif trait == 15:
        #     plane_others[0] = 1
        else:
            plane_others[0] = 1
        plane_action_record.append(plane.flatten())
        plane_action_record.append(plane_others)
    return np.concatenate(plane_action_record)


# def encode_another_played_history(current_player_id, num_players, action_recorder):
#     plane = np.zeros((num_players - 1, 4, 28), dtype=np.int8)
#     action_history = [[] for _ in range(num_players)]
#     for a in action_recorder:
#         if a[1] == 'draw' or a[1] == 'pass':
#             continue
#         action_history[a[0]].append(a[1])
#     for i in range(num_players):
#         p = i
#         if i == current_player_id:
#             continue
#         elif i > current_player_id:
#             p -= 1
#         if len(action_history[i]) > 25:
#             action_history[i] = action_history[i][-25:]
#         action_rec = hand2dict(action_history[i])
#         for card, count in action_rec.items():
#             card_info = card.split('-')
#             color = COLOR_MAP[card_info[0]]
#             trait = TRAIT_MAP[card_info[1]]
#             if trait <= 23:
#                 for num in range(count):
#                     plane[p][color][trait + num] = 1
#             elif trait <= 26:
#                 for num in range(count):
#                     plane[p][num][trait] = 1
#             elif trait == 27:
#                 for num in range(count):
#                     plane[p][num][27] = 1
#             elif trait == 28:
#                 plane[p][3][27] = 1
#
#     return plane.flatten()


def encode_another_num_cards_left(current_player_id, num_players, num_left_cards):
    max_num_cards = 10
    one_hot = np.zeros((num_players - 1, max_num_cards), dtype=np.int8)
    for i in range(num_players):
        p = i
        if i == current_player_id:
            continue
        elif i > current_player_id:
            p -= 1
        if num_left_cards[i] >= 10:
            one_hot[p][9] = 1
        else:
            one_hot[p][num_left_cards[i] - 1] = 1
    return one_hot.flatten()


def encode_another_skip_turn(current_player_id, num_players, skip_turn):
    one_hot = np.zeros((num_players - 1, 3), dtype=np.int8)
    for i in range(num_players):
        p = i
        if i == current_player_id:
            continue
        elif i > current_player_id:
            p -= 1
        s_t = 2 if skip_turn[i] >= 3 else skip_turn[i]
        one_hot[p][s_t] = 1
    return one_hot.flatten()


def encode_action_record(action_record):
    plane_action_record = []
    # action_rec = deepcopy(action_record)
    if len(action_record) > 20:
        action_rec = action_record[-20:]
    else:
        action_rec = action_record
        for _ in range(20 - len(action_record)):
            plane = np.zeros((4, 16), dtype=np.int8)
            plane_others = np.zeros(3, dtype=np.int8)
            plane_action_record.append(plane.flatten())
            plane_action_record.append(plane_others)
    for a in action_rec:
        plane = np.zeros((4, 16), dtype=np.int8)
        plane_others = np.zeros(3, dtype=np.int8)
        if a[1] == 'draw':
            plane_others[1] = 1
            plane_action_record.append(plane.flatten())
            plane_action_record.append(plane_others)
            continue
        if a[1] == 'pass':
            plane_others[2] = 1
            plane_action_record.append(plane.flatten())
            plane_action_record.append(plane_others)
            continue
        target_info = a[1].split('-')
        color = COLOR_MAP[target_info[0]]
        trait = TARGET_MAP[target_info[1]]
        if trait <= 15:
            plane[color][trait] = 1
        # elif trait == 15:
        #     plane_others[0] = 1
        else:
            plane_others[0] = 1
        plane_action_record.append(plane.flatten())
        plane_action_record.append(plane_others)
    return np.concatenate(plane_action_record).reshape(-1, 67)
