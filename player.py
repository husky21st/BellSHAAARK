#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse

import os

import sys
import time

import socketio

from rich import print
from send_event import SendEvent
from utils import SocketConst, DrawReason, ARR_COLOR
from utils import make_card_list, make_card_info, change_action_name

from model import Agent


SPECIAL_LOGIC_TITLE = '最後の希望'
TEST_TOOL_HOST_PORT = '3000'
TIME_DELAY = 50


print('Start demo player ...')

parser = argparse.ArgumentParser(description='A demo player written in Python')
parser.add_argument('host', action='store', type=str,
                    help='Host to connect')
parser.add_argument('room_name', action='store', type=str,
                    help='Name of the room to join')
parser.add_argument('player', action='store', type=str,
                    help='Player name you join the game as')
parser.add_argument('event_name', action='store', nargs='?', default=None, type=str,
                    help='Event name for test tool')

args = parser.parse_args(sys.argv[1:])
host = args.host
room_name = args.room_name
player = args.player
event_name = args.event_name
is_test_tool = TEST_TOOL_HOST_PORT in host

print('Start demo player ...')

print({
    'host': host,
    'room_name': room_name,
    'player': player,
    'is_test_tool': is_test_tool,
    'event_name': event_name
})


once_connected = False
id = ''
uno_declared = {}
if not host:
    print('Host missed')
    os._exit(0)
if not room_name or not player:
    print('Arguments invalid')
    # If test-tool, ignore exit

    if not is_test_tool:
        os._exit(0)

# SocketIO Client
sio = socketio.Client()
emitter = SendEvent(sio)
agent = Agent()
first_trig = True


def execute_play(hand_num, pre_action):
    action = change_action_name(pre_action)
    data = {
        'card_play': action,
    }
    if hand_num == 2:
        # call event say-uno-and-play-card
        emitter.send_say_uno_and_play_card(data)
    else:
        # call event play-card
        emitter.send_play_card(data)


def determine_if_execute_pointed_not_say_uno(number_card_of_player, target_id):
    global uno_declared
    target = None
    for k, v in number_card_of_player.items():
        if v == 1:
            target = k
            break
        elif k in uno_declared:
            del uno_declared[k]

    target_num = number_card_of_player.get(target_id)
    if (
        target is not None and
        target != id and
        target not in uno_declared.keys()
        and target == target_id
        and target_num is not None and target_num == 1
    ):
        emitter.send_pointed_not_say_uno({
            'target': target,
        })
        time.sleep(TIME_DELAY / 1000)


def play_challenge(number_card_of_player, play_draw_4_player_id):
    if number_card_of_player[play_draw_4_player_id] >= 4:
        num_cards = agent.num_cards
        min_num_cards = min(num_cards)
        if min_num_cards == 1:
            return True
    return False


@sio.on('connect')
def on_connect():
    print('Client connect successfully!')
    global once_connected

    def join_room_callback(*args):
        global once_connected, id, agent
        if args[0]:
            print('Client join room failed!')
            print(args[0])
            sio.disconnect()
        else:
            print('Client join room successfully!')
            print(args[1])
            once_connected = True
            id = args[1].get('your_id')
            agent.set_id(id)

    if not once_connected:
        data_join_room = {
            'room_name': room_name,
            'player': player
        }
        emitter.send_join_room(data_join_room, join_room_callback)
        return


@sio.on('disconnect')
def on_disconnect():
    print('Client disconnect:')
    os._exit(0)


@sio.on(SocketConst.EMIT.JOIN_ROOM)
def on_join_room(data_res):
    # no action
    print('join room: data_res:', data_res)


@sio.on(SocketConst.EMIT.RECEIVER_CARD)
def on_receiver_card(data_res):
    global agent, first_trig
    # set hand, max_color
    receive_cards = data_res.get('cards_receive')
    if len(receive_cards) == 7 and first_trig:
        # reset model
        agent.reset()
        agent.set_hand(make_card_list(receive_cards))
        agent.set_max_color()
        first_trig = False
    agent.last_receive_cards = make_card_list(receive_cards)
    print('{} receive cards: '.format(id))
    print(data_res)


