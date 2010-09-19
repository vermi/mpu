#!/usr/bin/python2.6

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
from urllib import quote_plus
from datetime import datetime, time, timedelta
import gdata.youtube
import gdata.youtube.service
import json
from htmlentitydefs import name2codepoint as n2cp
import gzip
import os
import stat
import xml.dom.minidom as minidom
import traceback

## Beginning Setup
# Connection information
network = dirty_secrets.network
port = dirty_secrets.port
password = dirty_secrets.password
channel = dirty_secrets.channel
nick = dirty_secrets.nick
name = dirty_secrets.name
trigger = '!'

#ispm = 0
gagged = False
gag_points = 0
gag_time = datetime.utcnow()
gag_lastmessage = ''

lastmessage = { }
lastaction = { }

yt_service = gdata.youtube.service.YouTubeService()
yt_service.developer_key = 'AI39si7bsw0DiAFUUUeG-idPa--w4I2w3SA-IAVMXIkfY7ml0Aw6fP6fN-u248cLyjuWZkFVbxoqV5MdyjA_th4dUD4Y8vvo5A'
google_key = 'ABQIAAAA6-N_jl4ETgtMf2M52JJ_WRQjQjNunkAJHIhTdFoxe8Di7fkkYhRRcys7ZxNbH3MIy_MKKcEO4-9_Ag'

# Create an IRC object
irc = irclib.IRC()

## Methods
def say(message):
	global gag_points, gag_time, gag_lastmessage, gagged, ispm
	gag_points += 5
	gag_points -= (datetime.utcnow() - gag_time).seconds
	if gag_points < 0:
		gag_points = 0
	elif message == gag_lastmessage:
		gag_points *= 2

	if gag_points > 15:
		action("gags himself.")
		gagged = True
	else:
		gagged = False
		ispm = 0
	gag_time = datetime.utcnow()
	gag_lastmessage = message

	if not gagged:
		server.privmsg(channel, message)
		sleep(1)

def action(message):
	if not gagged:
		server.action(channel, message)
		sleep(1)

def log(text):
	text = str(text)
	logFile = open('MPU.log', 'a')
	return logFile.write(strftime("%Y-%m-%d %H:%M:%S") + ": " + text + "\n") and logFile.close()
	print text

def help(command):
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
	elif command=='anidb':
		say("Search for series ID on AniDB. Useful for the aid function.")
		say("Usage: anidb [search string]")
	elif command=='aid':
		say("Get details for a specific series ID from AniDB. Used with the anidb function.")
		say("Usage: aid [id#]")
	elif command=='tr':
		say("Translates a given phrase via Google Translate.")
	elif command=='roman':
		say("Converts a Japanese phrase to romaji via Google Transliterate.")
	elif command=='calc':
		say("A simple calculator from Google. Also does currency and unit conversion.")
	elif command=='roll':
		say("Roll any number of dice of any size. Default is 1d6.")
		say("Example: roll 3d6")
	else:
		say("Available commands: " + (' '.join(sorted(handleFlags.keys()))))
		say("Type 'help [command]' to get more info about command. I also respond to PMs; just remember you don't need ! in front of the command.")
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
	return log(userFrom + " had something to say: " + message)

def kill(userFrom):
	global users

	if userFrom == users['owner']:
		log("Got killed!")
		server.disconnect()
		sys.exit()
	else:
		say("You can kill a man, but you can't kill an idea manifested in Python.")

def gag():
	global gagged, gag_points
	gagged = True
	gag_points = 300
	return True

def ungag():
	global gagged, gag_points
	gagged = False
	gag_points = 10
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
	try:
		info = split[0]
	except:
		help('infoset')
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
		imoutos = random.randint(0, 10)
		if (imoutos == 1):
			imoutos = 'an imouto.'
		else:
			imoutos = str(imoutos) + ' imoutos.'
		action('gives ' + userFrom + ' ' + imoutos)

def ratio(userFrom, command):
	user = userFrom
	if len(command) > 0:
		user = command
	try:
		req = urllib2.Request('http://www.bakabt.com/users.php?search=' + user)
		req.add_header('Cookie', 'uid=498909;pass=')
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

def chnick(userFrom, command):
	if userFrom == users['owner'] and len(command) > 0:
		server.nick(command)

def qdb(userFrom, command):
	try:
		if len(command) > 0 and command.isdigit():
			html = urllib2.urlopen('http://www.chalamius.se/quotes/api/json/quote/' + command)
			quote = json.load(html)
			content = quote['content'].replace('\r\n', ' ')
			content = decode_htmlentities(content).encode('utf-8')
			if len(content) < 450: # actual limit is 512, but that is the raw line
				say(content)
			else:
				say('http://www.chalamius.se/quotes/?p=quote&id=' + command)
		else:
			while True:
				html = urllib2.urlopen('http://www.chalamius.se/quotes/api/json/random')
				quote = json.load(html)
				content = quote['content'].replace('\r\n', ' ')
				content = decode_htmlentities(content).encode('utf-8')
				if len(content) < 450:
					break
			say(quote['id'] + ': ' + content)
	except:
		say("%s: Error while retrieving quote." % userFrom)

