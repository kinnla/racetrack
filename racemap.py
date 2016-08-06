import queue
import sys
import os.path

class Map:

	def __init__(self, filename):

		# check, if the map file exists
		if not os.path.isfile(filename):
			print('Error: Map file <{f}> does not exist.'.format(f=filename))
			sys.exit(0)

		# read the map line by line and store it in a tuple of strings
		# remove line breaks as well.
		try:
			mapfile = open(filename, 'r')
			self.map_data = [line[:-1] for line in mapfile]
		except:
			print('Error while loading map file <{f}>'.format(f=filename))
			sys.exit(0)
		finally:
			mapfile.close()
		
		# determine width and height
		self.width = len(self.map_data[0])
		self.height = len(self.map_data)

		# scan the map and find start and finish co-ordinates
		# also check for consistency:
		# - all lines should have the same length
		# - first and last column all 'o'
		# - allowed characters: 's', 'f', 'o', ' '
		self.start_points = []
		self.finish_points = []
		for y in range(self.height):
			line = self.map_data[y]
			if len(line) != self.width:
				print('Error: Map lines have inconsistent length, see line #{n}.'
					.format(n=y+1))
				if (y == self.height - 1):
					print ('Missing linebreak in last line?')
				sys.exit(0)
			if line[0] != 'o' or line[-1] != 'o':
				print('Error: first and last character of the map should be all "o"')
				sys.exit(0)
			for x in range(self.width):
				char = line[x]
				if char == 's':
					self.start_points.append((x,y))
				elif char == 'f':
					self.finish_points.append((x,y))
				elif char != ' ' and char != 'o':
					print('Error: unknown character in map: "{c}".'
						.format(char=c))
					sys.exit(0)

		# Check map consistency: first and last line all 'o'
		if any(char != 'o' for char in self.map_data[0]):
			print('Error: first map line should be all "o"')
			sys.exit(0)
		if any(char != 'o' for char in self.map_data[-1]):
			print('Error: first map line should be all "o"')
			sys.exit(0)

		# check that we have any start and finish points
		if not self.start_points:
			print('Error: map has no start points.')
			sys.exit(0)
		if not self.finish_points:
			print('Error: map has no finish points.')
			sys.exit(0)

		# create distance map
		self.distances = {}
		q = queue.Queue()
		for p in self.finish_points:
			self.distances[p] = 0
			q.put(p)
		while not q.empty():
			cell = q.get()
			for p in self.get_neighbors(cell):
				if self.get(p) and p not in self.distances:
					self.distances[p] = self.distances[cell] + 1
					self.max_distance = self.distances[cell] + 1
					if self.get(p) != 'o':
						q.put(p)

		# check that all start cells have a path to the finish
		if any([p not in self.distances for p in self.start_points]):
			print('Error: at least 1 start point has no path to the finish')
			sys.exit(0)


	def get_neighbors(self, p):
		""" returns a list of up to 9 neighbor points for the given point,
		including the point itself. Does not check if the points are inside
		the map or out. """
		x, y = p
		return [(x+i, y+j) for i in range(-1, 2) for j in range(-1, 2)]


	def get(self, p):
		""" returns the contents of the given point as a character.
		if p is outside the map, None is returned. """
		x, y = p
		if x < 0 or x >= self.width or y < 0 or y >= self.height:
			return None
		return self.map_data[y][x]


	def get_distance(self, p):
		""" returns the distance of a given point to the finish.
		If there is no way from p to the finish or p is outside the map,
		None is returned. """
		if p in self.distances:
			return self.distances[p]
		return None