@sio.on(SocketConst.EMIT.FIRST_PLAYER)
def on_first_player(data_res):
    global agent
    # set target, player_id, direction, add played_card
    target_card = make_card_info(data_res.get('first_card'))
    agent.set_target(target_card)
    agent.set_player(data_res.get('play_order'))
    agent.add_play_card(target_card)
    trait = data_res.get('first_card').get('special')
    if trait is not None and trait == 'reverse':
        agent.direction *= -1
    # TODO add action_record
    print('{} is first player.'.format(data_res.get('first_player')))
    print(data_res)


@sio.on(SocketConst.EMIT.COLOR_OF_WILD)
def on_color_of_wild(data_res):
    global agent
    time.sleep(TIME_DELAY / 1000)
    # send wild color
    if agent.send_wild_color is None or agent.send_wild_color == 'w':
        agent.set_max_color()
        color_of_wild = ARR_COLOR[agent.send_wild_color]
    else:
        color_of_wild = ARR_COLOR[agent.send_wild_color]
    data = {
        'color_of_wild': color_of_wild,
    }
    emitter.send_color_of_wild(data)


@sio.on(SocketConst.EMIT.UPDATE_COLOR)
def on_update_color(data_res):
    global agent
    # set target
    agent.update_target(data_res.get('color'))
    # TODO change last action_record
    print('update reveal card color is {}.'.format(data_res.get('color')))
    print(data_res)


@sio.on(SocketConst.EMIT.SHUFFLE_WILD)
def on_shuffle_wild(data_res):
    global agent
    # set hand, max_color
    receive_cards = data_res.get('cards_receive')
    agent.set_hand(make_card_list(receive_cards))
    agent.set_max_color()
    agent.set_num_cards(data_res.get('number_card_of_player'))
    global uno_declared
    uno_declared = {}
    for k, v in data_res.get('number_card_of_player').items():
        if v == 1:
            uno_declared[data_res.get('player')] = True
            break
        elif k in uno_declared:
            del uno_declared[k]
    print('{} receive cards from shuffle wild.'.format(id))
    print(data_res)


@sio.on(SocketConst.EMIT.PLAY_CARD)
def on_play_card(data_res):
    global agent
    # white_wild -> set skip_turn
    # set direction
    # TODO add action_record
    card_play = data_res.get('card_play')
    player_id = data_res.get('player')
    color = card_play.get('color')
    if color == 'white':
        agent.set_skip_turn(player_id)
    agent.decrease_num_cards(player_id)
    trait = card_play.get('special')
    if trait is not None and trait == 'reverse':
        agent.direction *= -1
    card = make_card_info(card_play)
    agent.add_play_card(card)
    print(
        '{} play card {} {}.'.format(
            data_res.get('player'), card_play.get('color'), card_play.get('special') or card_play.get('number'))
    )
    print('{} data_res:'.format(SocketConst.EMIT.PLAY_CARD), data_res)


@sio.on(SocketConst.EMIT.DRAW_CARD)
def on_draw_card(data_res):
    global agent
    time.sleep(TIME_DELAY / 1000)
    # skip_turn -= 1
    player_id = data_res.get('player')
    agent.decrease_skip_turn(player_id)
    # TODO add action_record
    print('{} data_res:'.format(SocketConst.EMIT.DRAW_CARD), data_res)
    # can_play_draw_card == True -> send False(pass) or send True(card)
    if data_res.get('player') == id:
        c_p_d_c = data_res.get('can_play_draw_card')
        if c_p_d_c is True or str(c_p_d_c) == 'True' or str(c_p_d_c) == 'true':
            print('{} data_req:'.format(SocketConst.EMIT.PLAY_DRAW_CARD), {
                'is_play_card': True
            })
            agent.play_type = 1
            action = agent.action()
            trig = False if action == 'pass' else True
            if trig:
                if len(agent.hand) == 1:
                    emitter.send_say_uno_and_play_draw_card({})
                else:
                    data = {
                        'is_play_card': trig
                    }
                    emitter.send_play_draw_card(data)
            else:
                data = {
                    'is_play_card': trig
                }
                emitter.send_play_draw_card(data)
        else:
            print('{} can not play draw card.'.format(data_res.get('player')))


