import daemon
import requests
import json
import os.path
import time
import sys,getopt
from signal import signal, SIGTERM
import atexit
# from AppKit import *
# from PyObjCTools import AppHelper
from urlparse import urlparse
from blinkstick import blinkstick
from pync import Notifier
import Quartz

def extractAuthURL(str):
	start = str.find('MsRtcOAuth');
	q1 = str.find('"',start);
	q2 = str.find('"',q1+1);
	if q1 == -1 or q2 == -1:
		raise Exception("cannot find auth string")
	return str[q1+1:q2]


def getToken(verbose = False, sip_domain = "", username = "", password = ""):
	discover_url = "https://LyncDiscoverInternal.{0}/".format(sip_domain)
	if verbose:
		print "--1. GET: {0}".format(discover_url);
	r1 = requests.get(discover_url)
	if verbose:
		print "--Response Code: {0}".format(r1.status_code)
	j = r1.json();
	user_url = j['_links']['user']['href']

	#
	# ping the user url, expect a 401/address of oath server
	#
	if verbose:
		print "--2. GET: {0}".format(user_url);
	r2 = requests.get(user_url);

	if verbose:
		print "--Response Code: {0}".format(r2.status_code)
	auth_url = extractAuthURL(r2.headers['www-authenticate'])

	#
	# send auth request, expect 200/authentication token
	#
	r3_data = {'grant_type':'password', 'username':username,'password':password}
	if verbose:
		print "--3. POST: {0}".format(auth_url)
	r3 = requests.post(auth_url,data=r3_data)
	if verbose:
		print "--Response Code: {0}".format(r3.status_code)
	access_token = r3.json()

	#
	# resend user request w/ oath headers, look for applications url
	#
	auth_headers = {'Authorization':"{0} {1}".format(access_token['token_type'],access_token['access_token'])}
	if verbose:
		print "--4. GET: {0}".format(user_url)
	r4 = requests.get(user_url,headers=auth_headers)
	if verbose:
		print "--Response Code: {0}".format(r4.status_code)
	#print json.dumps(r4.json(),indent=4)

	#
	# create an application endpoint, takes a json query w/ app identifier and appropriate content type
	#
	application_data = {'culture':'en-us','endpointId':'1235637','userAgent':'pythonApp/1.0 (CritterOS)'}
	applications_url=r4.json()['_links']['applications']['href']
	if verbose:
		print "--5. GET: {0}".format(applications_url)
	r5_headers = {'content-type': 'application/json'}
	r5_headers.update(auth_headers)
	r5 = requests.post(applications_url,headers=r5_headers,data=json.dumps(application_data))
	if verbose:
		print "--Response Code: {0}".format(r5.status_code)
	apps = r5.json()
	#print json.dumps(r5.json(),indent=4)
	up = urlparse(applications_url)
	application_base = "{0}://{1}".format(up.scheme,up.netloc)

	r6_url = application_base + apps['_links']['self']['href'] + "/people/" + username + "/presence"

	return auth_headers, r6_url

class Blinkstrip(blinkstick.BlinkStickPro):

	def setStatus(self, status):
		# self.set_mode(2)

		r = 0
		g = 0
		b = 0

		if status == "Online":
			g = 255

		elif status == "Busy" or status == "DoNotDisturb":
			r = 255

		elif status == "BeRightBack" or status == "Away":
			r = 255
			g = 255

		if status == "DoNotDisturb":

			t_end = time.time() + 10
			while time.time() < t_end:
				for x in range(self.r_led_count):
					self.set_color(0, x, 0, 0, 0)
				self.send_data(0)
				time.sleep(300/1000.0)

				for x in range(self.r_led_count):
					self.set_color(0, x, r, g, b)
				self.send_data(0)

				time.sleep(700/1000.0)

		elif status == "BeRightBack":
			for x in range(self.r_led_count):
				self.set_color(0, x, 0, 0, 0)
			self.send_data(0)

			for x in range(self.r_led_count):
				self.set_color(0, x, r, g, b)
				self.send_data(0)
				time.sleep(400/1000.0 )
				self.set_color(0, x, 0, 0, 0)
				self.send_data(0)

		elif status == "Deploy":

			for y in range(0, 9, 3):
				self.off()
				for x in range(y, (y+3)):
					if (y == 3):
						self.set_color(0, x, 255, 0, 0)
					else:
						self.set_color(0, x, 0, 0, 255)
				self.send_data(0)
				time.sleep(100/1000.0 )
		elif status == "Off":
			self.off()
		else:
			for x in range(self.r_led_count):
				self.set_color(0, x, r,g,b)
			self.send_data(0)
			time.sleep(700/1000.0)


def cleanup(strip):
	strip.off()

def main(argv, config):
	opts, args = getopt.getopt(argv,"hdv")
	verbose = False
	for opt, arg in opts:
		if opt == '-v':
			verbose = True

	blinkstrip = Blinkstrip(r_led_count=9, max_rgb_value=240)
	if blinkstrip.connect():
		auth_token_headers, url = getToken(verbose = verbose, sip_domain = config['sip_domain'], username = config['username'], password = config['password'])
		if verbose:
			print "--6. GET: {0}".format(url)

		try:
			print 'Press Ctrl-C to quit.'
			prev = ""
			while True:
				d=Quartz.CGSessionCopyCurrentDictionary()
				if d and d.get("CGSSessionScreenIsLocked", 0) == 0 and d.get("kCGSSessionOnConsoleKey", 0) == 1:
					#print "--6. GET: {0}".format(url)
					r6 = requests.get(url,headers=auth_token_headers)
					#print "--Response Code: {0}".format(r6.status_code)
					contact = r6.json()
					# print json.dumps(r6.json(),indent=4)
					if verbose:
						print "{0} status: {1}".format(config['username'], contact['availability'])
					if 'availability' in contact:
						if prev != contact['availability']:
							Notifier.notify(contact['availability'], title='Blinklync')
							prev = contact['availability']
						blinkstrip.setStatus(contact['availability'])
				else:
					blinkstrip.setStatus('BeRightBack')

		except KeyboardInterrupt:
			# print "turn off"
			blinkstrip.off()

		atexit.register(cleanup, blinkstrip)
		# Normal exit when killed
		signal(SIGTERM, lambda signum, stack_frame: exit(1))

	else:
		print "No BlinkSticks found"

if __name__ == "__main__":
	if os.path.isfile('config.json'):
		with open('config.json') as data_file:
			data = json.load(data_file)

			argv = sys.argv[1:]
			opts, args = getopt.getopt(argv,"hdvs")
			for opt, arg in opts:
				if opt == '-h':
					print "usage:\t{0} [-hdvs]\n\t{0} -h\t\tThis help\n\t{0} -d\t\tRun as daemon\n\t{0} -v\t\tVerbose mode\n\t{0} -s Online\tSet status manually, ie. Online, Busy, DoNotDisturb, BeRightBack, Away and Deploy".format(sys.argv[0])
					sys.exit()
				elif opt == '-s':
					blinkstrip = Blinkstrip(r_led_count=9, max_rgb_value=240)
					if blinkstrip.connect():
						try:
							print 'Press Ctrl-C to quit.'
							while True:
								blinkstrip.setStatus(args[0])

						except KeyboardInterrupt:
							# print "turn off"
							blinkstrip.off()
					else:
						print "No BlinkSticks found"
					sys.exit()
				elif opt in ("-d"):
					with daemon.DaemonContext():
						main(argv, config = data)
						sys.exit()

			main(argv, config = data)

	else:
		print "no config file found"
		sys.exit()