def substitute_entity(match):
	ent = match.group(3)

	if match.group(1) == "#":
		if match.group(2) == '':
			return unichr(int(ent))
		elif match.group(2) == 'x':
			return unichr(int('0x'+ent, 16))
	else:
		cp = n2cp.get(ent)

		if cp:
			return unichr(cp)
		else:
			return match.group()

def decode_htmlentities(string):
	entity_re = re.compile(r'&(#?)(x?)(\w+);')
	return entity_re.subn(substitute_entity, string)[0]

def translate(userFrom, command):
	langpairs = ''
	while True:
		split = command.split(' ', 1)
		if len(split) == 2 and len(split[0]) == 5 and split[0][2] == '|':
			langpairs += '&langpair=' + split[0]
			command = split[1]
		else:
			break

	try:
		q = quote_plus(command)
		if len(langpairs) > 0:
			requrl = "http://ajax.googleapis.com/ajax/services/language/translate?v=1.0&q=%s%s&key=%s" % (q, langpairs, google_key)
			req = urllib2.Request(requrl)
			req.add_header('Referer', 'http://raylu.eth24.net/')
			response = urllib2.urlopen(req)
			tr = json.load(response)
			say_response(tr)
		else:
			requrl = "http://ajax.googleapis.com/ajax/services/language/detect?v=1.0&q=%s&key=%s" % (q, google_key)
			req = urllib2.Request(requrl)
			req.add_header('Referer', 'http://raylu.eth24.net/')
			response = urllib2.urlopen(req)
			tr = json.load(response)
			tr = tr['responseData']
			say("Language: %s, Reliable: %s, Confidence: %f" % (tr['language'], tr['isReliable'], tr['confidence']))
	except:
		say(userFrom + ': Error while translating.')

def say_response(tr):
	if 'responseStatus' in tr:
		if tr['responseStatus'] != 200:
			say(tr['responseDetails'])
	if 'responseData' in tr:
		say_response(tr['responseData'])
	elif 'translatedText' in tr:
		tr_text = tr['translatedText'].encode('utf-8')
		say(tr_text)
	else:
		for r in tr:
			say_response(r)

def transliterate(userFrom, command):
	if len(command) == 0:
		return
	try:
		q = quote_plus(command)
		req = urllib2.Request('http://translate.google.com/translate_a/t?client=t&hl=ja&sl=ja&tl=en-U&text=' + q)
		req.add_header('User-agent', 'Mozilla/5.0')
		response = urllib2.urlopen(req)
		tr = response.read().split('"', 6)[5]
		say(tr)
	except Exception as e:
		say(userFrom + ': Error while transliterating from Japanese.')
		print e

def calc(userFrom, command):
	if len(command) > 0:
		try:
			q = quote_plus(command)
			requrl = "http://www.google.com/ig/calculator?hl=en&q=%s&key=%s" % (q, google_key)
			req = urllib2.Request(requrl)
			req.add_header('Referer', 'http://raylu.eth24.net/')
			response = urllib2.urlopen(req).read()

			match = re.match('{lhs: "(.*)",rhs: "(.*)",error: "(.*)",icc: (true|false)}', response)
			if match == None or match.group(3) != '':
				say(userFrom + ': Error while calculating.')
			else:
				say("%s = %s" % (match.group(1), match.group(2)))
		except:
			say(userFrom + ': Error while calculating.')

def anidb(userFrom, command):
	try:
		atime = datetime.fromtimestamp(os.stat('animetitles.dat')[stat.ST_MTIME])
		d = datetime.now() - atime
		if d > timedelta(0, 0, 0, 0, 0, 12, 0):
			update_anidb()
	except OSError:
		update_anidb()

	if len(command) < 2:
		return
	regex = re.compile(command, re.IGNORECASE)
	aid = [ ]

	anidb_file = open('animetitles.dat', 'r')
	for line in anidb_file:
		if line[0] != '#':
			split = line.split('|')
			if split[1] != '3' and regex.search(split[3]) and split[0] not in aid:
				aid.append(split[0])

	if len(aid) > 0 and len(aid) < 16:
		anidb_file.seek(0, 0)
		aid_text = [ ]
		for line in anidb_file:
			if line[0] != '#':
				split = line.split('|')
				if split[1] == '1' and split[0] in aid:
					aid_text.append(split[0] + '|' + split[3][:-1])
		say(', '.join(aid_text))
	elif len(aid) == 0:
		say(userFrom + ': No search results.')
	else:
		say(userFrom + ': Too many search results.')
	anidb_file.close()