@sio.on(SocketConst.EMIT.PLAY_DRAW_CARD)
def on_play_draw_card(data_res):
    global agent
    # white_wild -> set skip_turn
    # set direction
    card_play = data_res.get('card_play')
    player_id = data_res.get('player')
    if card_play is not None:
        color = card_play.get('color')
        if color == 'white':
            agent.set_skip_turn(player_id)
        agent.decrease_num_cards(player_id)
        trait = card_play.get('special')
        if trait is not None and trait == 'reverse':
            agent.direction *= -1
        card = make_card_info(card_play)
        agent.add_play_card(card)
    # TODO add action_record
    print('{} data_res:'.format(SocketConst.EMIT.PLAY_DRAW_CARD), data_res)
    print('{} play draw card.'.format(data_res.get('player')))


@sio.on(SocketConst.EMIT.CHALLENGE)
def on_challenge(data_res):
    global agent
    # update chicken trigger
    if data_res.get('is_challenge'):
        play_draw_4_player_id = data_res.get('target')
        if play_draw_4_player_id is not None:
            if agent.get_num_cards(play_draw_4_player_id) <= 4:
                agent.chicken_trig = False
        if data_res.get('is_challenge_success'):
            print('{} challenge successfully!'.format(
                data_res.get('challenger')))
        else:
            print('{} challenge failed!'.format(data_res.get('challenger')))
    else:
        print('{} no challenge.'.format(data_res.get('challenger')))


@sio.on(SocketConst.EMIT.PUBLIC_CARD)
def on_public_card(data_res):
    # no action
    print('Public card of player {}.'.format(data_res.get('card_of_player')))
    print(data_res.get('cards'))


@sio.on(SocketConst.EMIT.SAY_UNO_AND_PLAY_CARD)
def on_say_uno_and_play_card(data_res):
    global uno_declared, agent
    # white_wild -> set skip_turn
    # set direction
    card_play = data_res.get('card_play')
    player_id = data_res.get('player')
    color = card_play.get('color')
    if color == 'white':
        agent.set_skip_turn(player_id)
    agent.decrease_num_cards(player_id)
    trait = card_play.get('special')
    if trait is not None and trait == 'reverse':
        agent.direction *= -1
    card = make_card_info(card_play)
    agent.add_play_card(card)
    uno_declared[data_res.get('player')] = True
    # TODO add action_record
    card_play = data_res.get('card_play', {})
    print(
        '{} play card {} {} and say UNO.'.format(
            data_res.get('player'), card_play.get('color'), card_play.get('special') or card_play.get('number'))
    )


@sio.on(SocketConst.EMIT.SAY_UNO_AND_PLAY_DRAW_CARD)
def on_say_uno_and_play_draw_card(data_res):
    global uno_declared, agent
    # white_wild -> set skip_turn
    # set direction
    card_play = data_res.get('card_play')
    player_id = data_res.get('player')
    color = card_play.get('color')
    if color == 'white':
        agent.set_skip_turn(player_id)
    agent.decrease_num_cards(player_id)
    trait = card_play.get('special')
    if trait is not None and trait == 'reverse':
        agent.direction *= -1
    card = make_card_info(card_play)
    agent.add_play_card(card)
    uno_declared[data_res.get('player')] = True
    # TODO add action_record
    card_play = data_res.get('card_play', {})
    print(
        '{} play draw card {} {} and say UNO.'.format(
            data_res.get('player'), card_play.get('color'), card_play.get('special') or card_play.get('number'))
    )


@sio.on(SocketConst.EMIT.POINTED_NOT_SAY_UNO)
def on_pointed_not_say_uno(data_res):
    # no action
    if str(data_res.get('have_say_uno')) == 'True':
        print('{} have say UNO.'.format(data_res.get('target')))
    elif str(data_res.get('have_say_uno')) == 'False':
        print('{} no say UNO.'.format(data_res.get('target')))


