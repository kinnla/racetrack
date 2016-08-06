import tkinter
import sys
import getopt
import time
import threading
import os
import random
import enum

import racemap
import racecar
import racecolor


def callback(event):
	""" Reacts to a user click on the window """

	# switch on the status
	global status

	# if still initializing, ignore the click and don't do anything
	if status == Status.init:
		return

	# if ready, start the race or show the distance map
	elif status == Status.ready:
		if cars:
			status = Status.race
			t = threading.Thread(target = start_race)
			t.start()
		else:
			status = Status.distances
			draw_map()

	# if the race is running, pause the race
	elif status == Status.race:
		status = Status.paused

	# if the race is paused, continue running
	elif status == Status.paused:
		status = Status.race

	# if the distance map is shown, show the normal map
	elif status == Status.distances:
		status = Status.ready
		draw_map()
			
	# if the race is finished, exit the program
	elif status == Status.finished:
		sys.exit(0)


def start_race():

	global status

	# start the race
	print ("Starting race. Time delay: {t}, max rounds: {r}, max driver time: {e} "
		.format(t=time_delay, r=max_rounds, e=driver_time))

	# loop while we don't have a winner
	unfinished_cars = []
	for round in range(max_rounds):

		# end the race if all cars either reached the finish 
		# or were disqualified through too much driver time
		unfinished_cars = [c for c in cars if map.get_distance(c.position)]
		unfinished_cars = [c for c in unfinished_cars if c.total_time < driver_time]
		if not unfinished_cars:
			break

		# iterate on all cars that not yet finished
		for car in unfinished_cars:
			x1, y1 = car.position

			# move the car, if it not yet finished
			car.move(tuple([(car.position, car.velocity) for car in cars]))

			# paint the car
			x2, y2 = car.position
			xx1, yy1 = car.drawing_offset
			xx2, yy2 = car.update_drawing_offset(cell_size // 4)
			canvas.create_line(
				x1 * cell_size + cell_size // 2 + xx1, 
				y1 * cell_size + cell_size // 2 + yy1,
				x2 * cell_size + cell_size // 2 + xx2,
				y2 * cell_size + cell_size // 2 + yy2,
				fill=car.color,
				width=cell_size // 5,
				arrow='last',
				arrowshape='9 12 5')

			log ('<{d}> in {c} car #{n} at {p} with {v}, time spent: {t}'
					.format(n=car.number, d=car.get_driver_name(), c=car.color,
						p=car.position, v=car.velocity, t=car.total_time))
			
			# check, if the car has to be disqualified for too much computation time
			if car.total_time > driver_time:
				log ('<{d}> in {c} car #{n} disqualified for too much time'
						.format(n=car.number, d=car.get_driver_name(), c=car.color))

			# time delay 
			time.sleep(time_delay)
			while status == Status.paused:
				time.sleep(time_delay)

		# end of for loop
		log ('Finished round {r}.'.format(r=round+1))

	# end of while loop
	# get the results by sorting the cars for
	# 1. the number of moves
	# 2. the distance to the finish
	# 3. the total time spend
	results = sorted (cars, key=lambda c: c.total_time)
	results = sorted (results, key=lambda c: c.total_moves)
	results = sorted (results, key=lambda c: map.get_distance(c.position))

	# print results
	print ('--------------- !!! Race finished !!! -----------------')
	for i in range (len(results)):
		car = results[i]
		print ('{rank}: <{dr}> in {c} car #{n}, rounds={r}, distance={d}, time={t}'
			.format(rank=i+1, n=car.number, dr=car.get_driver_name(), c=car.color,
			r=car.total_moves, t=car.total_time, d=map.get_distance(car.position)))
	status = Status.finished


def draw_map():
	""" draws the map on the canvas """

	# iterate on all cells
	for x in range(map.width):
		for y in range(map.height):

			# default cell color is white
			cell = map.get((x,y))
			color = 'white'

			# check, if distances shall be shown
			if status == Status.distances:
				d = map.get_distance((x,y))

				# compute color by distance to finish, if there is a distance
				if d is not None:
					color = '#' + hex(0xBBBB00 
						+ 0xFF * (map.max_distance - d) // map.max_distance)[2:]
			else:
				# determine color by the cell type 
				if cell == 's':
					color = 'light grey'
				elif cell == 'f':
					color = 'pale green'

			# draw rectangle
			canvas.create_rectangle(
				x * cell_size, 
				y * cell_size,
				(x + 1) * cell_size,
				(y + 1) * cell_size,
				fill=color)

			# draw obstacle, if any
			if cell == 'o':
				canvas.create_oval(
					x * cell_size + 1, 
					y * cell_size + 1,
					(x + 1) * cell_size - 1,
					(y + 1) * cell_size - 1,
					fill='black')

def log(s):
	""" checks if the verbose flag is set and if so, prints the string """
	if verbose: print(s)

class Status(enum.Enum):
	init = 0
	ready = 1
	distances = 2
	race = 3
	paused = 4
	finished = 5

# -------------------- start of the script ------------------

# Flag indicating if the simulation is paused
# initially, before the simulation thread is started, set to None
status = Status.init

# -------------------- default values for options ------------------

# debug mode (don't catch exceptions from the driver)
debug_mode = False

# debug mode (don't catch exceptions from the driver)
verbose = False

# shuffle mode (random start order for drivers)
shuffle = False

# name of the map file to be loaded
map_file = 'maps/map.txt'

# size of the cell to be rendered in pixels
cell_size = 16

# maximum number of rounds to be simulated
# cars might get stuck so we won't loop forever
max_rounds = 100

# time (in seconds) per car's move that the race is delayed
time_delay = 0.05

# maximum total time (in seconds) for each driver
# exceeding the driver time will disqualify the car
driver_time = 10

# -------------------- parse options --------------------

try:
	opts, args = getopt.getopt(sys.argv[1:], "dvsm:c:r:t:e:", 
		["mapfile=", "cellsize=", "maxrounds=", "timedelay=", "drivertime="])
except getopt.GetoptError:
	print ('usage: racetrack.py -d -v -s -m <mapfile> -c <cellsize> -r <maxrounds> '
		'-t <timedelay> -e <drivertime> <driver_1> <driver_2> ... <driver_n>')
	sys.exit(2)
for opt, arg in opts:

	# debug mode (surpresses exception handling)
	if opt == '-d':
		debug_mode = True

	# verbose (surpresses exception handling)
	if opt == '-v':
		verbose = True

	# shuffle (random start order of drivers)
	if opt == '-s':
		shuffle = True

	# map file
	if opt in ('-m', '--mapfile'):
		if not os.path.isfile(arg):
			print('Error: mapfile <{file}> does not exist'.format(file=arg))
			sys.exit(0)
		map_file = arg

	# cell size
	elif opt in ('-c', '--cellsize'):
		try:
			cell_size = int(arg)
		except:
			print('Error: cellsize must be an integer')
			sys.exit(0)

	# maximum number of rounds
	elif opt in ('-r', '--maxrounds'):
		try:
			max_rounds = int(arg)
		except:
			print('Error: maxrounds must be an integer')
			sys.exit(0)

	# time delay after each car moved
	elif opt in ('-t', '--timedelay'):
		try:
			time_delay = float(arg)
		except:
			print('Error: timedelay must be a number')
			sys.exit(0)

	# maximum computation time a driver may use for the race
	elif opt in ('-e', '--drivertime'):
		try:
			driver_time = float(arg)
		except:
			print('Error: drivertime must be a number')
			sys.exit(0)

# -------------------- load and draw map --------------------

# load map
map = racemap.Map(map_file)

# create tk root and canvas
tk_root = tkinter.Tk()
w, h = map.width * cell_size, map.height * cell_size
canvas = tkinter.Canvas(tk_root, width=w, height=h, bg="#ffffff")

# draw the map
draw_map()

# -------------------- create the cars --------------------

# check if we have enough start points for the cars
if len(args) > len(map.start_points):
	print('Error: Too many drivers for this map! '
		'There are {n1} drivers, but only {n2} start points'
		.format(n1=len(args), n2=len(map.start_points)))
	sys.exit(0)

# shuffle drivers, if the related option is set
if shuffle:
	random.shuffle(args)

# iterate on the drivers
cars = []
for number in range(len(args)):

	# create car and driver
	car = racecar.Car(args[number], map, number, debug_mode, verbose)
	
	# make sure that we don't have a double color
	while car.color in [c.color for c in cars]:
		car.color = random.choice(racecolor.COLORS)

	# paint a circle in the car's color
	x, y = car.position
	canvas.create_oval(
	x * cell_size + cell_size // 5, 
	y * cell_size + cell_size // 5,
	(x + 1) * cell_size - cell_size // 5,
	(y + 1) * cell_size - cell_size // 5,
	fill=car.color)

	# add the car to the list
	cars.append(car)
	print ('loaded driver <{d}> as car #{n} with color {c}'
		.format(d=args[number], n=number, c=car.color))

# -------------------- show the gui --------------------

# bind event
canvas.bind("<Button-1>", callback)

# show the canvas
canvas.pack()
tk_root.title("Race Track")
if cars:
	print ('finished intitialization. Click to start race.')
else:
	print ('finished intitialization. Click to show distance map.')
status = Status.ready
tk_root.mainloop()


