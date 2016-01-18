import itertools
from deuces import Card, Deck #7462 max
import time
import random

import numpy as np
import theano
import theano.tensor as T

import lasagne

def move(data,oppName,holeCards,button,s,evaluator,network):
	potSize = data[1]
	numBoardCards = int(data[2])
	boardCards = data[3:3 + numBoardCards]
	numLastActions = int(data[3 + numBoardCards])
	lastActions = data[4 + numBoardCards:4 + numBoardCards + numLastActions]
	numLegalActions = int(data[4 + numBoardCards + numLastActions])
	legalActions = data[5 + numBoardCards + numLastActions:-1]
	timebank = data[-1]

	avg_rank = average_rank(evaluator, holeCards, boardCards)
	call_odds = odds(oppName, potSize, lastActions)

	if "RAISE" in legalActions[-1] or "BET" in legalActions[-1]:
		max_raise = legalActions[-1].split(':')[-1]
		raise_odds = int(max_raise) / (int(potSize) + int(max_raise) + 0.0)

		print "raise odds", raise_odds, (1- avg_rank/7462) + 0.4

		if (1- avg_rank/7462) - random.random()/3 > raise_odds:
			if "RAISE" in legalActions[-1]:
				s.send("RAISE:" + max_raise + "\n")
			elif "BET" in legalActions[-1]:
				s.send("BET:" + max_raise + "\n")
		else:
			s.send("CALL\n")
	elif (1 - avg_rank/7462) - random.random()/5 > call_odds:
			s.send("CALL\n")
	else:
			s.send("FOLD\n")

	# if "POST" in "".join(lastActions):
	# 	if button == True:
	# 		if avg_rank/7462 < 0.95:
	# 			s.send("CALL\n")
	# 		else:
	# 			s.send("FOLD\n")
	# 	else:
	# 		if avg_rank/7462 < 0.50:
	# 			s.send("CALL\n")
	# 		else:
	# 			s.send("FOLD\n")
	# else:
	# 	if button == True:
	# 		if avg_rank/7462 - 0.1 > call_odds:
	# 			s.send("CALL\n")
	# 		else:
	# 			s.send("FOLD\n")
	# 	else:
	# 		if avg_rank/7462  - 0.1 > call_odds:
	# 			s.send("CALL\n")
	# 		else:
	# 			s.send("FOLD\n")

def rank(evaluator, holeCards, boardCards):
	deck = Deck()

	allCards = holeCards.union(boardCards)
	while len(allCards) < 9:
		card = deck.draw(1)
		if len(allCards) != len(allCards.union([card])):
			allCards.add(card)
			boardCards.add(card)

	all2CardCombos = itertools.combinations(holeCards,2)
	all3CardCombos = itertools.combinations(boardCards,3)

	min_rank = 10000

	for handCombo in all2CardCombos:
		for boardCombo in all3CardCombos:
			rank = evaluator.evaluate(boardCombo, handCombo)
			if rank < min_rank:
				min_rank = rank

	return min_rank

def average_rank(evaluator, holeCards, boardCards):
	holeCards = map(Card.new, holeCards)
	boardCards = map(Card.new, boardCards)

	if len(boardCards) == 0 or len(boardCards) == 3:
		reps = 101
	elif len(boardCards) == 4:
		reps = 51
	else:
		reps = 2

	ranks = [0.0]
	for i in range(1,reps):
		ranks.append(rank(evaluator, set(holeCards), set(boardCards)))

	return sum(ranks)/(len(ranks)-1)

def odds(oppName, potSize, lastActions):
	#either post, bet, raise, check
	#only care about opponent moves
	lastActions = [action for action in lastActions if oppName in action]
	if len(lastActions) == 0:
		return 0
	lastAction = lastActions[-1]

	if "CHECK" in lastAction:
		call = 0
	elif "BET" in lastAction:
		call = int(lastAction[4])
	elif "RAISE" in lastAction:
		call = (int(potSize)-int(lastAction[6]))
	elif "POST" in lastAction:
		call = 1
	else:
		call = 0

	return call/(float(potSize)+call)

#aggression index
#if aggression < __:
#check/fold
#elif aggression < __:
#call
#else
#bet/raise