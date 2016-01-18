import argparse
import socket
import sys
import newhand, getaction
from deuces import Evaluator
import data_to_tensor_helper as hp
import os
import time
import cPickle

import numpy as np
import theano
import theano.tensor as T

import lasagne

def build_cnn(input_var=None):
    # As a third model, we'll create a CNN of two convolution + pooling stages
    # and a fully-connected hidden layer in front of the output layer.

    # Input layer, as usual:
    network = lasagne.layers.InputLayer(shape=(None, 40, 17, 17),
                                        input_var=input_var)
    # This time we do not apply input dropout, as it tends to work less well
    # for convolutional layers.

    # Convolutional layer with 32 kernels of size 5x5. Strided and padded
    # convolutions are supported as well; see the docstring.
    network = lasagne.layers.Conv2DLayer(
            network, num_filters=32, filter_size=(5, 5),
            nonlinearity=lasagne.nonlinearities.rectify,
            W=lasagne.init.GlorotUniform())
    # Expert note: Lasagne provides alternative convolutional layers that
    # override Theano's choice of which implementation to use; for details
    # please see http://lasagne.readthedocs.org/en/latest/user/tutorial.html.

    # Max-pooling layer of factor 2 in both dimensions:
    network = lasagne.layers.MaxPool2DLayer(network, pool_size=(2, 2))

    # Another convolution with 32 5x5 kernels, and another 2x2 pooling:
    network = lasagne.layers.Conv2DLayer(
            network, num_filters=32, filter_size=(5, 5),
            nonlinearity=lasagne.nonlinearities.rectify)
    network = lasagne.layers.MaxPool2DLayer(network, pool_size=(2, 2))

    # A fully-connected layer of 256 units with 50% dropout on its inputs:
    network = lasagne.layers.DenseLayer(
            lasagne.layers.dropout(network, p=.5),
            num_units=256,
            nonlinearity=lasagne.nonlinearities.rectify)

    # And, finally, the 10-unit output layer with 50% dropout on its inputs:
    network = lasagne.layers.DenseLayer(
            lasagne.layers.dropout(network, p=.5),
            num_units=5,
            nonlinearity=lasagne.nonlinearities.softmax)

    return network
    