@sio.on(SocketConst.EMIT.FINISH_TURN)
def on_finish_turn(data_res):
    global first_trig
    first_trig = True
    # no action
    if data_res.get('winner'):
        print('Winner turn {} is {}.'.format(
            data_res.get('turn_no'), data_res.get('winner')))
    else:
        print('Finish turn. No winner is this turn.')


@sio.on(SocketConst.EMIT.FINISH_GAME,)
def on_finish_game(data_res):
    # no action
    print(data_res)
    print('Winner of game {}, turn win is {}.'.format(
        data_res.get('winner'), data_res.get('turn_win')))


@sio.on(SocketConst.EMIT.PENALTY,)
def on_finish_game(data_res):
    global uno_declared
    # no action
    print(data_res)
    print('{} gets a penalty. Reason: {}'.format(
        data_res.get('player'), data_res.get('error')))
    if data_res.get('player') in uno_declared:
        del uno_declared[data_res.get('player')]


@sio.on(SocketConst.EMIT.NEXT_PLAYER)
def on_next_player(data_res):
    global agent
    agent.play_type = 0
    print('{} data_res: '.format(SocketConst.EMIT.NEXT_PLAYER), data_res)
    time.sleep(TIME_DELAY / 1000)
    print('{} is next player. turn: {}'.format(
        data_res.get('next_player'),
        data_res.get('number_turn_play')
    ))
    # set hand, target, num_cards
    hands = make_card_list(data_res.get('card_of_player'))
    agent.set_hand(hands)
    target_card = make_card_info(data_res.get('card_before'))
    agent.set_target(target_card)
    agent.set_num_cards(data_res.get('number_card_of_player'))
    # check direction and played_card
    # if target_card[1:] != agent.played_cards[-1][1:]:
    #     print('played error')
    #     print(target_card)
    #     print(agent.played_cards)
    #     # return None
    t_r = data_res.get('turn_right')
    _direction = 1 if t_r is True or str(t_r) == 'true' else -1
    # if _direction != agent.direction:
    #     print('direction error')
    #     # return None
    agent.direction = _direction
    determine_if_execute_pointed_not_say_uno(data_res.get('number_card_of_player'), data_res.get('before_player'))
    print('Run NEXT_PLAYER ...')

    # play_wild_draw4_turnの直後のターンの場合 プレイの前にChallengeができます。
    # ただし、白いワイルド（bind_2）の効果が発動している間はチャレンジができません。
    # send challenge if draw_reason is 'wild_draw_4' and more
    draw_reason = data_res.get('draw_reason')
    if draw_reason == DrawReason.WILD_DRAW_4 and agent.get_my_skip_turn() == 0:
        do_challenge = play_challenge(data_res.get('number_card_of_player'), data_res.get('before_player'))
        data = {
                'is_challenge': do_challenge,
        }
        emitter.send_challenge(data)
        if do_challenge:
            return

    # TODO send special_logic
    # special_logic_num_random = random_by_number(10)
    # if special_logic_num_random == 0:
    #     data = {
    #         'title': SPECIAL_LOGIC_TITLE,
    #     }
    #     emitter.send_special_logic(data)

    # send draw or play_card
    # wild card change color and trait name
    m_c_d_c = data_res.get('must_call_draw_card')
    if m_c_d_c is True or str(m_c_d_c) == 'True' or str(m_c_d_c) == 'true':
        # If must_call_draw_card = True, Player must be call event draw_card
        print('{} data_req:'.format(SocketConst.EMIT.DRAW_CARD), {
            'player': id,
        })
        emitter.send_draw_card({})
        return
    else:
        action = agent.action()
        if action == 'draw':
            emitter.send_draw_card({})
        else:
            execute_play(len(hands), action)
        return


@sio.on('*')
def catch_all(event, data):
    print('!! unhandled event: {} '.format(event), data)


def main():
    sio.connect(
        args.host,
        transports=['websocket'],
    )
    sio.wait()


if __name__ == '__main__':
    main()
