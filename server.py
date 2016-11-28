#!/usr/bin/env python3
import json
import time
import socket
import _thread
import requests
import threading
#import RPi.GPIO as GPIO

"""
global
"""
global solution_num

"""
	airport_code (str)
"""
class Weather(object):
	def __init__(self, airport_code):
		self.airport_code = airport_code
		self.getAirportLoc()
		self.getWeather()
	def getAirportLoc(self):
		url = 'http://www.airport-data.com/api/ap_info.json?iata='
		request = url + self.airport_code
		data = requests.get(request)
		data_dict = json.loads(data.text)
		self.location = data_dict.get('location')
	def getWeather(self):
		url = 'http://api.openweathermap.org/data/2.5/weather?q='
		api_key = '&APPID=2463e27646249ffba883b72a3a592b36'
		request = url + self.location + api_key
		weather = requests.get(request)
		self.weather_text = weather.text


"""
	origin (str):	origin airport code
	destination (str): destination airport code
	date (str): date
"""
class FlightInfo(object):
	def __init__(self, origin, destination, date):
		self.origin = origin
		self.destination = destination
		self.date = date
	def getInfo(self):
		api_key = "AIzaSyAzhRKsVomussZwM3GSX76kz2dPdDhNt5w"
		url = "https://www.googleapis.com/qpxExpress/v1/trips/search?key=" + api_key
		headers = {'content-type': 'application/json'}
		params = {
		  "request": {
		    "slice": [
		      {
		        "origin": self.origin,
		        "destination": self.destination,
		        "date": self.date
		      }
		    ],
		    "passengers": {
		      "adultCount": 1
		    },
		    "solutions": solution_num,
		    "refundable": False
		  }
		}
		response = requests.post(url, data=json.dumps(params), headers=headers)
		data = response.json()
		trips_text = data.get('trips')

		self.trips_data = trips_text.get('data')
		#print (data)
		if self.trips_data.get('airport') == None: 
			return None
		else:
			#global solution_num

			trip_option = trips_text.get('tripOption')
			flightInfo = [None] * solution_num
			flightPrice = [None] * solution_num
			
			for i in range (0, len(trip_option)):
				flight_str = ''
				flight_list = []
				tripInfo = trip_option[i]

				price = tripInfo.get('saleTotal')
				flightPrice[i] = price

				data_slice = tripInfo.get('slice')
				data_length = len(data_slice)
				for j in range (0, data_length):
					segment = data_slice[j].get('segment')
					for k in range (0, len(segment)):
						leg = segment[k].get('leg')
						for n in range (0, len(leg)):
							origin = leg[n].get('origin')
							destination = leg[n].get('destination')
							departureTime = leg[n].get('departureTime')
							arrivalTime	= leg[n].get('arrivalTime')
							
							flight_str = origin + '\t' + destination + '\t' + departureTime + '\t' + arrivalTime 
							flight_list.append(flight_str)
				flightInfo[i] = flight_list
			return [flightInfo, flightPrice]


"""
	client thread

	clientsocket (socket)
"""
class ClientThread(threading.Thread) :

	def __init__(self,clientsocket):
		threading.Thread.__init__(self)
		self.csocket = clientsocket
		self.size = 8192
		#self.id = id
		print ("[+] New thread started ")

	def run(self): 
		question_byte = self.csocket.recv(self.size)
		question_str  = question_byte.decode("utf-8") 
		question_dict = json.loads(question_str)

		airports = [None] * 3

		airports[0] = question_dict.get("first")
		airports[1] = question_dict.get("second")
		airports[2] = question_dict.get("third")

		destination = question_dict.get("destination")
		date = question_dict.get("date")

		#destination weather
		destination_weather = Weather(destination)
		#print(destination_weather.weather_text)

		find_flight = False
		trips_data = None
		for i in range (0,3):
			flightInfo = FlightInfo(airports[i], destination, date)
			trips_data = flightInfo.getInfo()
			if trips_data != None:
				find_flight = True
				break
		

		# create answer payload
		weather_dict = json.loads(destination_weather.weather_text)
		answer = {"weather": weather_dict,"flight": trips_data}
		
		answer_str = json.dumps(answer)
		self.csocket.send(answer_str.encode('utf-8'))	
		#airport_one = flightInfo()

		"""
		count = 0
		while True:
			time.sleep(1)
			#print("Id is " + str(self.id))
			
			print(data)
			count += 1
			if (count == 5):
				self.csocket.close()
				self.csocket = None
				break
		"""

		
"""
LED thread, control 7 segement LED show coresponding client number
"""
class LEDThread(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.num = 0;
	#	self.num (int): client number
	def run(self):
		while 1:
			time.sleep(2)
			self.num = threading.active_count() - 2
			print(self.num)
		
			#print(Server.backlog)
			#if (Server.client[0] == None):
			#	print("NONE")
	#def count_1(self):

"""
	server 
	hostAdd (str): host ip address
"""
class Server(object):
	def __init__(self, hostAdd):
		self.host = hostAdd
		self.backlog = 5
		self.client = None
		self.address = None
		self.openServer()
		self.startListen()

	def openServer(self):
		port = 2000
		size = 1024		
		self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.server.bind((self.host, port))

	def startListen(self):
		# LED thread
		led = LEDThread()
		led.start()

		error_msg = '<socket.socket [closed] fd=-1, family=AddressFamily.AF_INET, type=SocketKind.SOCK_STREAM, proto=0>'
		print ('server started and listening..')
		while True:
			self.server.listen(self.backlog)
			self.client, self.address = self.server.accept()

			#pass client socket 
			newthread = ClientThread(self.client)
			newthread.start()
			



"""
	main function
"""
if __name__ == "__main__":
	global solution_num
	solution_num = 20
	a_lock = _thread.allocate_lock()
	host = ''
	server = Server(host)
