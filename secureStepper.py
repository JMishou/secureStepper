#!/usr/bin/env python2                                                       

import curses                                                                
from curses import panel    
import simplejson as json
import signal
import sys
import pickle
from tabulate import tabulate
import glob
import traceback
import picamera

from database import *
from encryption import *
from stepperMotor import *
from alarm import *
from sendGmail import *

enc = encryption(None, "rsa_key.bin")
connections = json.loads(enc.decrypt("connections.bin"))
userdb = userDatabase(connections['dbconnect'])
currentUser = {}
alrm = alarm(12,20)
gmail = sendGmail(connections['gmailUser'],connections['gmailPass'])
camera = picamera.PiCamera()

class Menu(object): 

    def signal_handler(self, signal, frame):
	raise self.exit_menu
                                                         

    def __init__(self, name, items, stdscreen):
        self.window = stdscreen.subwin(0,0)
        self.window.keypad(1)
	self.name = name
        self.panel = panel.new_panel(self.window)
        self.panel.hide()
	self.panel.set_userptr(self)
        panel.update_panels()

        self.position = 0
	self.name = name
        self.items = items                                                   
        self.items.append(('exit','exit'))      

	signal.signal(signal.SIGINT, self.signal_handler)

    class exit_menu(Exception): pass                             

    def navigate(self, n):                                                   
        self.position += n                                                   
        if self.position < 0:                                                
            self.position = 0                                                
        elif self.position >= len(self.items):                               
            self.position = len(self.items)-1     

    def exit(self):
	raise self.exit_menu                           

    def display(self):                                                       
        self.panel.top()                                                     
        self.panel.show()                                                    
        self.window.clear()  
	(y, x) = self.window.getmaxyx()                                                
	cursorLoc = (0,0)

	try:
		while True:                                                          
		    self.window.refresh()                                            
		    curses.doupdate()      
		    self.window.addstr(0, 1, self.name, curses.A_UNDERLINE )                                           
		    for index, item in enumerate(self.items):                     
		        if index == self.position:                                   
		            mode = curses.A_REVERSE                                  
		        else:                                                        
		            mode = curses.A_NORMAL                                   

		        msg = '%d. %s' % (index+1, item[0])   


			if len(msg) > x/2:
				msg = msg[:x/2]
			if (index+2) >= y:
				cursorLoc = ((index-y)+4,x/2)
				self.window.addstr((index-y)+4, x/2, msg, mode)
			else:                      
				cursorLoc = (index+2,1)
		        	self.window.addstr(index+2, 1, msg, mode)                    

			self.window.move(cursorLoc[0]+4,cursorLoc[1]+10)
		    key = self.window.getch()                                        

		    if key in [curses.KEY_ENTER, ord('\n')]:                         
		        if self.position == len(self.items)-1:                       
		            break                                                    
		        else:                                                        
		            self.items[self.position][1]()                           

		    elif key == curses.KEY_UP:                                       
		        self.navigate(-1)                                            

		    elif key == curses.KEY_DOWN:                                     
		        self.navigate(1)                                             
	except self.exit_menu:
		pass
	except Exception as e:
		sys.exit(traceback.format_exc())

        self.window.clear()
        self.panel.hide()
        panel.update_panels()
        curses.doupdate()