def update_anidb():
	try:
		say("Updating anidb titles...")
		gzdata = urllib2.urlopen('http://anidb.net/api/animetitles.dat.gz')
		anidbgz_file = open('animetitles.dat.gz', 'wb')
		anidbgz_file.write(gzdata.read())
		anidbgz_file.close()
		anidb_file = open('animetitles.dat', 'wb')
		anidbgz_file = gzip.open('animetitles.dat.gz', 'rb')
		anidb_file.write(anidbgz_file.read())
		anidbgz_file.close()
		anidb_file.close()
		os.remove('animetitles.dat.gz')
	except:
		say("Error while updating anidb titles.")

def aid(userFrom, command):
	if command.isdigit():
		aid = command
	else:
		return
	if not os.path.isdir('anidb'):
		os.mkdir('anidb')
	a_file = "anidb/%s.xml.gz" % aid
	try:
		atime = datetime.fromtimestamp(os.stat(a_file)[stat.ST_MTIME])
		d = datetime.now() - atime
		if d > timedelta(0, 0, 0, 0, 0, 24, 0):
			get_anidb(aid)
	except OSError:
		get_anidb(aid)

	try:
		xml_file = gzip.open(a_file)
		dom = minidom.parse(xml_file)

		titles = [ ]
		anime = dom.getElementsByTagName('anime')[0]
		for node in anime.getElementsByTagName('title'):
			tlang = node.getAttribute('xml:lang')
			ttype = node.getAttribute('type')
			if (tlang == 'x-jat' and ttype == 'main') or (ttype == 'official' and tlang in ('ja', 'en')):
				titles.append(node.firstChild.nodeValue.encode('utf-8'))
		server.notice(userFrom, "%s: %s" % (aid, ', '.join(titles)))

		stype = get_xml_value(dom, 'type')
		episodes = get_xml_value(dom, 'episodecount')
		startdate = get_xml_value(dom, 'startdate')
		enddate = get_xml_value(dom, 'enddate')
		server.notice(userFrom, "%s, %s episodes, %s - %s" % (stype, episodes, startdate, enddate))

		relatedanime = dom.getElementsByTagName('relatedanime')
		if len(relatedanime) > 0:
			related = [ ]
			typelen = 0
			for node in relatedanime[0].getElementsByTagName('anime'):
				raid = node.getAttribute('id')
				rtype = node.getAttribute('type')
				rtitle = node.firstChild.nodeValue
				related.append((rtype, "%s|%s" % (raid, rtitle)))
				if len(rtype) > typelen :
					typelen = len(rtype)
			for a in related:
				server.notice(userFrom, ("%" + str(typelen) + "s: %s") % a)

		server.notice(userFrom, 'http://anidb.net/perl-bin/animedb.pl?show=anime&aid=' + aid)
	except:
		say("Error while reading data for aid %s." % aid)

def get_xml_value(dom, tag):
	return dom.getElementsByTagName(tag)[0].firstChild.nodeValue

def get_anidb(aid):
	try:
		xml = urllib2.urlopen('http://api.anidb.net:9001/httpapi?request=anime&client=mpuboth&clientver=1&protover=1&aid=' + aid)
		xml_file = open("anidb/%s.xml.gz" % aid, 'wb')
		xml_file.write(xml.read())
		xml_file.close()
	except:
		say("Error while getting aid %s." % aid)

def roll(userFrom, command):
	dice = 1
	size = 6

	split = command.split('d', 1)
	try:
		if len(split) == 2:
			dice = int(split[0])
			if dice > 10:
				dice = 10
			size = int(split[1])
			if size > 20:
				size = 20
	except:
		say("Check your syntax.")
		return

	say("Rolling %sd%s. Max is 10d20." % (dice, size))
	result = [random.randint(1, size) for i in range(dice)]

	if dice == 1:
		say("%s> %s" % (userFrom, ' '.join(str(i) for i in result)))
	else:
		total = sum(result)
		say("%s> %s, for a total of: %s" % (userFrom, ' '.join(str(i) for i in result), total))

