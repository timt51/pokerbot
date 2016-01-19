import argparse
import socket
import sys
import newhand, getaction
from deuces import Evaluator

"""
Simple example pokerbot, written in python.

This is an example of a bare bones pokerbot. It only sets up the socket
necessary to connect with the engine and then always returns the same action.
It is meant as an example of how a pokerbot should communicate with the engine.
"""
class Player:
    def run(self, input_socket, evaluator):
        # Get a file-object for reading packets from the socket.
        # Using this ensures that you get exactly one packet per read.
        f_in = input_socket.makefile()
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
                # Currently CHECK on every move. You'll want to change this.
                getaction.move(data,oppName,holeCards,button,s,evaluator)
            elif word == "NEWHAND":
                handID = data[1]
                button = bool(data[2])
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

    bot = Player()
    evaluator = Evaluator()
    bot.run(s, evaluator)


#beginning strategy?
