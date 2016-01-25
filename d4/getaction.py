import itertools
from deuces import Card, Deck #7462 max
import time
import random
import math
import numpy as np

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

def create_heuristic_action_distribution(numBoardCards,avg_rank,bets_this_round,has_button):
	bet_raise = 2.0
	check_call = 2.0
	fold = 0.5
	bet_amount = 0.0

	if has_button:
		bet_raise = 2.0
		check_call = 1.0
		fold = 0.5

	bet_faced = 0.0
	raise_amount = 0.0
	min_bet = 0.0
	max_bet = 0.0
	reasonable_bet = 0.0

	hand_value = 1-avg_rank/7462.0
	baseline_value = 0.4
	if numBoardCards == 3:
		baseline_value = baseline_value + 0.1
	elif numBoardCards == 4:
		baseline_value = baseline_value + 0.15
	elif numBoardCards == 5:
		baseline_value = baseline_value + 0.2

	if bets_this_round >= 1:
		baseline_value += 0.05 * bets_this_round
	baseline_value = min(baseline_value, 0.90)

	if hand_value > baseline_value:
		bet_increase = 3.0 / 0.10 * (hand_value - baseline_value)
		bet_raise += bet_increase
		fold_decrease = 0.5 / 0.10 * (hand_value - baseline_value)
		fold -= fold_decrease
	elif hand_value < baseline_value:
		bet_decrease = 1.0 / 0.10 * (hand_value - baseline_value)
		bet_raise -= bet_decrease
		fold_increase = 0.5 / 0.10 * (hand_value - baseline_value)
		fold += fold_increase

	if bets_this_round > 1:
		fold_decrease = 0.5 / 2 * (max(bets_this_round,5) - 1)
		fold -= fold_decrease
		check_call += 2 * fold_decrease

	raise_minimum = 0.0
	if bets_this_round == 0:
		raise_minimum += 0.5
		if has_button and numBoardCards >= 4:
			raise_minimum += 0.5
	if has_button and bets_this_round < 2:
		raise_minimum += 0.5

	return (max(bet_raise + raise_minimum, raise_minimum), check_call, max(fold, 0.0), math.floor(bet_amount))

def choose_heuristic_action(allowed_actions, numBoardCards, avg_rank, bets_this_round, has_button):
	(bet_raise, check_call, fold, bet_amount) = create_heuristic_action_distribution(numBoardCards,avg_rank,bets_this_round,has_button)

	action_sum = bet_raise + check_call + fold

	bet_raise /= action_sum
	check_call /= action_sum
	fold /= action_sum

	action_probs = []
	can_bet = False
	can_fold = False
	for action in allowed_actions:
		if "BET" in action or "RAISE" in action:
			can_bet = True
		if "FOLD" in action:
			call_fold = True

	for action in allowed_actions:
		probability = 0.0
		if "CALL" in action:
			probability += check_call
			if not can_bet:
				probability += bet_raise
		elif "BET" in action or "RAISE" in action:
			probability += bet_raise
		elif "FOLD" in action:
			probability += fold
		elif "CHECK" in action:
			probability += check_call
			if not can_fold:
				probability += fold
			if not can_bet:
				probability += bet_raise

		action_probs.append(probability)

	action_distribution = action_probs
	print '0---------', allowed_actions, action_distribution

	choice_action = np.random.choice(len(allowed_actions), 1, p=action_distribution)

	return (allowed_actions[choice_action[0]], bet_amount)

def move(data,oppName,holeCards,button,s,evaluator,bets_this_round):
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

	action = choose_heuristic_action(legalActions, numBoardCards, avg_rank, bets_this_round, button)
	action = action[0]

	min_bet = 0.0
	max_bet = 0.0
	for an_action in legalActions:
		if "BET" in an_action or "RAISE" in an_action:
			min_bet = an_action.split(':')[1]
			max_bet = an_action.split(':')[-1]
			break
	medium_bet = str(int((int(min_bet)+int(max_bet))/2))
	if avg_rank < 0.33:
		bet = random.choice([min_bet]*2+[medium_bet]*4+[max_bet]*9)
	elif avg_rank > 0.66:
		bet = random.choice([min_bet]*5+[medium_bet]*5+[max_bet]*5)
	else:
		bet = random.choice([min_bet]*3+[medium_bet]*5+[max_bet]*7)

	if action == "CALL":
		s.send("CALL\n")
	elif action == "CHECK":
		s.send("CHECK\n")
	elif action == "FOLD":
		s.send("FOLD\n")
	elif "BET" in action:
		s.send("BET:"+bet+"\n")
	elif "RAISE" in action:
		s.send("RAISE:"+bet+"\n")
	# if random.random() < 0.05:
	# 	s.send("FOLD\n")
	# else:
	# 	if "RAISE" in legalActions[-1] or "BET" in legalActions[-1]:
	# 		max_raise = legalActions[-1].split(':')[-1]
	# 		raise_odds = int(max_raise) / (int(potSize) + int(max_raise) + 0.0)

	# 		print "raise odds", raise_odds, (1- avg_rank/7462) + 0.4

	# 		if (1- avg_rank/7462) - random.random()/10 > raise_odds:
	# 			if "RAISE" in legalActions[-1]:
	# 				s.send("RAISE:" + max_raise + "\n")
	# 			elif "BET" in legalActions[-1]:
	# 				s.send("BET:" + max_raise + "\n")
	# 		else:
	# 			s.send("CALL\n")
	# 	elif (1 - avg_rank/7462) - random.random()/6 > call_odds:
	# 			s.send("CALL\n")
	# 	else:
	# 			s.send("FOLD\n")