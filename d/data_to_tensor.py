import cPickle
import copy
import data_to_tensor_helper as hp
import pprint
import numpy as np
from sys import getsizeof
pp = pprint.PrettyPrinter(indent=4)

def get_data():
	print('ok')
	with open('data.pickle') as f:
		data = cPickle.load(f)
	print('ok')

	x_data = {}
	y_data = {}
	mask = {}

	for oppName in data:
		x_data[oppName] = np.zeros((100000,35,17,17))
		y_data[oppName] = np.zeros((100000,5))
		mask[oppName] = np.zeros((100000,5))
		cnt = 0
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
				if 'preflop' == last_round:
					potSize = 3
				elif 'showdown' == last_round:
					potSize = abs(int(game[last_round]['WIN']))
				else:
					potSize = int(game[last_round]['POT'])
			elif last_round != 'preflop':
				for a_round in ['flop', 'turn', 'river']:
					if game[a_round]['POT'] == '800':
						last_move = game[hp.prev_round[a_round]]['MOVES'][hp.myName][-1]
						if 'preflop' == hp.prev_round[a_round]:
							potSize = 3
						else:
							potSize = int(game[hp.prev_round[a_round]]['POT'])
						break
				if last_move == '':
					last_move = game[hp.prev_round[last_round]]['MOVES'][hp.myName][-1]
					if 'preflop' == hp.prev_round[a_round]:
						potSize = 3
					elif 'showdown' == hp.prev_round[a_round]:
						potSize = abs(int(game[hp.prev_round[a_round]]['WIN']))
					else:
						potSize = int(game[hp.prev_round[a_round]]['POT'])
			else:
				continue

			last_opp_moves = []
			if len(game[last_round]['MOVES'][oppName]) > 0:
				last_opp_moves = game[last_round]['MOVES'][oppName]
			elif last_round != 'preflop':
				for a_round in ['flop', 'turn', 'river']:
					if game[a_round]['POT'] == '800':
						last_opp_moves = game[hp.prev_round[a_round]]['MOVES'][oppName]
						break
				if last_opp_moves == []:
					last_opp_moves = game[hp.prev_round[last_round]]['MOVES'][oppName]
			if len(last_opp_moves) > 0:
				last_opp_move = last_opp_moves[-1]

			last_move_temp = last_move.split(':')[0]
			if amount_won < 0:
				if last_move_temp == "checks":
					amount_won = potSize/-5.0
				elif last_move_temp == "calls":
					if "bets" in last_opp_move:
						amount_won = int(last_opp_move.split(':')[-1])*-1
					elif "raises" in last_opp_move:
						amount_won = (int(last_opp_move.split(':')[-1])-potSize)*-1
				elif last_move_temp == "raises":
					second_last_opp_move = last_opp_moves[-2]
					if second_last_opp_move.split(':')[0] == "bets":
						amount_won = (int(last_move.split(':')[-1])-(potSize+int(second_last_opp_move.split(':')[-1])))*-1
					elif second_last_opp_move.split(':')[0] == "raises":
						amount_won = (int(last_move.split(':')[-1])-int(second_last_opp_move.split(':')[-1]))*-1
					else:
						amount_won = (int(last_move.split(':')[-1])-potSize)*-1
				elif last_move_temp == "bets":
					amount_won = int(last_move.split(':')[-1])*-1
			last_move = last_move_temp

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
				amount_won = 0
			elif last_move == 'calls':
				idx = 2
			elif last_move == 'bet' or last_move == 'bets':
				idx = 3
			elif last_move == 'raises':
				idx = 4
			end_tensor = [0, 0, 0, 0, 0]
			mask_tensor = [0.0, 0.0, 0.0, 0.0, 0.0]

			end_tensor[idx] = (amount_won/400.00000) + 1.75
			# print end_tensor
			mask_tensor[idx] = 1.0
		
			x_data[oppName][cnt] = np.array(game_tensor)
			y_data[oppName][cnt] = np.array(end_tensor)
			mask[oppName][cnt] = np.array(mask_tensor)

			cnt +=1
		x_data[oppName] = x_data[oppName][:cnt+1]
		y_data[oppName] = y_data[oppName][:cnt+1]
		mask[oppName] = mask[oppName][:cnt+1]
			


	#print pp.pprint(y_data[oppName])
	#print pp.pprint(data)
	return x_data[oppName], y_data[oppName], mask[oppName]