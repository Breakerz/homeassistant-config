#!/usr/bin/python

# Create By Brad Goodman
# http://www.bradgoodman.com/
# brad@bradgoodman.com

# Modified by Breakerz

####################### Fill in settings below #######################
# You must have a credentials.yaml file... fill the sample, then rename it
############################ End settings ############################


import urllib3
import json
import datetime
import re
import time
import math
import base64
import time
import sys
import getopt
import stat
import string
import yaml

from enum import Enum

class TotalComfortAction(Enum):
	STATUS = 1
	JSON = 2
	CANCEL = 3
	COOL = 4
	HEAT = 5
	MODE = 6
	FAN = 7

AUTH="https://mytotalconnectcomfort.com/portal"

cookiere=re.compile('\s*([^=]+)\s*=\s*([^;]*)\s*')

def client_cookies(cookiestr,container):
  if not container: container={}
  toks=re.split(';|,',cookiestr)
  for t in toks:
    k=None
    v=None
    m=cookiere.search(t)
    if m:
      k=m.group(1)
      v=m.group(2)
      if (k in ['path','Path','HttpOnly']):
        k=None
        v=None
    if k:
      #print k,v
      container[k]=v
  return container

def export_cookiejar(jar):
  s=""
  for x in jar:
    s+='%s=%s;' % (x,jar[x])
  return s


def execute(action : TotalComfortAction, value = 0, hold_time=1):
    credentials = yaml.load(open('./credentials.yaml'))
    cookiejar=None
    #print
    #print
    #print "Run at ",datetime.datetime.now()
    headers={"Content-Type":"application/x-www-form-urlencoded",
            "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Encoding":"sdch",
            "Host":"mytotalconnectcomfort.com",
            "DNT":"1",
            "Origin":"https://mytotalconnectcomfort.com/portal",
            "User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.95 Safari/537.36"
        }
    conn = urllib3.connection.HTTPSConnection("mytotalconnectcomfort.com")
    conn.request("GET", "/portal/",None,headers)
    r0 = conn.getresponse()
    #print r0.status, r0.reason

    for x in r0.getheaders():
      (n,v) = x
      #print "R0 HEADER",n,v
      if (n.lower() == "set-cookie"):
        cookiejar=client_cookies(v,cookiejar)
    #cookiejar = r0.getheader("Set-Cookie")
    location = r0.getheader("Location")

    retries=5
    params=urllib3.request.urlencode({"timeOffset":"240",
        "UserName":credentials['username'],
        "Password":credentials['password'],
        "RememberMe":"false"})
    #print params
    newcookie=export_cookiejar(cookiejar)
    #print "Cookiejar now",newcookie
    headers={"Content-Type":"application/x-www-form-urlencoded",
            "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Encoding":"sdch",
            "Host":"mytotalconnectcomfort.com",
            "DNT":"1",
            "Origin":"https://mytotalconnectcomfort.com/portal/",
            "Cookie":newcookie,
            "User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.95 Safari/537.36"
        }
    conn = urllib3.connection.HTTPSConnection("mytotalconnectcomfort.com")
    conn.request("POST", "/portal/",params,headers)
    r1 = conn.getresponse()
    #print r1.status, r1.reason

    for x in r1.getheaders():
      (n,v) = x
      #print "GOT2 HEADER",n,v
      if (n.lower() == "set-cookie"):
        cookiejar=client_cookies(v,cookiejar)
    cookie=export_cookiejar(cookiejar)
    #print "Cookiejar now",cookie
    location = r1.getheader("Location")

    if ((location == None) or (r1.status != 302)):
        #raise BaseException("Login fail" )
        print("ErrorNever got redirect on initial login  status={0} {1}".format(r1.status,r1.reason))
        return


   # Skip second query - just go directly to our device_id, rather than letting it
    # redirect us to it.

    code=str(credentials['device_id'])

    t = datetime.datetime.now()
    utc_seconds = (time.mktime(t.timetuple()))
    utc_seconds = int(utc_seconds*1000)
    #print "Code ",code

    location="/portal/Device/CheckDataSession/"+code+"?_="+str(utc_seconds)
    #print "THIRD"
    headers={
            "Accept":"*/*",
            "DNT":"1",
            #"Accept-Encoding":"gzip,deflate,sdch",
            "Accept-Encoding":"plain",
            "Cache-Control":"max-age=0",
            "Accept-Language":"en-US,en,q=0.8",
            "Connection":"keep-alive",
            "Host":"mytotalconnectcomfort.com",
            "Referer":"https://mytotalconnectcomfort.com/portal/",
            "X-Requested-With":"XMLHttpRequest",
            "User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.95 Safari/537.36",
            "Cookie":cookie
        }
    conn = urllib3.connection.HTTPSConnection("mytotalconnectcomfort.com")
    #conn.set_debuglevel(999);
    #print "LOCATION R3 is",location
    conn.request("GET", location,None,headers)
    r3 = conn.getresponse()
    if (r3.status != 200):
      print("Error Didn't get 200 status on R3 status={0} {1}".format(r3.status,r3.reason))
      return


    # Print thermostat information returned

    if (action == TotalComfortAction.STATUS):

        #print r3.status, r3.reason
        rawdata=r3.read()
        j = json.loads(rawdata.decode('utf-8'))
        #print "R3 Dump"
        #print json.dumps(j,indent=2)
        #print json.dumps(j,sort_keys=True,indent=4, separators=(',', ': '))
        #print "Success:",j['success']
        #print "Live",j['deviceLive']
        print("Indoor Temperature:",j['latestData']['uiData']["DispTemperature"])
        print("Indoor Humidity:",j['latestData']['uiData']["IndoorHumidity"])
        print("Cool Setpoint:",j['latestData']['uiData']["CoolSetpoint"])
        print("Heat Setpoint:",j['latestData']['uiData']["HeatSetpoint"])
        print("Hold Until :",j['latestData']['uiData']["TemporaryHoldUntilTime"])
        print("Status Cool:",j['latestData']['uiData']["StatusCool"])
        print("Status Heat:",j['latestData']['uiData']["StatusHeat"])
        print("Status Fan:",j['latestData']['fanData']["fanMode"])

        return

    if (action == TotalComfortAction.JSON):
        rawdata=r3.read()
        j = json.loads(rawdata.decode('utf-8'))
        print(rawdata)
        return j

    headers={
            "Accept":'application/json; q=0.01',
            "DNT":"1",
            "Accept-Encoding":"gzip,deflate,sdch",
            'Content-Type':'application/json; charset=UTF-8',
            "Cache-Control":"max-age=0",
            "Accept-Language":"en-US,en,q=0.8",
            "Connection":"keep-alive",
            "Host":"mytotalconnectcomfort.com",
            "Referer":"https://mytotalconnectcomfort.com/portal/",
            "X-Requested-With":"XMLHttpRequest",
            "User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.95 Safari/537.36",
            'Referer':"/TotalConnectComfort/Device/CheckDataSession/"+code,
            "Cookie":cookie
        }


    # Data structure with data we will send back

    payload = {
        "CoolNextPeriod": None,
        "CoolSetpoint": None,
        "DeviceID": credentials['device_id'],
        "FanMode": None,
        "HeatNextPeriod": None,
        "HeatSetpoint": None,
        "StatusCool": None,
        "StatusHeat": None,
        "SystemSwitch": None
    }


    # Calculate the hold time for cooling/heating

    t = datetime.datetime.now();

    stop_time = ((t.hour+hold_time)%24) * 60 + t.minute
    stop_time = stop_time/15


    # Modify payload based on user input

    if (action == TotalComfortAction.COOL):
      payload["CoolSetpoint"] = value
      print("action=COOL")

    if (action == TotalComfortAction.HEAT):
      payload["HeatSetpoint"] = value
      payload["StatusCool"] = 1
      payload["StatusHeat"] = 1
      payload["HeatNextPeriod"] = stop_time
      print("action=HEAT")

    if (action == TotalComfortAction.MODE):
      payload["SystemSwitch"] = value
      print("action=MODE")
      
    if (action == TotalComfortAction.CANCEL):
      payload["StatusCool"] = 0
      payload["StatusHeat"] = 0
      print("action=CANCEL")

    if (action == TotalComfortAction.FAN):
      payload["FanMode"] = value
      print("action=FAN")

    # Prep and send payload

    location="/portal/Device/SubmitControlScreenChanges"

    rawj=json.dumps(payload)
    print("json post :{0}".format(rawj))
    conn = urllib3.connection.HTTPSConnection("mytotalconnectcomfort.com");
    #conn.set_debuglevel(999);
    #print "R4 will send"

    conn.request("POST", location,rawj,headers)
    r4 = conn.getresponse()
    if (r4.status != 200):
      print("Error Didn't get 200 status on R4 status={0} {1}".format(r4.status,r4.reason))
      return
    else:
        print("Success in configuring thermostat!")
        data = r4.read()
        print(data)
		#print "R4 got 200"

