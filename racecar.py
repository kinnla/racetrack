import racemap
import copy
import sys
import random
import time
import os.path

class Car:
	
	def __init__(self, path_to_driver, map, number, debug_mode, verbose):
	
		# the current velocity of the car, initially zero
		self.velocity = (0, 0)

		# the current drawing offset for the car, initially zero
		# the drawing offset helps to visualize the car's path more vividely
		self.drawing_offset = (0, 0)

		# the color for the car, initially gray
		self.color = "gray"

		# the accumulated time spent by the driver
		self.total_time = 0.0

		# the number of moves by this car in the race
		self.total_moves = 0

		# the map of the race track
		self.map = map	

		# the number of the car
		self.number = number

		# debug mode
		self.debug_mode = debug_mode

		# the current position of the car, initially the start position
		self.position = map.start_points[number]

		# verbose mode (print detailed messages)
		self.verbose = verbose

		# check if the driver file exists
		if not os.path.exists(path_to_driver):
			print('Error: Driver file <{d}> does not exists!'
				.format(d=path_to_driver))
			sys.exit(0)

		# add the path where the driver is located to the python path,
		# so the module can be loaded
		sys.path.append(os.path.dirname(path_to_driver))

		# prepare the module name for loading
		module = os.path.basename(path_to_driver)
		if module[-3:] == '.py':
			module = module[:-3]

		# load the driver
		if debug_mode:
			self.load_driver(module)
		else:
			try:
				self.load_driver(module)
			except ImportError:
				print('Error: Import of driver <{d}> failed!'
					.format(d=path_to_driver))
				sys.exit(0)
			except AttributeError:
				print('Error: Module <{d}> does not contain a class named '
					'"Driver"!'.format(d=path_to_driver))
				sys.exit(0)
			except TypeError:
				print('Error: Can not create an instance of "Driver" in <{d}>.'
					'Wrong signature of __init__?'
					.format(d=path_to_driver))
				sys.exit(0)

	def load_driver(self, module):
		""" Loads and initializes the driver.

		The time while loading will be recorded and added to total_time. """
		driverClass = getattr(__import__(module), 'Driver')
		t = time.time()
		self.driver = driverClass(copy.deepcopy(self.map), self.number)
		self.color = self.driver.get_color()
		self.total_time += time.time() - t

	def move(self, car_data):
		""" Moves the car.

		Will call the related driver routine, evaluate the move and an eventual
		crash, then apply the move.
		:car_data: a tuple of tupels (position, velocity) for each car """

		# get the driver's move
		p1 = self.position
		v1 = self.velocity
		projection = (p1[0] + v1[0], p1[1] + v1[1])
		t = time.time()
		if self.debug_mode:
			p2 = self.driver.drive(car_data)
		else:
			try:
				p2 = self.driver.drive(car_data)
			except:
				# in case of an exception, keep current speed and direction
				self.log ('Car #{n} with driver {d} in color {c}'
						' caused an exception while driving. '
						'Keep current speed and direction.'
						.format(n=self.number, d=self.get_driver_name(), c=self.color))
				p2 = projection

		# count the move and add the time to the total time spent
		self.total_moves += 1
		self.total_time += time.time() - t

		# if move is illegal, keep current speed and direction
		if not p2 in self.map.get_neighbors(projection):
			self.log ('Car #{n} with driver {d} in color {c} tries to cheat. '
					'Keep current speed and direction.'
					.format(n=self.number, d=self.get_driver_name(), c=self.color))
			p2 = projection
		
		# check if the car will crash
		# check each cell between p1 and p2
		v2 = (p2[0] - p1[0], p2[1] - p1[1])
		steps = max(abs(v2[0]), abs(v2[1]))

		for i in range(steps):
			dx = int (round (v2[0] * (i + 1) / steps))
			dy = int (round (v2[1] * (i + 1) / steps))
			p = p1[0] + dx, p1[1] + dy

			# check, if the car crashed into the wall
			if self.map.get(p) == 'o':
				v2 = (0, 0)
				self.log ('Car #{n} with driver <{d}> in color {c} crashed at {p}.'
						.format(n=self.number, d=self.get_driver_name(), 
						c=self.color, p=p))
				if self.map.get(p1) == 'o':
					
					# don't move at all, if the car was already crashed.
					# prevents cars from biting themselves through walls
					p2 = p1
					self.log ('Car #{n} with driver <{d}> in color {c} tries to '
							'bite itself through the wall at {p}.'
							.format(n=self.number, d=self.get_driver_name(),
							c=self.color, p=p))
				else:
					p2 = p
				break

		# check, if the car crashed into another car
		if any([t[0] for t in car_data if t[0] == p2]) and self.map.get(p2) != 'o':
			v2 = (0, 0)
			self.log ('Car #{n} with driver <{d}> in color {c} '
					'crashed into another car at {p2}.'
					.format(n=self.number, d=self.get_driver_name(), 
					c=self.color, p2=p2))

		# apply the new position and velocity that we just computed
		self.position = p2
		self.velocity = v2


	def get_position_and_velocity(self):
		""" returns the car's current position and velocity as a tuple """
		return self.position, self.velocity


	def update_drawing_offset(self, max):
		""" randomly generates a new drawing offset and returns it """
		self.drawing_offset = (random.randint(-max, max), 
			random.randint(-max, max))
		return self.drawing_offset


	def get_driver_name(self):
		""" returns the name of the driver """
		return self.driver.__module__


	def log(self, s):
		""" checks if the verbose flag is set and if so, prints the string """
		if self.verbose: print(s)
