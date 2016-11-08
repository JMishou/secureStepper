import RPi.GPIO as GPIO 	#import the gpio library
import time
import signal

class alarm:

	def __init__(self,gpio_in,gpio_out):

		self.input = gpio_in
		self.output = gpio_out
		self.init = 0
		self.enabled = 0
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(self.input, GPIO.IN, pull_up_down=GPIO.PUD_UP) 
		GPIO.setup(self.output, GPIO.OUT)
		signal.signal(signal.SIGALRM, self.timer_interrupt)
		self.enable()

	def gpio_interrupt(self, channel):

		self.alert(0.2)

	def enable(self):
		try:
			if self.enabled == 0:
				GPIO.add_event_detect(self.input, GPIO.FALLING, callback=self.gpio_interrupt, bouncetime=300)
				self.enabled = 1
		except Exception as e:
			gracefulExit(e)

	def disable(self):
		try:
			if self.enabled == 1:
				GPIO.remove_event_detect(self.input)
				signal.setitimer(signal.ITIMER_REAL, 0) # Disable the alarm
				self.enabled = 0
		except Exception as e:
			gracefulExit(e)

	def alert(self, duration):
		signal.setitimer(signal.ITIMER_REAL, duration)
		GPIO.output(self.output, GPIO.HIGH)

	def timer_interrupt(self, signum, frame):

		GPIO.output(self.output, GPIO.LOW)

	def __del__(self):
		GPIO.cleanup([self.input, self.output])

	def gracefulExit(self, excetion):
		if exception != Menu.exitMenu:
			sys.exit(traceback.format_exc())

