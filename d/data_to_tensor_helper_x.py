import copy
import numpy as np
import pprint
pp = pprint.PrettyPrinter(indent=4)

myName = 'RANDOMONE'
zero_tensor = [[0 for i in xrange(17)] for j in xrange(17)]
one_tensor = [[0 for i in xrange(17)] for j in xrange(17)]
for i in xrange(2,15):
	for j in xrange(6,10):
		one_tensor[j][i] = 1
betting_tensor = [[[0 for i in xrange(17)] for j in xrange(17)] for k in xrange(7)]
cards_tensor = [[[0 for i in xrange(17)] for j in xrange(17)] for k in xrange(5)]
suits = {'d':6, 'c':7, 'h':8, 's': 9}
value = {'A':14, '2':2, '3':3, '4':4, '5':5, '6':6, '7':7, '8':8, '9':9, 'T':10, 'J':11, 'Q':12, 'K':13}
prev_round = {'flop': 'preflop', 'turn': 'flop', 'river': 'turn', 'showdown': 'river'}

# def cards_as_tensor(hole_cards, board_cards):
# 	all_cards = hole_cards + board_cards
# 	cards_tensor_mod = copy.deepcopy(cards_tensor)

# 	count = 0
# 	for card in all_cards:
# 		cards_tensor_mod[count][suits[card[1]]][value[card[0]]] = 1
# 		count += 1

# 	last_cards_tensor = copy.deepcopy(np.matrix(zero_tensor))
# 	for matrix in cards_tensor_mod:
# 		last_cards_tensor = last_cards_tensor + np.matrix(matrix)
# 	last_cards_tensor = last_cards_tensor.tolist()

# 	cards_tensor_mod[9] = last_cards_tensor
# 	return cards_tensor_mod

def cards_as_tensor(hole_cards, board_cards):
	all_cards = hole_cards + board_cards
	cards_tensor_mod = copy.deepcopy(cards_tensor)

	count = 0
	for card in hole_cards:
		cards_tensor_mod[count][suits[card[1]]][value[card[0]]] = 1

	numBoardCards = len(board_cards)
	if numBoardCards >= 3:
		count += 1
		for card in board_cards[:3]:
			cards_tensor_mod[count][suits[card[1]]][value[card[0]]] = 1
	if numBoardCards >= 4:
		count += 1
		for card in board_cards[:4]:
			cards_tensor_mod[count][suits[card[1]]][value[card[0]]] = 1
	if numBoardCards >= 5:
		count += 1
		for card in board_cards[:5]:
			cards_tensor_mod[count][suits[card[1]]][value[card[0]]] = 1

	last_cards_tensor = copy.deepcopy(np.matrix(zero_tensor))
	for matrix in cards_tensor_mod:
		last_cards_tensor = last_cards_tensor + np.matrix(matrix)
	last_cards_tensor = last_cards_tensor.tolist()

	cards_tensor_mod[-1] = last_cards_tensor

	return cards_tensor_mod

def last_round(game):
	if 'showdown' in game:
		return 'showdown'
	elif 'river' in game:
		return 'river'
	elif 'turn' in game:
		return 'turn'
	elif 'flop' in game:
		return 'flop'
	else:
		return 'preflop'

def my_hole_cards(game):
	return game['preflop'][myName][1]

def final_board_cards(game,last_round):
	return game[last_round]['BOARDCARDS']

def button(game):
	if game['preflop'][myName][0][-1] == '1':
		return True
	else:
		return False

def pot_as_tensor(potSize):
	potSize /= 4
	pot_tensor = copy.deepcopy(zero_tensor)

	for i in xrange(2,15):
		for j in xrange(6,10):
			if potSize > 0:
				pot_tensor[j][i] = 1
				potSize -= 1
			else:
				return pot_tensor

	return pot_tensor

def betting_as_tensor(game, last_round):
	betting_tensors = {'preflop': copy.deepcopy(betting_tensor),
						'flop': copy.deepcopy(betting_tensor),
						'turn': copy.deepcopy(betting_tensor),
						'river': copy.deepcopy(betting_tensor)}

	has_button = button(game)

	for a_round in ['preflop', 'flop', 'turn', 'river']:
		if a_round != 'preflop' and game[a_round]['POT'] == '800':
			break

		if (a_round == 'preflop') == has_button:
			list1 = game[a_round]['MOVES'][myName]
			list2 = game[a_round]['MOVES']['RANDOMTWO']
			num = min(len(list1), len(list2))
			result = [None]*(num*2)
			result[::2] = list1[:num]
			result[1::2] = list2[:num]
			result.extend(list1[num:])
			result.extend(list2[num:])
			moves = result
		else:
			list2 = game[a_round]['MOVES'][myName]
			list1 = game[a_round]['MOVES']['RANDOMTWO']
			num = min(len(list1), len(list2))
			result = [None]*(num*2)
			result[::2] = list1[:num]
			result[1::2] = list2[:num]
			result.extend(list1[num:])
			result.extend(list2[num:])
			moves = result			

		count = 0
		for move in moves:
			if move in ['raises', 'bets', 'calls']:
				betting_tensors[a_round][count] = one_tensor
			count += 1




		if a_round == last_round:
			break

	return betting_tensors