"""
Simple example pokerbot, written in python.

This is an example of a bare bones pokerbot. It only sets up the socket
necessary to connect with the engine and then always returns the same action.
It is meant as an example of how a pokerbot should communicate with the engine.
"""
class Player:
    def run(self, input_socket, evaluator, network, input_var):
        # Get a file-object for reading packets from the socket.
        # Using this ensures that you get exactly one packet per read.
        f_in = input_socket.makefile()
        data_tensor = [[[[0 for i in xrange(17)] for i in xrange(17)] for i in xrange(40)]]
        preflop_cnt = 12
        flop_cnt = 19
        turn_cnt = 26
        river_cnt = 33
        test_prediction = lasagne.layers.get_output(network, deterministic=True)
        predict_fn = theano.function([input_var], test_prediction)
        while True:
            # Block until the engine sends us a packet.
            data = f_in.readline().strip().split()
            # If data is None, connection has closed.
            if not data:
                print "Gameover, engine disconnected."
                break

            # Here is where you should implement code to parse the packets from
            # the engine and act on it. We are just printing it instead.
            print data, "\n"

            # When appropriate, reply to the engine with a legal action.
            # The engine will ignore all spurious responses.
            # The engine will also check/fold for you if you return an
            # illegal action.
            # When sending responses, terminate each response with a newline
            # character (\n) or your bot will hang!
            word = data[0]
            if word == "GETACTION":
                potSize = data[1]
                numBoardCards = int(data[2])
                boardCards = data[3:3 + numBoardCards]
                numLastActions = int(data[3 + numBoardCards])
                lastActions = data[4 + numBoardCards:4 + numBoardCards + numLastActions]
                numLegalActions = int(data[4 + numBoardCards + numLastActions])
                legalActions = data[5 + numBoardCards + numLastActions:-1]
                timebank = data[-1]

                cards_tensor = hp.cards_as_tensor(holeCards, boardCards)
                cnt = 0
                for tensor in cards_tensor:
                    data_tensor[0][cnt] = tensor
                    cnt += 1

                pot_tensor = hp.pot_as_tensor(int(potSize))
                data_tensor[0][10] = pot_tensor

                if numBoardCards == 0:
                    for action in lastActions:
                        if 'POST' in action:
                            continue
                        elif 'CALL' in action or 'RAISE' in action or 'BET' in action:
                            data_tensor[0][preflop_cnt] = hp.one_tensor
                            preflop_cnt += 1
                        else:
                            preflop_cnt += 1
                elif numBoardCards == 1:
                    for action in lastActions:
                        if 'DEAL' in action:
                            continue
                        elif 'CALL' in action or 'RAISE' in action or 'BET' in action:
                            data_tensor[0][preflop_cnt] = hp.one_tensor
                            flop_cnt += 1
                        else:
                            flop_cnt += 1
                elif numBoardCards == 2:
                    for action in lastActions:
                        if 'DEAL' in action:
                            continue
                        elif 'CALL' in action or 'RAISE' in action or 'BET' in action:
                            data_tensor[0][preflop_cnt] = hp.one_tensor
                            turn_cnt += 1
                        else:
                            turn_cnt += 1
                elif numBoardCards == 3:
                    for action in lastActions:
                        if 'DEAL' in action:
                            continue
                        elif 'CALL' in action or 'RAISE' in action or 'BET' in action:
                            data_tensor[0][preflop_cnt] = hp.one_tensor
                            river_cnt += 1
                        else:
                            river_cnt += 1

                prediction = np.argmax(predict_fn(data_tensor))
                print(prediction)
                if prediction == 0:
                    s.send("FOLD\n")
                elif prediction == 1:
                    s.sent("CHECK\n")

                s.send("CALL\n")
            elif word == "NEWHAND":
                handID = data[1]
                button = bool(data[2])
                if button == True:
                    button_tensor = hp.one_tensor
                else:
                    button_tensor = hp.zero_tensor
                data_tensor[0][11] = button_tensor
                holeCards = data[3:7]
                myBank = data[7]
                otherBank = data[8]
                timeBank = data[9]
            elif word == "NEWGAME":
                myName = data[1]
                oppName = data[2]
                stackSize = data[3]
                bb = data[4]
                numHands = data[5]
                timeBank = data[6]
            elif word == "HANDOVER":
                myBankRoll = data[1]
                oppBankRoll = data[2]
                numBoardCards = int(data[3])
                boardCards = data[4:4 + numBoardCards]
                numLastActions = int(data[4 + numBoardCards])
                lastActions = data[5 + numLastActions:-1]
                timeBank = data[-1]
                data_tensor = [[[[0 for i in xrange(17)] for i in xrange(17)] for i in xrange(40)]]
                preflop_cnt = 12
                flop_cnt = 19
                turn_cnt = 26
                river_cnt = 33
            elif word == "REQUESTKEYVALUES":
                # At the end, the engine will allow your bot save key/value pairs.
                # Send FINISH to indicate you're done.
                s.send("FINISH\n")

        # Clean up the socket.
        s.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='A Pokerbot.', add_help=False, prog='pokerbot')
    parser.add_argument('-h', dest='host', type=str, default='localhost', help='Host to connect to, defaults to localhost')
    parser.add_argument('port', metavar='PORT', type=int, help='Port on host to connect to')
    args = parser.parse_args()

    # Create a socket connection to the engine.
    print 'Connecting to %s:%d' % (args.host, args.port)
    try:
        s = socket.create_connection((args.host, args.port))
    except socket.error as e:
        print 'Error connecting! Aborting'
        exit()

    with open('network.pickle') as f:
        all_param_values = cPickle.load(f)
    f.close()
    input_var = T.tensor4('inputs')
    network = build_cnn(input_var)
    lasagne.layers.set_all_param_values(network, all_param_values)
    
    bot = Player()
    evaluator = Evaluator()
    bot.run(s, evaluator, network, input_var)


#beginning strategy?
