import racemap

class Driver:

	def __init__(self, map, number):
		
		# save objects and create distance map
		self.map = map
		self.number = number


	def drive(self, car_data):

		# get the possible positions, according to current position and velocity
		x, y = car_data[self.number][0]
		dx, dy = car_data[self.number][1]
		projection = (x + dx, y + dy)
		points = self.map.get_neighbors(projection)
		
		# discard points 
		# - outside the map 
		# - obstacles 
		# - with no distance
		points = [p for p in points if self.map.get(p)]
		points = [p for p in points if self.map.get(p) != 'o']
		points = [p for p in points if self.map.get_distance(p) is not None]

		# in case no position remains, return the projection
		# that means we will crash 
		if len(points) == 0:
			return projection

		# choose the position with minimum value
		return min(points, key = self.map.get_distance)

	def get_color(self):
		""" returns the preferred color for this driver.
		racecolor.py contains a list of all eligable colors. """
		return "red"
