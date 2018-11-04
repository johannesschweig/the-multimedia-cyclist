#!/usr/bin/python
import RPi.GPIO as GPIO
import time
from statistics import median
import threading
import sys
import board
import neopixel

try:
	t = int(sys.argv[1])
except:
	print('Using default time of 20s')
	t = 20
try:
        TH = int(sys.argv[2])
except:
        print('Using default warning distance of 1.40m')
        TH = 140

try:
        TH2 = int(sys.argv[3])
except:
        print('Using default message distance of 1.0m')
        TH2 = 100

class queue():
	def __init__(self, n):
		self.n = n
		self.l = [None] * n
	def add(self, item):
		self.l.pop(0)
		self.l.append(item)
	def median(self):
		try:
			return median([i for i in self.l if i is not None])
		except:
			return 650

# initialize neopixel matrix with brightness level
def init(bright):
    return neopixel.NeoPixel(board.D18, 64, brightness=bright, auto_write=False)

# turns off all pixels and deinitializes the neopixel matrix
def deinit():
    for i in range(0, 64):
        pixels[i] = (0,0,0)
    pixels.show()
    pixels.deinit()


def symbol(symbol, color):
	i = 0
	for char in open('symbols/' + symbol + '.txt', 'r').read():
		if not char: break
		if char == '1':
			pixels[i] = color
			i += 1
		elif char == '0':
			pixels[i] = (0,0,0)
			i = i + 1
	pixels.show()


class arrow(threading.Thread):
	def __init__(self, event, freq=0.5):
		threading.Thread.__init__(self)
		self.event = event
		self.event.show = False

		vec1 = [1,0,0,1,1,0,0,1] * 2
		vec2 = [0,0,1,1,0,0,1,1] * 2
		vec3 = [0,1,1,0,0,1,1,0] * 2
		vec4 = [1,1,0,0,1,1,0,0] * 2
		self.vecs = [vec1, vec2, vec3, vec4, vec4, vec3, vec2, vec1]

		self.shift = 0
		self.freq = freq

	def run(self):
		while not self.event.wait(self.freq):
			if not self.event.show:
				continue
			#print('test2')
			mat = [ i for v in self.vecs for i in v[0+self.shift:8+self.shift]]
			self.shift = (self.shift + 1) % 4
			#print(mat)
			for i, p in enumerate(mat):
				if p:
					pixels[i] = (255, 100, 0)
				else:
					pixels[i] = (0,0,0)
			pixels.show()
			#time.sleep(self.freq)

def simple_arrow():
	vec1 = [0,0,0,1,1,0,0,1]
	vec2 = [0,0,1,1,0,0,1,1]
	vec3 = [0,1,1,0,0,1,1,0]
	vec4 = [1,1,0,0,1,1,0,0]
	mat = vec1 + vec2 + vec3 + vec4 + vec4 + vec3 + vec2 + vec1

	for i, p in enumerate(mat):
		if p:
			pixels[i] = (255, 100, 0)
		else:
			pixels[i] = (0,0,0)
	pixels.show()




def run_measurement(PIN_ctrl, PIN_read, LED=None, d_th = TH2, n = 3):
	vals = []
	GPIO.output(PIN_ctrl, GPIO.HIGH)

	for i in range(n):
		while GPIO.input(PIN_read):
			pass
		while GPIO.input(PIN_read) == 0:
			p_start = time.time()
		while GPIO.input(PIN_read)==1:
			p_end = time.time()
		pulse_duration = p_end - p_start
		distance = round(pulse_duration * 17279, 2)
		vals.append(distance)

	distance = median(vals)

	if not LED:
		pass
	elif distance < d_th:
		GPIO.output(LED, GPIO.HIGH)
	else:
		GPIO.output(LED, GPIO.LOW)

	GPIO.output(PIN_ctrl, GPIO.LOW)
	return distance



try:
	#GPIO.setmode(GPIO.BOARD)
	PIN_TRIGGER = 17 #11  #upper 1st orange
	PIN_ECHO = 4 #7	  #upper 1st yellow
	LED_RED = 23 #16	  #lower orange
	LED_GREEN = 12 #32	  #lower 2nd red
	PIN_TRIGGER2 = 22 #15 #upper grey
	PIN_ECHO2 = 27 #13    #upper white

	GPIO.setup(PIN_TRIGGER, GPIO.OUT)
	GPIO.setup(PIN_ECHO, GPIO.IN)
	GPIO.setup(PIN_TRIGGER2, GPIO.OUT)
	GPIO.setup(PIN_ECHO2, GPIO.IN)
	GPIO.setup(LED_GREEN, GPIO.OUT)
	GPIO.setup(LED_RED, GPIO.OUT)

	GPIO.output(PIN_TRIGGER, GPIO.LOW)
	GPIO.output(PIN_TRIGGER2, GPIO.LOW)
	GPIO.output(LED_RED, GPIO.LOW)
	GPIO.output(LED_GREEN, GPIO.LOW)

	print("Waiting for sensor to settle & LED-test")

	for i in range(2):
		GPIO.output(LED_RED, GPIO.HIGH)
		GPIO.output(LED_GREEN, GPIO.HIGH)
		time.sleep(0.25)
		GPIO.output(LED_RED, GPIO.LOW)
		GPIO.output(LED_GREEN, GPIO.LOW)
		time.sleep(0.5)

	pixels = init(0.3)

	vals = []
	print('{}s measurement starting now'.format(t))
	start = time.time()

	event = threading.Event()
	timer = arrow(event, 0.1)
	timer.start()

	while time.time() - start < t:

		v1 = run_measurement(PIN_TRIGGER, PIN_ECHO)
		v2 = run_measurement(PIN_TRIGGER2, PIN_ECHO2)
		vals.append((v1, v2))

		if v2 < TH2:
			event.show = False
			symbol('smiley_sad', (255,0,0))

		elif v1 < TH:
			#print(v2)
			event.show = True
			#timer.show()
			#simple_arrow()
		else:
			event.show = False
			symbol('smiley', (0,255,0))
			#for i in range(64):
			#	pixels[i] = (0,0,0)
			#pixels.show()

	event.set()

	for i, d in enumerate(vals):
		print('Measurement {}: {} cm, {} cm'.format(i, d[0], d[1]))



finally:
	deinit()
	GPIO.cleanup()
