from utils import SocketConst
from utils import handle_error


class SendEvent(object):
	def __init__(self, sio):
		self.sio = sio

	# イベント送信
	def send_join_room(self, data, callback):
		self.sio.emit(
			SocketConst.EMIT.JOIN_ROOM,
			data,
			callback=callback
		)

	def send_color_of_wild(self, data):
		print('{} data_req:'.format(SocketConst.EMIT.COLOR_OF_WILD), data)
		self.sio.emit(
			SocketConst.EMIT.COLOR_OF_WILD,
			data,
			callback=lambda err, undefined: handle_error(
				SocketConst.EMIT.COLOR_OF_WILD, err)
		)

	def send_play_card(self, data):
		print('{} data_req:'.format(SocketConst.EMIT.PLAY_CARD), data)
		self.sio.emit(
			SocketConst.EMIT.PLAY_CARD,
			data,
			callback=lambda err, undefined: handle_error(
				SocketConst.EMIT.PLAY_CARD, err)
		)

	def send_draw_card(self, data):
		print('{} data_req:'.format(SocketConst.EMIT.DRAW_CARD), data)
		self.sio.emit(
			SocketConst.EMIT.DRAW_CARD,
			data,
			callback=lambda err, undefined: handle_error(
				SocketConst.EMIT.DRAW_CARD, err)
		)

	def send_play_draw_card(self, data):
		print('{} data_req:'.format(SocketConst.EMIT.PLAY_DRAW_CARD), data)
		self.sio.emit(
			SocketConst.EMIT.PLAY_DRAW_CARD,
			data,
			callback=lambda err, undefined: handle_error(
				SocketConst.EMIT.PLAY_DRAW_CARD, err)
		)

	def send_say_uno_and_play_card(self, data):
		print('{} data_req:'.format(SocketConst.EMIT.SAY_UNO_AND_PLAY_CARD), data)
		self.sio.emit(
			SocketConst.EMIT.SAY_UNO_AND_PLAY_CARD,
			data,
			callback=lambda err, undefined: handle_error(
				SocketConst.EMIT.SAY_UNO_AND_PLAY_CARD, err)
		)

	def send_say_uno_and_play_draw_card(self, data):
		print('{} data_req:'.format(SocketConst.EMIT.SAY_UNO_AND_PLAY_DRAW_CARD), data)
		self.sio.emit(
			SocketConst.EMIT.SAY_UNO_AND_PLAY_DRAW_CARD,
			data,
			callback=lambda err, undefined: handle_error(
				SocketConst.EMIT.SAY_UNO_AND_PLAY_DRAW_CARD, err)
		)

	def send_pointed_not_say_uno(self, data):
		print('{} data_req:'.format(SocketConst.EMIT.POINTED_NOT_SAY_UNO), data)
		self.sio.emit(
			SocketConst.EMIT.POINTED_NOT_SAY_UNO,
			data,
			callback=lambda err, undefined: handle_error(
				SocketConst.EMIT.POINTED_NOT_SAY_UNO, err)
		)

	def send_challenge(self, data):
		print('{} data_req:'.format(SocketConst.EMIT.CHALLENGE), data)
		self.sio.emit(
			SocketConst.EMIT.CHALLENGE,
			data,
			callback=lambda err, undefined: handle_error(
				SocketConst.EMIT.CHALLENGE, err)
		)

	def send_special_logic(self, data):
		print('{} data_req:'.format(SocketConst.EMIT.SPECIAL_LOGIC), data)
		self.sio.emit(
			SocketConst.EMIT.SPECIAL_LOGIC,
			data,
			callback=lambda err, undefined: handle_error(
				SocketConst.EMIT.SPECIAL_LOGIC, err)
		)