## Handle Input
handleFlags = {
	'help':      lambda userFrom, command: help(command),
	'source':    lambda userFrom, command: source(),
	'report':    lambda userFrom, command: report(userFrom, command),
	'kill':      lambda userFrom, command: kill(userFrom),
	'gag':       lambda userFrom, command: gag(),
	'ungag':     lambda userFrom, command: ungag(),
#	'info':      lambda userFrom, command: info(command),
#	'infoset':   lambda userFrom, command: infoset(userFrom, command),
	'changelog': lambda userFrom, command: changelog(command),
	'whatis':    lambda userFrom, command: whatis(userFrom, command),
	'usermod':   lambda userFrom, command: usermod(userFrom, command),
	'fortune':   lambda userFrom, command: fortune(userFrom, command),
	'limerick':  lambda userFrom, command: limerick(userFrom, command),
	'stuff':     lambda userFrom, command: stuff(userFrom, command),
#	'ratio':     lambda userFrom, command: ratio(userFrom, command),
	'idle':      lambda userFrom, command: idle(userFrom, command),
	'nick':      lambda userFrom, command: chnick(userFrom, command),
	'qdb':       lambda userFrom, command: qdb(userFrom, command),
	'tr':        lambda userFrom, command: translate(userFrom, command),
	'roman':     lambda userFrom, command: transliterate(userFrom, command),
	'calc':      lambda userFrom, command: calc(userFrom, command),
	'anidb':     lambda userFrom, command: anidb(userFrom, command),
	'aid':       lambda userFrom, command: aid(userFrom, command),
	'roll':      lambda userFrom, command: roll(userFrom, command),
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
	#global ispm
	temp = channel
	channel = userFrom

	try:
		handleFlags[flag.lower()](userFrom, ' '.join(command))
		channel = temp
		#ispm = 1
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
				say(userFrom + ': regex error.')
		else:
			say(userFrom + ': s/find/replace[/ username]')

	# track lastmessage
	if userFrom in lastmessage:
		if len(lastmessage[userFrom]) > 4:
			lastmessage[userFrom].pop()
		lastmessage[userFrom].insert(0, message)
	else:
		lastmessage[userFrom] = [message]
	# track lastaction
	lastaction[userFrom] = datetime.utcnow()

	# handle youtube
	vid = ''
	if flag[0:31] == 'http://www.youtube.com/watch?v=':
		vid = flag[31:]
	if flag[0:27] == 'http://youtube.com/watch?v=':
		vid = flag[27:]
	if vid != '':
		try:
			amp = vid.find('&')
			if amp != -1:
				vid = vid[0:amp]
			entry = yt_service.GetYouTubeVideoEntry(video_id=vid)

			seconds = long(entry.media.duration.seconds)
			minutes, seconds = divmod(seconds, 60)
			hours, minutes = divmod(minutes, 60)
			duration = '%02d:%02d' % (minutes, seconds)
			if hours > 0:
				duration = '%s:%s' % (hours, duration)

			say("%s's video: %s, %s" % (userFrom, entry.media.title.text, duration))
		except:
			pass

	# handle commands
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
		lastaction[event.target()] = datetime.utcnow()
		lastaction.pop(oldnick)

# Handle server welcome so we know when to identify with NickServ
def handleWelcome(connection, event):
	if len(password) > 0:
		server.privmsg('NickServ', 'IDENTIFY ' + password)

# Handle NickServ successes so that we can join +r channels
def handleMode(connection, event):
	if (event.target() == nick and '+r' in event.arguments()) or len(password) == 0:
		server.join(channel)

def handleCTCP(connection, event):
	if event.arguments()[0] == 'ACTION':
		text = event.arguments()[1]
		match = re.match('gives (\S+) ([0-9]+) lolis?, ([0-9]+) onee-chans?, ([0-9]+) lions? and ([0-9]+) imoutos?', text)
		if match != None:
			glomp = 'everything'
			if match.group(2) != '0':
				glomp = 'a loli'
			elif match.group(3) != '0':
				glomp = 'an onee-chan'
			elif match.group(4) != '0':
				glomp = 'a lion'
			elif match.group(5) != '0':
				glomp = 'an imouto'
			action('glomps ' + glomp)
	elif event.arguments()[0] == 'VERSION':
		server.ctcp_reply(event.source().split('!')[0], 'VERSION MPU (http://github.com/vermi/mpu/)')

	lastaction[event.source().split('!')[0]] = datetime.utcnow()

## Final Setup
# Add handlers
irc.add_global_handler('privmsg', handlePrivateMessage)
irc.add_global_handler('pubmsg',  handlePublicMessage)
irc.add_global_handler('part',    handlePart)
irc.add_global_handler('nick',    handleNick)
irc.add_global_handler('welcome', handleWelcome)
irc.add_global_handler('umode',   handleMode)
irc.add_global_handler('ctcp',    handleCTCP)

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

# Jump into an infinite loop
while True:
	try:
		# Create a server object, connect and join the channel
		server = irc.server()
		server.connect(network, port, nick, password=password, ircname=name, ssl=dirty_secrets.ssl)

		irc.process_forever(timeout=15.0)
	except KeyboardInterrupt:
		print "\nCaught ^C, exiting..."
		sys.exit()
	except Exception:
		log(traceback.format_exc(10))
		irc.disconnect_all()
	sleep(5)
