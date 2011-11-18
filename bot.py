# IMAG CHAT BOT BY Guillaume
# V1.121111

# -*- coding: iso-8859-15 -*-
import subprocess, httplib, urllib, base64, random, shlex, time, sys, re

#
# GLOBAL VARS
#

# For debugging purpose
DEBUG = True
# Default parameters
BOT_NAME = "BOT"
# Log filename
LOG_FILE = "imagchat.log"
# Some URLs
URL = "www.philaeux.ns5-wistee.fr:80"
URL_CHAT = "/imag/index.php?pfc_ajax=1&f=loadChat"



# General HTTP headers
headers_get = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}
headers_post = {}
# Root users
root_users = set()
# Challenges used
challs_used = set()
challs_allowed = set()
# Timers
starttime = 0
lastcmd = 0
# General channel parameters
nick_id = ""
client_id = ""
channel_id = ""
# PHP session ID
session_id = ""
# For bullshit speaking feature
speak_enabled = False

#
# LOCAL FUNCTIONS
#

def get_param(regex, data):
	# Do regex
	matches = re.search(regex, data)
	if matches:
		return matches.group(2)
	else:
		print "[!] ERROR: connect_to_server"
		sys.exit(1)

def get_session_id(headers):
	for subtab in headers:
		# Get cookie
		if subtab[0] == "set-cookie":
			return re.search(r"(.*);", subtab[1]).groups()[0]
		
	print "[!] ERROR: get_session_id"
	sys.exit(1)

def connect_to_server():
	server_params = ""
	conn = httplib.HTTPConnection(URL)
	# Get it!
	conn.request("GET", "/imag/", "", headers_get)
	# Get informations
	res = conn.getresponse()
	server_params = res.read()
	# Retrieve PHP session ID
	global session_id
	session_id = get_session_id(res.getheaders())
	conn.close()
	# Parse parameters
	global nick_id
	global client_id
	nick_id = get_param(r"pfc_nickid(\s)+=\s\"(.*)\";", server_params)
	client_id = get_param(r"pfc_clientid(\s)+=\s\"(.*)\";", server_params)
	if DEBUG:
		print "[*] NICKID:    ", nick_id
		print "[*] CLIENTID:  ", client_id

def connect_to_channel():
	global session_id
	conn = httplib.HTTPConnection(URL)
	# Build 'CONNECT' POST request
	params_post = "pfc_ajax=1&f=handleRequest&cmd=%2Fconnect%20" + client_id + "%200%20%22" + BOT_NAME + "%22"
	# Build headers!
	global headers_post
	headers_post = {"Accept": "text/javascript, text/html, application/xml, text/xml, */*",
					"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
					"Cookie": session_id,
					# AJAX bullshit
					"X-Requested-With": "XMLHttpRequest",
					"X-Prototype-Version": "1.6.0.2"}
	# Post it!
	conn.request("POST", "/imag/index.php?pfc_ajax=1&f=loadChat", params_post, headers_post)
	# Get informations
	res = conn.getresponse()
	channel_params = res.read()
	# Retrieve channel ID
	global channel_id
	try:
		channel_id = re.search(r"Array\(\'(.*)\',", channel_params).groups()[0]
	except AttributeError:
		print "[!] ERROR: connect_to_channel"
		sys.exit(1)
	if DEBUG:
		print "[*] CHANNELID: ", channel_id
	conn.close()

