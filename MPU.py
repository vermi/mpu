#!/usr/bin/python

'''
MPU bot by James Pearson
licensed under the WTF license
'''

import sys
from time import strftime, sleep
import cPickle as pickle
import commands
import re
import irclib
import dirty_secrets
import random
import urllib2
import re
from datetime import datetime, time, timedelta

## Beginning Setup
# Connection information
network = dirty_secrets.network
port = dirty_secrets.port
password = dirty_secrets.password
channel = dirty_secrets.channel
nick = dirty_secrets.nick
name = dirty_secrets.name
trigger = '!'

gagged = False
lastmessage = { }
lastaction = { }

# Create an IRC object
irc = irclib.IRC()

## Methods
# a shortened way to send messages to the channel
def say(message):
	if(not gagged):
		server.privmsg(channel, message)
		sleep(1)
def action(message):
	if(not gagged):
		server.action(channel, message)
		sleep(1)

def help(command=None):
	global users
	global nick

	if command=='help':
		say("If called by itself, will list all available commands. Followed by another command, will give more information on that command.")
		return True
	elif command=='source':
		say("Gives the address of the Git repository of MPU's code.")
		return True
	elif command=='report':
		say("Will send whatever follows to "+users['owner']+" in a PM, or log it if he's offline.")
		return True
	elif command=='kill':
		say("Disconnects from "+network+".")
		return True
	elif command=='gag':
		say("Prevents the bot from speaking until ungagged.")
		return True
	elif command=='ungag':
		say("Allows the bot to speak again after being gagged.")
		return True
	elif command=='info':
		say("Gets information on a user.")
		say("Usage: 'info [username]' to list infos, 'info [username] [info1, info2...]' to get infos.")
		return True
	elif command=='infoset':
		say("Sets information about you.")
		say("Usage: infoset [info] [details]")
		return True
	elif command=='changelog':
		say("Tells what's been changed recently.  If given an argument, get all changes since then.")
		say('Example: changelog 2weeks, changelog "12 march"')
		return True
	elif command=='whatis':
		say("Let's you know what everyone's talking about.  Best used via pm.")
		say("Example: whatis foo, whatis set foo a common metasyntatic variable")
		return True
	elif command=='usermod':
		say("Changes the status of a user, as viewed by "+nick)
		say("Usage: usermod [list] [user1 [user2 user3...]]")
	else:
		say("Available commands: " + (' '.join(sorted(handleFlags.keys()))))
		say("Type 'help [command]' to get more info about command.")
		say("I also respond to PMs; just remember you don't need ! in front of the command.")
		return True

def source():
	return say("You can view my source at http://github.com/raylu/mpu/ or the original at http://github.com/xiongchiamiov/mpu/")

def report(userFrom, message):
	global users

	# FIXME
	# some magic to determine if owner is online
	#if(True):
	#	server.privmsg(owner, userFrom+" has something to say: "+message)
	#	return True
	#else:
	#	# log it to a file
	#	logFile = open('MPU.log', 'a')
	#	return logFile.write(userFrom+" had something to say: "+message+"\n") and logFile.close()

	# temporary while I determine what magic to use above
	server.privmsg(users['owner'], userFrom+" has something to say: "+message)
	logFile = open('MPU.log', 'a')
	return logFile.write(strftime("%Y-%m-%d %H:%M:%S")+" -- "+userFrom+" had something to say: "+message+"\n") and logFile.close()

def kill(userFrom):
	global users

	if userFrom == users['owner']:
		logFile = open('MPU.log', 'a')
		logFile.write(strftime("%Y-%m-%d %H:%M:%S")+" -- "+"Got killed!\n")
		server.disconnect()
		sys.exit()
	else:
		say("You can kill a man, but you can't kill an idea manifested in Python.")

def gag():
	global gagged
	gagged = True
	return True

def ungag():
	global gagged
	gagged = False
	return True

