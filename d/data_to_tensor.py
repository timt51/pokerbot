import cPickle
import copy
import data_to_tensor_helper as hp
import pprint
import numpy
from sys import getsizeof
pp = pprint.PrettyPrinter(indent=4)

def get_data():
	print('ok')
	with open('data.pickle') as f:
		data = cPickle.load(f)
	print('ok')

	x_data = {}
	y_data = {}

	for oppName in data:
		x_data[oppName] = []
		y_data[oppName] = []

		for game in data[oppName]:
			last_round = hp.last_round(game)
			#ignore games that tie
			# print pp.pprint(game)
			# if 'MOVES' not in game[last_round]:
			# 	continue
			if len(game[last_round]['MOVES'][oppName])>0 and game[last_round]['MOVES'][oppName][-1] == 'ties':
				continue

			#find cards_tensor
			hole_cards = hp.my_hole_cards(game)
			if 'preflop' == last_round:
				board_cards = []
			elif 'showdown' == last_round:
				board_cards = hp.final_board_cards(game, 'river')
			else:
				board_cards = hp.final_board_cards(game, last_round)
			all_cards = hole_cards + board_cards
			cards_tensor = hp.cards_as_tensor(hole_cards, board_cards) #sum matrices for last matrix (cards)

			#figure out if button
			if hp.button(game) == True:
				button_tensor = hp.one_tensor
			else:
				button_tensor = hp.zero_tensor

			#figure out pot tensor
			if 'showdown' == last_round:
				pot_tensor = hp.pot_as_tensor(game, last_round)
			else:
				pot_tensor = hp.pot_as_tensor(game, last_round)

			#figure out betting tensor
			betting_tensors = hp.betting_as_tensor(game, last_round)

			#figure out how much is won
			#won
			amount_won = int(game[last_round]['WIN'])
			#last move
			last_move = ''
			if len(game[last_round]['MOVES'][hp.myName]) > 0:
				last_move = game[last_round]['MOVES'][hp.myName][-1]
			elif last_round != 'preflop':
				for a_round in ['flop', 'turn', 'river']:
					if game[a_round]['POT'] == '800':
						last_move = game[hp.prev_round[a_round]]['MOVES'][hp.myName][-1]
						break
				if last_move == '':
					last_move = game[hp.prev_round[last_round]]['MOVES'][hp.myName][-1]
			else:
				continue

			game_tensor = cards_tensor
			game_tensor.append(pot_tensor)
			game_tensor.append(button_tensor)
			for tensor in betting_tensors['preflop']:
				game_tensor.append(tensor)
			for tensor in betting_tensors['flop']:
				game_tensor.append(tensor)
			for tensor in betting_tensors['turn']:
				game_tensor.append(tensor)
			for tensor in betting_tensors['river']:
				game_tensor.append(tensor)

			idx = 1
			if last_move == 'folds':
				idx = 0
				# amount_won = 0
			elif last_move == 'calls':
				idx = 2
			elif last_move == 'bet' or last_move == 'bets':
				idx = 3
			elif last_move == 'raises':
				idx = 4
			end_tensor = [0, 0, 0, 0, 0]
			end_tensor[idx] = amount_won/400.0
			
			x_data[oppName].append(game_tensor)
			y_data[oppName].append(end_tensor)


	#print pp.pprint(y_data[oppName])
	#print pp.pprint(data)
	return x_data, y_data