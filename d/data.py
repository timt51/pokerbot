import os
import cPickle
import pprint
pp = pprint.PrettyPrinter(indent=4)

data = {}
myName = 'FOLDERBOT'

path = './Hand Logs/'
for filename in os.listdir(path):
	with open(path + filename) as f:
		oppName = [name for name in filename.split('_') if (name != 'FOLDERBOT' and name != 'vs')][0]
		print oppName

		data[oppName] = []
		count = -1

		for line in f:
			if 'Uncalled' in line or 'shows' in line:
				continue
			line = line.rstrip()
			if line == '' or '6.1' in line:
				continue
			if "Hand" in line:
				data[oppName].append({})
				count += 1
				stage = 'preflop'
				data[oppName][count][stage] = {}
				continue
			line_split = line.split(' ')
			line_no_brackets = (' ').join(line_split).replace('[','').replace(']','').split(' ')

			if 'FLOP' in line:
				stage = 'flop'
				data[oppName][count][stage] = {}
			elif 'TURN' in line:
				stage = 'turn'
				data[oppName][count][stage] = {}
			elif 'RIVER' in line:
				stage = 'river'
				data[oppName][count][stage] = {}
			elif 'show' in line:
				stage = 'showdown'
				data[oppName][count][stage] = {}

			if 'post' in line:
				data[oppName][count][stage][line_split[0]] = ['POST:' + line_split[-1]]
				continue
			if 'Dealt' in line:
				data[oppName][count][stage][line_split[2]].append(line_no_brackets[3:])
				continue
			if 'FLOP' in line:
				data[oppName][count][stage]['POT'] = line_no_brackets[3].replace('(','').replace(')','')
				data[oppName][count][stage]['BOARDCARDS'] = line_no_brackets[4:]
				continue
			if 'TURN' in line:
				data[oppName][count][stage]['POT'] = line_no_brackets[3].replace('(','').replace(')','')
				data[oppName][count][stage]['BOARDCARDS'] = line_no_brackets[4:]
				continue
			if 'RIVER' in line:
				data[oppName][count][stage]['POT'] = line_no_brackets[3].replace('(','').replace(')','')
				data[oppName][count][stage]['BOARDCARDS'] = line_no_brackets[4:]
				continue

			if 'MOVES' not in data[oppName][count][stage]:
				if 'wins' == line_split[1]:
					if line_split[0] == myName:
						data[oppName][count][stage]['WIN'] = line_split[-1].replace('(','').replace(')','')
					else:
						data[oppName][count][stage]['WIN'] = ('-' + line_split[-1].replace('(','').replace(')',''))
				data[oppName][count][stage]['MOVES'] = {myName:[], oppName:[]}
				if "bet" in line_split[1] or "raise" in line_split[1]:
					data[oppName][count][stage]['MOVES'][line_split[0]].append(line_split[1]+':'+line_split[-1])
				elif 'wins' != line_split[1]:
					data[oppName][count][stage]['MOVES'][line_split[0]].append(line_split[1])
				continue
			if 'wins' == line_split[1]:
				if line_split[0] == myName:
					data[oppName][count][stage]['WIN'] = line_split[-1].replace('(','').replace(')','')
				else:
					data[oppName][count][stage]['WIN'] = ('-' + line_split[-1].replace('(','').replace(')',''))
			else:
				if "bet" in line_split[1] or "raise" in line_split[1]:
					data[oppName][count][stage]['MOVES'][line_split[0]].append(line_split[1]+':'+line_split[-1])
				else:
					data[oppName][count][stage]['MOVES'][line_split[0]].append(line_split[1])

with open('data.pickle', 'w') as f:
	cPickle.dump(data,f)