def info(command):
	global userData
	split = command.split()

	if (len(split)==0):
		handleFlags['help'](None, 'info')
		return True

	user = split[0]

	if (len(split)<2):
		output = "I have the following information on "+user+": "
		try:
			for info in sorted(userData[user].keys()):
				output += info+", "
			# trim off the extra comma at the end
			output = output[0:-2]
		except:
			pass
		say(output)
	else:
		output = "Here's your requested info on "+user+": "
		infos = split[1:]
		for info in infos:
			try:
				output += info+": "+userData[user][info]+", "
			except KeyError:
				output += info+": No info, "

		# trim off the extra comma at the end
		output = output[0:-2]

		say(output)
	return True

def infoset(userFrom, command):
	global userData
	global userDataFile
	global files

	split = command.split()
	info = split[0]
	try:
		data = ' '.join(split[1:])
	except:
		data = ''
	
	try:
		userData[userFrom][info] = data
	except:
		userData[userFrom] = {}
		userData[userFrom][info] = data
	
	# pickle userData
	pickleFile = open(files['userData'], 'w')
	pickle.dump(userData, pickleFile)
	pickleFile.close()

	say("Field "+info+" updated.")

def changelog(command):
	if command and re.match('^[\w\d "]+$', command):
		output = commands.getstatusoutput('git --no-pager log --pretty=format:%%s --since=%s' % command)
	else:
		output = commands.getstatusoutput('git --no-pager log --pretty=format:%s -1')
	if output[0] or (command and not re.match('^[\w\d "]+$', command)):
		help('changelog')
		return False
	else:
		for summary in output[1].split('\n'):
			say(summary)
	return True

def whatis(userFrom, command):
	# are we recording new information?
	if command[:4] == 'set ':
		return whatis_set(userFrom, command[4:])

	global jeeves

	if command.lower() in jeeves:
		say(command+": "+jeeves[command.lower()])
		return True
	else:
		say("I don't know nothin' 'bout "+command)
		return False

def whatis_set(userFrom, definition):
	global users
	global jeeves
	global files

	if userFrom in users['cabal']:
		command = definition.split()[0].lower()
		definition = definition[len(command)+1:]

		if definition:
			jeeves[command] = definition
			say("New definition for "+command+" set.")
		else:
			del jeeves[command]
			say("Definition unset for "+command+".")

		# pickle jeeves
		pickleFile = open(files['jeeves'], 'w')
		pickle.dump(jeeves, pickleFile)
		pickleFile.close()

		return True
	else:
		say("I'm sorry, but I don't trust you.  Y'know, the darting eyes and all.")
		return False

def usermod(userFrom, command):
	global users
	global files

	if userFrom in users['owner']:
		try:
			mod = command.split()[0]
			usersToMod = command.split()[1:]
			if not usersToMod:
				say("Members of "+mod+": "+', '.join(users[mod]))
				return False
		except:
			say("Available userlists: "+', '.join(users.keys()))
			return False

		if mod in users.keys():
			for user in usersToMod:
				if user in users[mod]:
					users[mod].remove(user)
					say(user+" is no longer a member of "+mod)
				else:
					users[mod].append(user)
					say(user+" is now a member of "+mod)
			# pickles users
			pickleFile = open(files['users'], 'w')
			pickle.dump(users, pickleFile)
			pickleFile.close()

			return True
		else:
			say("Available userlists: "+', '.join(users.keys()))
			return False
	else:
		say("I'm sorry, but I don't trust you.  Y'know, the darting eyes and all.")
		return False

def fortune(userFrom, command):
	output = commands.getstatusoutput('fortune -sa')
	for summary in output[1].split('\n'):
		say(summary.replace('\t', '  '))

def limerick(userFrom, command):
	output = commands.getstatusoutput('fortune /usr/share/fortune/off/limerick')
	for summary in output[1].split('\n'):
		say(summary.replace('\t', '  '))

def stuff(userFrom, command):
	if userFrom not in lastmessage or lastmessage[userFrom].count(trigger + 'stuff') == 1:
		if (userFrom.startswith('Chiyachan')):
			imoutos = 'over 9000 imoutos.'
		else:
			imoutos = random.randint(0, 10)
			if (imoutos == 1):
				imoutos = 'a imouto.'
			else:
				imoutos = str(imoutos) + ' imoutos.'
		action('gives ' + userFrom + ' ' + imoutos)