def printUsage():
	print("")
	print("Cooling: -c temperature -t hold_time")
	print("Heating: -h temperature -t hold_time")
	print("Status: -s")
	print("Full Status JSON format : -j")
	print("Cancel: -x")
	print("Fan: -f [0=auto|1=on]")
	print("Mode: -m [0=EmHeat|1=Heat|2=Off|3=Cool]")
	print("")
	print("Example: Set temperature to cool to 80f for 1 hour: \n\t totalcomfort.py -c 80 -t 1")
	print("")
	print("If no -t hold_time is provided, it will default to one hour from command time.")
	print("")


def main():

    if sys.argv[1] == "-s":
        execute(TotalComfortAction.STATUS)
        sys.exit()

    if sys.argv[1] == "-j":
        execute(TotalComfortAction.JSON)
        sys.exit()

    if sys.argv[1] == "-x":
        execute(TotalComfortAction.CANCEL)
        sys.exit()

    if (len(sys.argv) < 3) or (sys.argv[1] == "-help"):
        printUsage()
        sys.exit()

    if sys.argv[1] == "-c":
        execute(TotalComfortAction.COOL, sys.argv[2])
        sys.exit()

    if sys.argv[1] == "-h":
        execute(TotalComfortAction.HEAT, sys.argv[2])
        sys.exit()

    if sys.argv[1] == "-m":
        execute(TotalComfortAction.MODE, sys.argv[2])
        sys.exit()

    if sys.argv[1] == "-f":
        execute(TotalComfortAction.FAN, sys.argv[2])
        sys.exit()

if __name__ == "__main__":
    main()