class MyApp(object):

    def __init__(self, stdscreen):  

        self.screen = stdscreen
	self.stepper = stepperMotor(coil_A_1_pin, coil_A_2_pin, coil_B_1_pin, coil_B_2_pin, enable_pin)
        curses.curs_set(0)

	global alrm
	self.alarm = alrm
	global gmail
	self.gmail = gmail

	users = userdb.userList()
	adminMenu_items = [("Add User", self.addUser)]
	for usr in users:
		adminMenu_items.append((usr, self.userActionMenu))            
	self.adminMenu = Menu("Admin Menu", adminMenu_items, self.screen)   

	techMenu_items = [                                                    
                ('Disable Alarm', self.disableAlarm),                                       
                ('Enable Alarm', self.enableAlarm),    
		('Create Program', self.createStepperProgram),  
		('Delete Program', self.deleteProgramMenu)
                ]
	self.techMenu = Menu("Technician Menu",techMenu_items, self.screen)

	userMenu_items = [                                                                                          
                ('Run Program', self.executeProgramMenu)                                     
                ]

	self.userMenu = Menu("Motor Control",userMenu_items, self.screen)
                                                        
	main_menu_items = []
	
	if currentUser['group'] == 'admin':
		main_menu_items.append(("Admin Menu",self.adminMenu.display))
	if currentUser['group']  == 'admin' or  currentUser['group']  == 'tech':
		main_menu_items.append(("Technician Menu", self.techMenu.display))

	main_menu_items.append(("Motor Control Menu", self.userMenu.display))

	main_menu = Menu("Main Menu", main_menu_items, self.screen)                       
	main_menu.display()  

    def enableAlarm(self):
	try:
		self.alarm.enable()
		self.print_msg("Alarm Enabled",10,10)
	except Exception as e:
		self.gracefulExit()

    def disableAlarm(self):
	try:
		self.alarm.disable()
		self.print_msg("Alarm Disabled",10,10)
	except Exception as e:
		self.gracefulExit()

    def setAlarm(alarm_=None, gpio_in=None, gpio_out=None):
	if alarm!=None:
		self.alarm = alarm_
	elif gpio_in!=None and gpio_out!=None:
		self.alarm = alarm(gpio_in,gpio_out)
	else:
		self.alarm = None
	

    def print_selection(self):
	top = panel.top_panel()
	top.window().clear()
	top.window().addstr(10,30, self.getSelectedItem(), curses.A_NORMAL) 

    def print_msg(self,message,y,x):
	top = panel.top_panel()
	top.window().clear()
	top.window().addstr(y,x, message, curses.A_NORMAL)  
	time.sleep(1)

    def getSelectedItem(self):
	top = panel.top_panel()
	menu = top.userptr()
	menu.window.clear()
	return menu.items[menu.position][0]

    def executeProgramMenu(self):
	programMenu = Menu("Programs", self.programMenuItems("execute"), self.screen)
	programMenu.display()
	

    def deleteProgramMenu(self):
	programMenu = Menu("Programs", self.programMenuItems("delete"), self.screen)
	programMenu.display()
	
	
    def programMenuItems(self, action):
	progs = self.listPrograms()
	menu_items = []
	func = None
	if action == "execute":
		func = self.executeStepperProgram
	elif action == "delete":
		func = self.deleteStepperProgram
	for prog in progs:
		menu_items.append((prog,func))
	return menu_items

    def executeStepperProgram(self):
	progName = self.getSelectedItem()
	program = []
	try:
		with open("programs/" + progName,'rb') as f:
	    		program = pickle.load(f)
		self.runStepperProgram(program)
	except Exception as e:	
		self.gracefulExit(e)

    def gracefulExit(self, excetion):
	if exception != Menu.exitMenu:
		sys.exit(traceback.format_exc())
		

