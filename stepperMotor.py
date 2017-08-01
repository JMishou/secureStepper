import RPi.GPIO as GPIO 	#import the gpio library
import time			#import the time library
import sys
import traceback

enable_pin = 18		#GPIO 18 is connected to 1,2 EN and 3,4 EN of the L293D chip physical pins 1 and 9
coil_A_1_pin = 4	#GPIO 4 is connected to 1A pin of the L293D chip physical pin 2
coil_A_2_pin = 17	#GPIO 17 is connected to 2A pin of the L293D chip physical pin 7
coil_B_1_pin = 23	#GPIO 23 is connected to 3A pin of the L293D chip physical pin 10
coil_B_2_pin = 24	#GPIO 24 is connected to 4A pin of the L293D chip physical pin 15

class stepperMotor():  #Class for controlling a stepper motor using the L293D


	def __init__(self, A1,A2,B1,B2,EN):

		GPIO.setmode(GPIO.BCM)		#sets the gpio to match the BCM number and not the physical pin number on the pin header
		 

		self.enable_pin = EN	#GPIO that is connected to 1,2 EN and 3,4 EN of the L293D chip physical pins 1 and 9
		self.coil_A_1_pin = A1	#GPIO that is connected to 1A pin of the L293D chip physical pin 2
		self.coil_A_2_pin = A2	#GPIO that is connected to 2A pin of the L293D chip physical pin 7
		self.coil_B_1_pin = B1	#GPIO that is connected to 3A pin of the L293D chip physical pin 10
		self.coil_B_2_pin = B2	#GPIO that is connected to 4A pin of the L293D chip physical pin 15
	
		#Configure the gpio pins as outputs
		GPIO.setup(self.enable_pin, GPIO.OUT)
		GPIO.setup(self.coil_A_1_pin, GPIO.OUT)
		GPIO.setup(self.coil_A_2_pin, GPIO.OUT)
		GPIO.setup(self.coil_B_1_pin, GPIO.OUT)
		GPIO.setup(self.coil_B_2_pin, GPIO.OUT)

	# The next two functions are the step sequencs.  They each take a delay and number of cycles.  
	# Each cycle has 4 steps.  We are using the two coil method of driving a stepper motor.
	# To learn how stepper motors work you may want to watch this video https://www.youtube.com/watch?v=bngx2dKl5jU

	def forward(self, delay, cycles):  
		for i in range(0, cycles):  #loop through the number of cycles
			self.setStep(1, 0, 1, 0)       #Step #1 turn on coil A forward and B forward
			time.sleep(delay)         #delay before turning on the next step in the sequence.
			self.setStep(0, 1, 1, 0)       #Step #2 turn on coil A reverse and B forward
			time.sleep(delay)         #delay before turning on the next step in the sequence.
			self.setStep(0, 1, 0, 1)       #Step #3 turn on coil A reverse and B reverse
			time.sleep(delay)         #delay before turning on the next step in the sequence.
			self.setStep(1, 0, 0, 1)       #Step #4 turn on coil A forward and B reverse
			time.sleep(delay)
	 
	def backwards(self, delay, cycles):  
		for i in range(0, cycles):
			self.setStep(1, 0, 0, 1)
			time.sleep(delay)
			self.setStep(0, 1, 0, 1)
			time.sleep(delay)
			self.setStep(0, 1, 1, 0)
			time.sleep(delay)
			self.setStep(1, 0, 1, 0)
			time.sleep(delay)
	  
	def setStep(self, w1, w2, w3, w4):      #Function to turn on the corresponding gpio pins
		GPIO.output(self.coil_A_1_pin, w1)   #Set the outputs accordingly
		GPIO.output(self.coil_A_2_pin, w2)   #.
		GPIO.output(self.coil_B_1_pin, w3)   #.
		GPIO.output(self.coil_B_2_pin, w4)   #.
	 
	def go(self, rpm, revolutions):  #Function to initate the stepper motor in motion
		try:
			GPIO.output(self.enable_pin, 1)  #Bring the enable pin high to turn on the L293D motor driver chip

			#delay = sec / step = 1 revolution / 200 steps * 60 sec / 1 minute * 1 minute / (RPM) revolutions
			#delay = 0.3 / RPM
			delay = abs(0.3 / rpm)

			# there are 200 steps per revolution
			# each cycle is 4 steps => 50 cycles / revolution
			cycles = int(revolutions * 50) 

			if rpm < 0:
				direction = 0
			else:
				direction = 1

			#Direction is handled as a boolean value 1 is forward 0 is reverse
			if direction:
				self.forward(delay,cycles)  #if forward turn the motor forwards
			else:
				self.backwards(delay,cycles)#if backwards turn the motor forwards

			self.setStep(0,0,0,0)  # when the motor is finished turn off all coils.

			GPIO.output(self.enable_pin, 0) #turn off the L293D chip
		except Exception as e:
			sys.exit(traceback.format_exc())

	def __del__(self):
		GPIO.cleanup([self.enable_pin, self.coil_A_1_pin, self.coil_A_2_pin, self.coil_B_1_pin, self.coil_B_2_pin])

