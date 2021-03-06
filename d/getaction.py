import itertools
import time
import random
import data_to_tensor_helper as hp

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

	cards_tensor = hp.cards_as_tensor(holeCards, boardCards)

 	s.send("CALL\n")