def parse_commands(user, msg):
	args = msg.split()
	
	# HELP
	if args[0].lower() == "help":
		# Print help menu
		write_channel(" 0= random <int> <int>"); 	time.sleep(0.5)
		write_channel(" 0= speak <yes/no>"); 		time.sleep(0.5)
		write_channel(" 0= lol <vdm>"); 			time.sleep(0.5)
		write_channel(" 0= sudome"); 				time.sleep(0.5)
		write_channel(" 0= finger"); 				time.sleep(0.5)
		write_channel(" 0= uptime"); 				time.sleep(0.5)
	# SPEAK
	elif args[0].lower() == "speak":
		try:
			assert(len(args) > 1)
			global speak_enabled
			# Enable/disable?
			speak_enabled = args[1].lower() == "yes"
			if speak_enabled:
				write_channel("[*] BULLSHIT ENABLED")
			else:
				write_channel("[*] BULLSHIT DISABLED")
		except AssertError:
			write_channel("[*] COMMAND ERROR!")
			return
	# BN
	elif args[0].lower() == "bn":
		write_channel(BOT_NAME + " VOUS SOUHAITE UNE BONNE NUIT!")
	# VDM
	elif args[0].lower() == "lol":
		try:
			assert(len(args) > 1)
			conn = httplib.HTTPConnection("www.viedemerde.fr")
			# Get random VDM
			conn.request("GET", "/aleatoire")
			data = conn.getresponse().read()
			# Get first VDM
			vdm = re.search("<div class=\"post article\" id=\"(.){6}\">(.*)</div>", data)
			# Parse HTML
			write_channel(re.sub("\(([0-9]*)\)(.*)", "", re.sub("<[^>]+>", "", vdm.group(0))))
			conn.close()
		except AssertionError:
			write_channel("[*] COMMAND ERROR!")
			return
	# PING/PONG
	elif args[0].lower() == "ping":
		write_channel("PONG")
	elif args[0].lower() == "pong":
		write_channel("PING")
	# SUDOME
	elif args[0].lower() == "sudome":
		if len(args) > 1:
			# Challenge response
			chall_res = base64.b64encode(base64.b64encode(args[1]))[0:6]
			if chall_res == args[2] and not (args[1] in challs_used) and (args[1] in challs_allowed):
				write_channel("YOU ARE ROOT :-}")
				# Replay attack protection
				root_users.add(user)
				challs_used.add(args[1])
				challs_allowed.remove(args[1])
			else:
				write_channel(":!: TENTATIVE D'INFRACTION :!:")
		else:
			# Create new challenge
			chall = str(random.randint(42, 1337))
			while chall in challs_used:
				# New one
				chall = str(random.randint(42, 1337))
			# OK
			challs_allowed.add(chall)
			write_channel("CHALLENGE: " + chall)
	# COUNTDOWN
	elif args[0].lower() == "rebours":
		try:
			cpt = int(args[1])
			if cpt > 30:
				write_channel("[*] TROP LONG!")
				return
			# Let's go
			for i in range(0, cpt+1):
				write_channel(str(cpt-i))
				time.sleep(1)
			# Prout!
			write_channel(":$: !BOOM! :$:")
		except ValueError:
			write_channel("[*] COMMAND ERROR!")
			return
	# CADEAU
	elif args[0].lower() == "cadeau":
		# Funny URLs
		write_channel("http://youporn.com"); 		time.sleep(0.5)
		write_channel("http://redtube.com"); 		time.sleep(0.5)
	# UPTIME
	elif args[0].lower() == "uptime":
		uptime = time.time() - starttime
		# Format string
		str_uptime = "%.2u jours, %.2u heures et %.2u minutes" % ((uptime/(24*60*60)), ((uptime%(24*60*60))/(60*60)), ((uptime%(60*60))/60))
		write_channel(str_uptime)
		# MENTOR
	elif args[0].lower() == "mentor":
		# Joke!
		write_channel("My mentor is G")
	# FINGER
	elif args[0].lower() == "finger":
		output = subprocess.Popen(["finger"], stdout=subprocess.PIPE).communicate()
		output_lines = output[0].split('\n')
		# Print line by line
		for line in output_lines:
			write_channel(line)
			time.sleep(1.5)
	# RANDOM
	elif args[0].lower() == "random":
		# Default range
		start = 0
		end = 10
		try:
			# Random range
			if len(args) > 2:
				start = int(args[1])
				end = int(args[2])
			elif len(args) > 1:
				end = int(args[1])
			# Check start < end
			assert(start < end)
		except (ValueError, AssertionError):
			write_channel("[*] COMMAND ERROR!")
			return
		r = random.randint(start, end)
		# Send random
		write_channel("RANDOM(" + str(start) + "," + str(end) + "): " + str(r))
	# Update cmd timer
	global lastcmd
	lastcmd = time.time()
	
def read_channel():
	conn = httplib.HTTPConnection(URL)
	# Build 'UPDATE' POST request
	params_post = "pfc_ajax=1&f=handleRequest&cmd=%2Fupdate%20" + client_id + "%20" + channel_id + "%20"
	# Post it!
	conn.request("POST", URL_CHAT, params_post, headers_post)
	# Get informations
	res = conn.getresponse()
	refresh_notification = res.read()
	# Get message(s) from user(s)
	msg_notification = re.search(r"'getnewmsg'(.*)", refresh_notification)
	if msg_notification:
		# New message(s)!
		try:
			user = re.search(":..\",\"(.*)\",\"" + channel_id + "\"", msg_notification.groups()[0]).groups()[0]
			msg = re.search("\"" + channel_id + "\",\"send\",\"(.*)\"", msg_notification.groups()[0]).groups()[0]
			if DEBUG:
				print user, ": ", msg
			# Log
			subprocess.call(["echo", "\"" + msg + "\" >> $HOME/" + LOG_FILE])
			# Joke
			if "G" in msg:
				write_channel(":$: Parle pas de G comme ça connard! :$:")
				time.sleep(1)
			# Parse commands if necessary
			elif msg.startswith("-bot "):
				# Anti-kick protection
				global lastcmd
				if (time.time() - lastcmd) > 3:
					parse_commands(user, msg[5:len(msg)])
				else:
					time.sleep(2)
					write_channel(":!: ANTI-KICK PROTECTION :!:")
		except AttributeError:
			# CRADE! (Erreur de parsing non geree...)
			None
	conn.close()

def write_channel(msg):
	conn = httplib.HTTPConnection(URL)
	# Bullshit
	msg_formatted = urllib.quote(msg.replace("&quot;", "\""))
	# Build 'UPDATE' POST request
	params_post = "pfc_ajax=1&f=handleRequest&cmd=%2Fsend%20" + client_id + "%20" + channel_id + "%20" + msg_formatted
	# Post it!
	conn.request("POST", URL_CHAT, params_post, headers_post)
	conn.close()

#
# BOT MAIN FUNCTION
#
if len(sys.argv) > 1:
	BOT_NAME = sys.argv[1]

connect_to_server()
connect_to_channel()

# Say hello
# write_channel(">>> BOT IS NOW WATCHING YOU <<<")

starttime = time.time()
loltime = time.time() + random.randint(15*60, 45*60)
# Refresh each second
while True:
	read_channel()
	time.sleep(1)
	# Check loltime
	if loltime <= time.time():
		loltime = time.time() + random.randint(15*60, 45*60)
		# Do lol
		lolstr = {
			0: "MY MENTOR IS AWESOME",
			1: "U MAD?",
			2: "PROBLEM?",
			3: "GCC SUXXX",
			4: "I'M OBAMA, AND YOU ARE AWESOME!"
			}
		if speak_enabled:
			write_channel(">>> " + lolstr.get(random.randint(0,4)) + " <<<")