#User actions
    def updateAdminMenu(self):
        users = userdb.userList()
	adminMenu_items = [("Add User", self.addUser)]
	for usr in users:
		adminMenu_items.append((usr, self.userActionMenu))            

	adminMenu_items.append(('exit','exit'))
	self.adminMenu.items = adminMenu_items

    def userActionMenu(self):
	self.curUserName = self.getSelectedItem()
	action_items = [
		('Lock User',self.lockUser),
		('Unlock User',self.unlockUser),
		('Delete User',self.deleteUser),
		('Add Email',self.addEmail),
		('Reset Password - User will reset on next login',self.resetPassword),
		('Change Password - Password will be manually changed by admin',self.changePassword) 
		]
	action_menu = Menu(self.curUserName + " Actions", action_items, self.screen)  
	action_menu.display()  

    def lockUser(self):
	userdb.lockUser(self.curUserName)


    def unlockUser(self):
	userdb.unlockUser(self.curUserName)

    def addEmail(self):
	top = panel.top_panel()
	menu = top.userptr()
	menu.window.clear()
	menu.window.refresh()
	curses.reset_shell_mode()
	email = raw_input("Email address:")
	userdb.editEmail(self.curUserName, email)
	curses.reset_prog_mode()
	menu.window.clear()
	menu.window.refresh()
	self.print_msg(email + " added",10,10)
	


    def deleteUser(self):
	userdb.deleteUser(self.curUserName)
	self.updateAdminMenu()
	pan = panel.top_panel()
	menu = pan.userptr()
	menu.exit()
	
    def resetPassword(self):
	userdb.resetPassword(self.curUserName)

    def changePassword(self):
	top = panel.top_panel()
	menu = top.userptr()
	menu.window.clear()
	menu.window.refresh()
	curses.reset_shell_mode()
	userdb.cliChangePassword(self.curUserName, 1)
	userdb.resetPassword(self.curUserName)
	curses.reset_prog_mode()
	menu.window.clear()
	menu.window.refresh()
	self.print_msg(self.curUserName + " Password Changed",10,10)

    def addUser(self):
	top = panel.top_panel()
	menu = top.userptr()
	menu.window.clear()
	menu.window.refresh()
	curses.reset_shell_mode()
	userdb.cliAddUser()
	self.updateAdminMenu()
	curses.reset_prog_mode()
	menu.window.clear()
	menu.window.refresh()

    def runStepperProgram(self, program):
	try:
		for command in program:
			self.stepper.go(command[0],command[1])
	except Exception as e:
		self.gracefulExit(e)
		

    def deleteStepperProgram(self):
	progName = self.getSelectedItem()
	program = []

	os.remove("programs/" + progName)
	top = panel.top_panel()
	menu = top.userptr()
	menu.items = programMenuItems("delete")

	

    def createStepperProgram(self):
	top = panel.top_panel()
	menu = top.userptr()
	menu.window.clear()
	menu.window.refresh()
	curses.reset_shell_mode()

	prog = []
	build = 1
	speed = 0
	revolutions = 0
	while build:
		while True:
			try:
				speed = int(raw_input('Enter Speed (-160 - 160 RPM: '))
				if speed >= -160 and speed <= 160:
					break
				else:
					print "Speed out of range. Try again..."
			except Exception as e:
				print "Invalid input for speed. Try again..."
				continue			

		while True:
			try:
				revolutions = abs(float(raw_input('Enter Revolutions: ')))
				break
			except Exception as e:
				print "Invalid input for revolutions. Try again..."
				continue

		while True:
			cont = raw_input('Would you like to additional steps to your program? (Yes/No)').lower()
			if cont == "yes" or  cont == "y":
				break
			elif cont == "no" or cont == "n":
				build = 0
				break
			else:
				print "Invalid input... Try again."

		
		prog.append([speed,revolutions])
	
	fileName = raw_input('Please enter the name of the program:')
	
	with open("programs/" + fileName + ".pgm",'wb') as f:
    		pickle.dump(prog,f)

	print "Created file " + fileName
	print tabulate(prog, headers=["speed", "revolutions"])

	raw_input('Hit enter to continue:')

	curses.reset_prog_mode()
	menu.window.clear()
	menu.window.refresh()
	curses.doupdate()



    def listPrograms(self):
		files = glob.glob('programs/*.pgm')
		for x in range(0, len(files)):
			files[x] = files[x].replace('programs/','')
		return files

    def sendEmail(self,subject,body):
	image_name = "images/" + time.strftime("%d-%m-%y_%H-%M-%S") + ".jpg"
	camera.capture(image_name)
	recipients = self.userdb.emailList()
	self.gmail.subject = subject
	self.gmail.body = body
	self.gmail.addRecipients(recipients)
	self.gmail.addAttachments(image_name)
	self.gmail.send()

def authenticate():
	userName = raw_input('Please Enter User Name: ')
	authenticated = userdb.cliAuthenticate(userName)
	if authenticated:
		print "Login Success."
		global currentUser 
		currentUser = userdb.getUser(userName)
	else:
		user = userdb.getUser(userName)
		if user == None or user['locked']:
			alrm.alert(0.2)
			if user == None:
				sendEmail("Unknown User: " + userName, "An unknown user has attempted to log into the system")
			else:
				sendEmail("User Locked: " + userName, "User is locked out of the system.")
		print "Login Failed"
		time.sleep(0.5)

	return authenticated       

def sendEmail(subject,body):
	image_name = "images/" + time.strftime("%d-%m-%y_%H-%M-%S") + ".jpg"
	camera.capture(image_name)
	recipients = userdb.emailList()
	gmail.subject = subject
	gmail.body = body
	gmail.addRecipients(recipients)
	gmail.addAttachments(image_name)
	gmail.send()                                

if __name__ == '__main__':    
	print userdb.emailList()
        if authenticate():
		curses.wrapper(MyApp)
	else:
		sys.exit("Unauthorized user")                   
  
