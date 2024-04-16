from rlcard.games.algoriuno.utils import cards2list, max_color, WILD, WILD_DRAW_4
from copy import copy

isTest = False


class UnoRound:
    def __init__(self, dealer, num_players, np_random):
        ''' Initialize the round class

        Args:
            dealer (object): the object of UnoDealer
            num_players (int): the number of players in game
        '''
        self.np_random = np_random
        self.dealer = dealer
        self.target = None
        self.current_player = 0
        self.num_players = num_players
        self.play_type = 0
        self.direction = 1
        self.played_cards = []
        self.last_action = [None for _ in range(self.num_players)]
        self.is_over = False
        self.winner = None

    def flip_top_card(self, first_player_hand):
        top = self.dealer.flip_top_card()
        self.played_cards.append(top)
        target_card = copy(top)
        if top.trait == 'wild':
            target_card.change_color(max_color(first_player_hand))
        self.target = target_card
        return target_card

    def perform_top_card(self, players, top_card):
        if top_card.trait == 'skip' or top_card.trait == 'wild':
            self.current_player = (self.current_player + self.direction) % self.num_players
        elif top_card.trait == 'reverse':
            self.direction = -1
            self.current_player = (self.current_player + self.direction) % self.num_players
        elif top_card.trait == 'draw_2':
            player = players[self.current_player]
            self.dealer.deal_cards(player)
            self.dealer.deal_cards(player)
            self.current_player = (self.current_player + self.direction) % self.num_players

    def get_state(self, players, player_id):
        state = {}
        player = players[player_id]
        state['hand'] = cards2list(player.hand)
        state['target'] = self.target.str
        state['played_cards'] = cards2list(self.played_cards)
        state['legal_actions'] = self.get_legal_actions(players, player_id)
        state['all_last_action'] = self.last_action
        state['direction'] = self.direction
        # if player.skip > 0:
        #     state['legal_actions'] = ['draw']
        # else:
        #     if self.play_type == 0:
        #         state['legal_actions'] = self.get_legal_actions(players, player_id)
        #     elif self.play_type == 1:
        #         state['legal_actions'] = self.draw_legal_actions(players, player_id)
        state['play_type'] = self.play_type
        state['num_cards'] = []
        for player in players:
            state['num_cards'].append(len(player.hand))
        state['skip_turn'] = []
        for player in players:
            state['skip_turn'].append(player.skip)
        return state

    def proceed_round(self, players, action):
        self.play_type = 0
        self.last_action[self.current_player] = action
        player = players[self.current_player]
        if action == 'draw':
            if player.skip > 0:
                player.skip -= 1
                self._draw_only(player)
                return None
            if len(player.hand) >= 25:
                self.current_player = (self.current_player + self.direction) % self.num_players
                return None
            self._perform_draw_action(player)
            return None
        elif action == 'pass':
            self.current_player = (self.current_player + self.direction) % self.num_players
            return None

        card_info = action.split('-')
        color = card_info[0]
        trait = card_info[1]
        # remove corresponding card
        remove_index = None
        if trait == 'wild' or trait == 'wild_draw_4' or trait == 'shuffle_wild' or trait == 'white_wild':
            for index, card in enumerate(player.hand):
                if trait == card.trait:
                    remove_index = index
                    break
        else:
            for index, card in enumerate(player.hand):
                if color == card.color and trait == card.trait:
                    remove_index = index
                    break
        card = player.hand.pop(remove_index)
        if not player.hand:
            self.is_over = True
            self.winner = self.current_player
        self.played_cards.append(card)
        target_card = copy(card)
        # perform the number action
        if card.type == 'number':
            self.current_player = (self.current_player + self.direction) % self.num_players
            self.target = target_card
        elif card.trait == 'shuffle_wild':
            target_card.change_color(color)
            self._perform_non_number_action(players, target_card)
            return target_card.str
        else:
            target_card.change_color(color)
            self._perform_non_number_action(players, target_card)
        return None

    def get_legal_actions(self, players, player_id):
        player = players[player_id]
        if player.skip > 0:
            return ['draw']
        else:
            if self.play_type == 0:
                return self.normal_legal_actions(player.hand)
            else:
                return self.draw_legal_actions(player.hand[-1])

    def normal_legal_actions(self, hand):
        wild_flag = True
        wild_draw_4_flag = True
        white_wild_flag = True
        legal_actions = []
        wild_4_actions = []
        # hand = players[player_id].hand
        if self.target.type == 'wild':
            for card in hand:
                if card.type == 'wild':
                    if card.trait == 'wild_draw_4':
                        if wild_draw_4_flag:
                            wild_draw_4_flag = False
                            wild_4_actions.extend(WILD_DRAW_4)
                    elif card.trait == 'wild':
                        if wild_flag:
                            wild_flag = False
                            legal_actions.extend(WILD)
                    elif card.trait == 'white_wild':
                        if white_wild_flag:
                            white_wild_flag = False
                            legal_actions.append('w-white_wild')
                    elif card.trait == 'shuffle_wild':
                        legal_actions.append('w-shuffle_wild')
                elif card.color == self.target.color:
                    legal_actions.append(card.str)
        # target is action card or number card
        else:
            for card in hand:
                if card.type == 'wild':
                    if card.trait == 'wild_draw_4':
                        if wild_draw_4_flag:
                            wild_draw_4_flag = False
                            wild_4_actions.extend(WILD_DRAW_4)
                    elif card.trait == 'wild':
                        if wild_flag:
                            wild_flag = False
                            legal_actions.extend(WILD)
                    elif card.trait == 'white_wild':
                        if white_wild_flag:
                            white_wild_flag = False
                            legal_actions.append('w-white_wild')
                    elif card.trait == 'shuffle_wild':
                        legal_actions.append('w-shuffle_wild')
                elif card.color == self.target.color or card.trait == self.target.trait:
                    legal_actions.append(card.str)
        if not legal_actions:
            legal_actions = wild_4_actions
        if len(hand) == 1 and legal_actions:
            return legal_actions
        unique_legal_actions = list(set(legal_actions))
        unique_legal_actions.append('draw')
        return unique_legal_actions

    def draw_legal_actions(self, draw_card):
        legal_actions = ['pass']
        # draw_card = players[player_id].hand[-1]
        if draw_card.type == 'wild':
            if draw_card.trait == 'wild_draw_4':
                legal_actions.extend(WILD_DRAW_4)
            elif draw_card.trait == 'wild':
                legal_actions.extend(WILD)
            elif draw_card.trait == 'white_wild':
                legal_actions.append('w-white_wild')
            elif draw_card.trait == 'shuffle_wild':
                legal_actions.append('w-shuffle_wild')
        elif draw_card.color == self.target.color or draw_card.trait == self.target.trait:
            if draw_card.type == 'action':
                legal_actions.append(draw_card.str)
            else:
                return [draw_card.str]
        return legal_actions

    def _perform_draw_action(self, player):
        self.play_type = 1
        if self._deck_check():
            return None
        card = self.dealer.deck.pop()
        player.hand.append(card)
        return None

    def _draw_only(self, player):
        if self._deck_check():
            return None
        card = self.dealer.deck.pop()
        player.hand.append(card)
        self.current_player = (self.current_player + self.direction) % self.num_players
        return None

    def _perform_non_number_action(self, players, target_card):
        # perform reverse card
        if target_card.trait == 'reverse':
            self.direction = -1 * self.direction
        elif target_card.trait == 'skip':
            self.current_player = (self.current_player + self.direction) % self.num_players
        elif target_card.trait == 'draw_2':
            draw_target_id = (self.current_player + self.direction) % self.num_players
            for _ in range(2):
                if self._deck_check():
                    return None
                self.dealer.deal_cards(players[draw_target_id])
            self.current_player = draw_target_id
        elif target_card.trait == 'wild':
            pass
        elif target_card.trait == 'wild_draw_4':
            draw_target_id = (self.current_player + self.direction) % self.num_players
            for _ in range(4):
                if self._deck_check():
                    return None
                self.dealer.deal_cards(players[draw_target_id])
            self.current_player = draw_target_id
        elif target_card.trait == 'shuffle_wild':
            self._player_card_shuffle(players)
            target_card.change_color(max_color(players[self.current_player].hand))
            self.last_action[self.current_player] = target_card.str
        elif target_card.trait == 'white_wild':
            skip_target_id = (self.current_player + self.direction) % self.num_players
            players[skip_target_id].skip += 2
            target_card.change_color(self.target.color)

        self.current_player = (self.current_player + self.direction) % self.num_players
        self.target = target_card

    def _player_card_shuffle(self, players):
        all_player_cards = []
        for player in players:
            all_player_cards.extend(player.hand)
            player.hand = []
        self.np_random.shuffle(all_player_cards)
        p = (self.current_player + self.direction) % self.num_players
        if not self.is_over:
            for card in all_player_cards:
                players[p].hand.append(card)
                p = (p + self.direction) % self.num_players
        else:
            for card in all_player_cards:
                players[p].hand.append(card)
                p = (p + self.direction) % self.num_players
                if p == self.current_player:
                    p = (p + self.direction) % self.num_players

    def _deck_check(self):
        if not self.dealer.deck:
            if len(self.played_cards) <= 1:
                self.is_over = True
                return True
            else:
                self.replace_deck()
                return False
        else:
            return False

    def replace_deck(self):
        top_card = self.played_cards[-1]
        self.dealer.deck.extend(self.played_cards[:-1])
        self.dealer.shuffle()
        self.played_cards = [top_card]
