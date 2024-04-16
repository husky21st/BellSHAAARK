class SocketConst:
    class EMIT:
        JOIN_ROOM = 'join-room'
        RECEIVER_CARD = 'receiver-card'
        FIRST_PLAYER = 'first-player'
        COLOR_OF_WILD = 'color-of-wild'
        UPDATE_COLOR = 'update-color'
        SHUFFLE_WILD = 'shuffle-wild'
        NEXT_PLAYER = 'next-player'
        PLAY_CARD = 'play-card'
        DRAW_CARD = 'draw-card'
        PLAY_DRAW_CARD = 'play-draw-card'
        CHALLENGE = 'challenge'
        PUBLIC_CARD = 'public-card'
        SAY_UNO_AND_PLAY_CARD = 'say-uno-and-play-card'
        SAY_UNO_AND_PLAY_DRAW_CARD = 'say-uno-and-play-draw-card'
        POINTED_NOT_SAY_UNO = 'pointed-not-say-uno'
        SPECIAL_LOGIC = 'special-logic'
        FINISH_TURN = 'finish-turn'
        FINISH_GAME = 'finish-game'
        PENALTY = 'penalty'


class Special:
    SKIP = 'skip'
    REVERSE = 'reverse'
    DRAW_2 = 'draw_2'
    WILD = 'wild'
    WILD_DRAW_4 = 'wild_draw_4'
    WILD_SHUFFLE = 'wild_shuffle'
    WHITE_WILD = 'white_wild'


class Color:
    RED = 'red'
    YELLOW = 'yellow'
    GREEN = 'green'
    BLUE = 'blue'
    BLACK = 'black'
    WHITE = 'white'


class DrawReason:
    DRAW_2 = 'draw_2'
    WILD_DRAW_4 = 'wild_draw_4'
    BIND_2 = 'bind_2'
    NOTING = 'nothing'


ARR_COLOR = {'r': Color.RED, 'y': Color.YELLOW, 'g': Color.GREEN, 'b': Color.BLUE, 'w': Color.RED}


# 共通エラー処理
def handle_error(event, err):
    if not err:
        return

    print('{} event failed!'.format(event))
    print(err)


def make_card_info(card_data):
    color = None
    trait = None
    for k, v in card_data.items():
        if k == 'color':
            if v == Color.RED:
                color = 'r'
            elif v == Color.GREEN:
                color = 'g'
            elif v == Color.BLUE:
                color = 'b'
            elif v == Color.YELLOW:
                color = 'y'
            else:
                color = 'w'
        elif k == 'number':
            trait = str(v)
        else:
            if v == Special.WILD_SHUFFLE:
                trait = 'shuffle_wild'
            else:
                trait = v
    return color + '-' + trait


def make_card_list(cards):
    card_list = []
    for card_data in cards:
        card_list.append(make_card_info(card_data))
    return card_list


def change_action_name(action):
    action_info = action.split('-')
    color = None
    number = None
    special = None
    if action_info[0] == 'r':
        color = Color.RED
    elif action_info[0] == 'g':
        color = Color.GREEN
    elif action_info[0] == 'b':
        color = Color.BLUE
    elif action_info[0] == 'y':
        color = Color.YELLOW

    if action_info[1] == Special.WILD:
        color = Color.BLACK
        special = Special.WILD
    elif action_info[1] == Special.WILD_DRAW_4:
        color = Color.BLACK
        special = Special.WILD_DRAW_4
    elif action_info[1] == Special.WHITE_WILD:
        color = Color.WHITE
        special = Special.WHITE_WILD
    elif action_info[1] == 'shuffle_wild':
        color = Color.BLACK
        special = Special.WILD_SHUFFLE
    elif action_info[1] == Special.SKIP:
        special = Special.SKIP
    elif action_info[1] == Special.DRAW_2:
        special = Special.DRAW_2
    elif action_info[1] == Special.REVERSE:
        special = Special.REVERSE
    else:
        number = action_info[1]

    if number is not None:
        return {'color': color, 'number': int(number)}
    else:
        return {'color': color, 'special': special}