def ratio(userFrom, command):
	user = userFrom
	if len(command) > 0:
		user = command
	try:
		req = urllib2.Request('http://www.bakabt.com/users.php?search=' + user)
		req.add_header('Cookie', 'uid=498909;pass=01625f5744266125386aea6b77118f8b')
		html = urllib2.urlopen(req).read()
		start = html.find('href="user/') + 6
		end = html.find('">', start)
		req = urllib2.Request('http://www.bakabt.com/' + html[start:end])
		html = urllib2.urlopen(req).read()

		start = html.find('Uploaded')
		start = html.find('">', start+8) + 2
		end = html.find(' - ', start+2)
		uploaded = html[start:end]

		start = html.find('Downloaded')
		start = html.find('">', start+10) + 2
		end = html.find(' - ', start+2)
		downloaded = html[start:end]

		start = html.find('Share ratio')
		start = html.find('">', start+11) + 2
		end = html.find('</span>', start+2)
		ratio = html[start:end]

		if ratio == "Inf.":
			color = "13"
		elif ratio == "---":
			color = "05"
		else:
			fratio = float(ratio)
			if fratio < 0.5:
				color = "04"
			elif fratio < 2:
				color = "07"
			else:
				color = "11"
		server.notice(userFrom, user + "'s ratio is \003" + color + ratio + "\003 (" + uploaded + "/" + downloaded+ ")")
	except:
		server.notice(userFrom, 'Search for "'+user+'" failed')

def idle(userFrom, command):
	if len(command) == 0:
		say('Usage: ' + trigger + 'idle username')
		return False

	user = command.strip()
	try:
		delta = datetime.utcnow() - lastaction[user]
		hours = 0
		minutes = 0
		seconds = delta.seconds
		while seconds >= 3600:
			seconds -= 3600
			hours += 1
		while seconds >= 60:
			seconds -=60
			minutes += 1

		strtime = ''
		if delta.days != 0:
			strtime = str(delta.days) + 'd '
		if hours != 0:
			strtime += str(hours) + 'h '
		strtime += str(minutes) + 'm '
		strtime += str(seconds) + 's'

		say(user + ' has been idle for ' + strtime)
	except:
		say(userFrom + ": I haven't seen " + user + " speak.")

## Handle Input
handleFlags = {
	'help':      lambda userFrom, command: help(command),
	'source':    lambda userFrom, command: source(),
	'report':    lambda userFrom, command: report(userFrom, command),
	'kill':      lambda userFrom, command: kill(userFrom),
	'gag':       lambda userFrom, command: gag(),
	'ungag':     lambda userFrom, command: ungag(),
	'info':      lambda userFrom, command: info(command),
	'infoset':   lambda userFrom, command: infoset(userFrom, command),
	'changelog': lambda userFrom, command: changelog(command),
	'whatis':    lambda userFrom, command: whatis(userFrom, command),
	'usermod':   lambda userFrom, command: usermod(userFrom, command),
	'fortune':   lambda userFrom, command: fortune(userFrom, command),
	'limerick':  lambda userFrom, command: limerick(userFrom, command),
	'stuff':     lambda userFrom, command: stuff(userFrom, command),
#	'ratio':     lambda userFrom, command: ratio(userFrom, command),
	'idle':      lambda userFrom, command: idle(userFrom, command),
}

# Treat PMs like public flags, except output is sent back in a PM to the user
def handlePrivateMessage(connection, event):
	# get the user the message came from
	userFrom = event.source().split('!')[0]
	# separate message into flag and rest
	try:
		splitMessage = event.arguments()[0].split()
		flag = splitMessage[0]
		command = splitMessage[1:]
	except:
		flag = even.arguments()[0]
		command = []
	
	# make say() send messages back in PMs
	global channel
	temp = channel
	channel = userFrom
	
	try:
		handleFlags[flag.lower()](userFrom, ' '.join(command))
		channel = temp
	except KeyError:
		handleFlags['help'](userFrom, '')
		channel = temp
	return True

