from flask import Flask
from flask import Flask, flash, redirect, render_template, request, session, abort
import os
import encryption
import ssl
from sqlalchemy.orm import sessionmaker
from database import *
from encryption import *
from stepperMotor import *

import RPi.GPIO as GPIO 	#import the gpio library
import time			#import the time library

stepper = stepperMotor(coil_A_1_pin, coil_A_2_pin, coil_B_1_pin, coil_B_2_pin, enable_pin)

enc = encryption(None, "rsa_key.bin")
connections = json.loads(enc.decrypt("connections.bin"))
userdb = userDatabase(connections['dbconnect'])
 
app = Flask(__name__)

global pass_attempts
global pass_fails 
global userName_failing
global message

pass_attempts = 3
pass_fails = 0 
userName_failing = ""
message = ""

ctx = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
ctx.load_cert_chain('server.crt', 'private.key')
 
@app.route('/')
def home():
    global message
    if not session.get('logged_in'):
        return render_template('login.html', msg=message)
    else:
        return render_template('main.html')

def locked():
        return "Account Locked.  Please contact your adminstrator"
 
@app.route('/login', methods=['POST'])
def do_admin_login():

    global pass_attempts
    global pass_fails
    global userName_failing
    global message
    POST_USERNAME = str(request.form['username'])
    POST_PASSWORD = str(request.form['password'])
 
    result = userdb.queryUser(POST_USERNAME)
    if not result:
	message = 'User name not found!'
	return home()
    else:
	if not result.locked:
		salt = result.salt
		pwd = result.password
		hashed = hashData(POST_PASSWORD + salt)
		if hashed == pwd:	
			pass_fails = 0
			message = ""
			session['logged_in'] = True
		else:
			if userName_failing != POST_USERNAME:
				pass_fails = 0
				userName_failing = POST_USERNAME
			pass_fails += 1
			remaining = pass_attempts - pass_fails
			message = "Login failed... {} attempts remaining".format(remaining)
	        if pass_fails == pass_attempts:
			pass_fails = 0
	        	userdb.lockUser(POST_USERNAME) 
			return locked()
	else:
		return locked()
    return home()
 
@app.route("/logout")
def logout():
    session['logged_in'] = False
    return home()

# When the submit button is pushed on the webpage
@app.route("/submit", methods=['POST'])
def handle_data(): #get the data
   rpm = request.form.get('speed', default=0, type=int)  #get the input for speed
   revolutions = request.form.get('revs',default=0,type=int) #get the input for revolution
   direction = request.form.get('direction',default=1,type=int) #get the input for direction

   



   #since the user input for direction is 1 or 0 we need create a string
   #to add to the output.  If direction = 1 then dirstr = forward 
   #otherwise dirstr = backwards
   dirstr=""
   if direction:
     dirstr = "forward"
   else:
     rpm = -rpm
     dirstr = "backwards"

   #out put a message that states what the motor is doing.
   print ("{0} @ {1} RPM for {2} revolutions".format(dirstr, rpm,revolutions))

   #run the motor
   stepper.go(rpm, revolutions)

   #reload the main page
   return render_template('main.html')

 
if __name__ == "__main__":


    app.secret_key = os.urandom(12)
    app.run(debug=True,host='0.0.0.0', port=4000, ssl_context=ctx) 			


