from flask import Flask
from flask import Flask, flash, redirect, render_template, request, session, abort
import os
import hashlib
import ssl
from sqlalchemy.orm import sessionmaker
from database import *

userdb = userDatabase(active_db_url)
 
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
ctx.load_cert_chain('ssl.cert', 'ssl.key')
 
@app.route('/')
def home():
    global message
    if not session.get('logged_in'):
        return render_template('login.html', msg=message)
    else:
        return "Hello Boss!  <a href='/logout'>Logout</a>"

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
		if hashlib.sha256(POST_PASSWORD + salt).hexdigest() == pwd:	
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

 
if __name__ == "__main__":


    app.secret_key = os.urandom(12)
    app.run(debug=True,host='0.0.0.0', port=4000, ssl_context=ctx)