# Take a look at public messages and see if we need to do anything with them
def handlePublicMessage(connection, event):
	# get the user the message came from
	userFrom = event.source().split('!')[0]

	# separate message into flag and rest
	message = event.arguments()[0]
	try:
		splitMessage = message.split()
		flag = splitMessage[0]
		command = splitMessage[1:]
	except:
		flag = message
		command = []
	
	# s/find/replace/
	if (flag[0:2] == 's/'):
		splitMessage = message.split('/')
		if (len(splitMessage) >= 3):
			#if s///username, frUser is username
			#if s// or s///,  frUser is userFrom
			frUser = ''
			if len(splitMessage) == 4:
				frUser = splitMessage[3].strip()
			if frUser == '':
				frUser = userFrom
			try:
				for s in lastmessage[frUser]:
					new_string, n = re.subn(splitMessage[1], splitMessage[2], s)
					if n > 0:
						say(frUser + '> ' + new_string)
						break
			except:
				say(userFrom + ': No messages found from ' + frUser)
		else:
			say(userFrom + ': s/find/replace[/ username]')

	# track lastmessage
	if userFrom in lastmessage:
		if len(lastmessage[userFrom]) > 4:
			lastmessage[userFrom].pop()
		lastmessage[userFrom].insert(0, message)
	else:
		lastmessage[userFrom] = [message]
	#track lastaction
	lastaction[userFrom] = datetime.utcnow()

	#handle commands
	if (flag[0] == trigger):
		try:
			return handleFlags[flag[1:].lower()](userFrom, ' '.join(command))
		except KeyError:
			return True

# Remove people from lastmessage and lastaction
def handlePart(connection, event):
	user = event.source().split('!')[0]
	if user in lastmessage:
		lastmessage.pop(user)
	if user in lastaction:
		lastaction.pop(user)

# Discard lastmessage and move lastaction
def handleNick(connection, event):
	oldnick = event.source().split('!')[0]
	if oldnick in lastmessage:
		lastmessage.pop(oldnick) #because replaces would show the new nick and that'd look weird
	if oldnick in lastaction:
		lastaction[event.target()] = lastaction[oldnick]
		lastaction.pop(oldnick)

# Handle server welcome so we know when to identify with NickServ
def handleWelcome(connection, event):
	server.privmsg('NickServ', 'IDENTIFY ' + password)

# Handle NickServ successes so that we can join +r channels
def handleMode(connection, event):
	if event.target() == nick and '+r' in event.arguments():
		print "NickServ authentication success!"
		server.join(channel)

## Final Setup
# Add handlers
irc.add_global_handler('privmsg', handlePrivateMessage)
irc.add_global_handler('pubmsg',  handlePublicMessage)
irc.add_global_handler('part',    handlePart)
irc.add_global_handler('nick',    handleNick)
irc.add_global_handler('welcome', handleWelcome)
irc.add_global_handler('umode',   handleMode)

# Jump into an infinite loop
while(True):
	try:
		# dictionary to group information about files we need
		files = {}
		irclib.DEBUG = dirty_secrets.debug
		files['userData'] = 'userData.pickle'
		files['jeeves'] = 'jeeves.pickle'
		files['users'] = 'users.pickle'

		# load the pickled files
		for key, file in files.items():
			try:
				pickleFile = open(file, 'r')
				vars()[key] = pickle.load(pickleFile)
				pickleFile.close()
			except:
				vars()[key] = {}

		# add some defaults for users
		users['owner'] = dirty_secrets.owner
		if not 'cabal' in users.keys():
			users['cabal'] = []

		# Create a server object, connect and join the channel
		server = irc.server()
		server.connect(network, port, nick, password=password, ircname=name)

		try:
			irc.process_forever(timeout=10.0)
		except KeyboardInterrupt:
			print "\nCaught ^C, exiting..."
			sys.exit()
	except irclib.ServerNotConnectedError:
		sleep(5)
