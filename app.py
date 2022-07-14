# Copyright (c) 2018, 2019, 2020 President and Fellows of Harvard College.
# This file is part of ProvBuild.

# ProvBuild Interface
import os
import shutil
import re
import commands
import time 
import string
from flask import Flask, request, redirect, url_for, render_template,session
from werkzeug.utils import secure_filename
import threading
import webbrowser
from sys import platform
from shutil import copyfile

UPLOAD_FOLDER = '.'
ALLOWED_EXTENSIONS = set(['py'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = "HII"

def stripComments(code):
    return code

def cleanhtml(code):
	code = str(code)
	cleanrule = re.compile('<.*?>')
	cleantext = re.sub(cleanrule, '', code)
	return cleantext

def remove(path):
    """ param <path> could either be relative or absolute. """
    if os.path.isfile(path) or os.path.islink(path):
        os.remove(path)  # remove the file
    elif os.path.isdir(path):
        shutil.rmtree(path)  # remove dir and all contains

def getFuncname(line):
	flag = 0
	name = ""
	for i in line:
		if i == "'" and flag == 0:
			flag = 1
			continue
		elif i == "'" and flag == 1:
			break
		elif flag == 1:
			name += i
	return name

### normal test editor interface
@app.route('/normal', methods = ['GET', 'POST'])
def normal():
   if request.method == 'POST':
		user_file = request.files['file']
		user_file.save(secure_filename(user_file.filename))

		user_name = request.form['username']
		
		file = open("session.txt", "w")
		file.write(user_name + ":" + user_file.filename + ":" + "NORMAL")

		# initialize the first run, recall the time
		print 'run ' + user_file.filename + ': Execute '	+ user_file.filename
		timefile = open("time.txt", "a")
		timefile.write(user_name + "\t" + user_file.filename + "\n")
		timefile.write("NORMAL start first run: \t" + str(time.time()) + "\n")
		status, output = commands.getstatusoutput('python ' + user_file.filename)
		timefile.write("NORMAL end first run and we start here: \t" + str(time.time()) + "\n")

		return render_template('normal.html', 
		 					user_file=user_file.filename, 
		 					message="Initial Done", 
		 					content=open(user_file.filename, 'r').read(), 
		 					status=status, 
		 					result=open("result.txt", "r").read(),
		 					output=output)

### normal execution
@app.route("/runnormal", methods=['POST'])
def runnormal():
	file = open("session.txt", "r") 
	info = file.readline().split(":")
	username = info[0]
	filename = info[1] 

	f= open(filename, 'w')
	code = request.form['script'].replace("<br>", "\n").replace("<div>", "\n").replace("</div>", "\n")
	finalcode = cleanhtml(code)
	finalcode = finalcode.replace("&gt;", ">").replace("&lt;", "<")
	f.write(finalcode)
	f.close()

	# execute the script
	print 'run '	+ filename + ': Execute '	+ filename
	timefile = open("time.txt", "a")
	timefile.write("NORMAL start run: \t" + str(time.time())  + "\n")
	status, output = commands.getstatusoutput('python '	+ filename)
	timefile.write("NORMAL end run: \t" + str(time.time())  + "\n")

	return render_template('normal.html', 
							user_file=filename, 
							message="Execute Done", 
							content=open(filename, 'r').read(), 
							status=status, 
							result=open("result.txt", "r").read(),
							output=output)

### finalize the result and time record
@app.route("/finish", methods=['POST'])
def finish():
	# update finish time
	timefile = open("time.txt", "a")
	timefile.write("NORMAL finish: \t" + str(time.time())  + "\n")
	timefile.write("--------------------------------------\n")

	file = open("session.txt", "r") 
	info = file.readline().split(":")
	username = info[0]
	filename = info[1] 

	remove(filename)

	return render_template('index.html')

### ProvBuild mode text editor interface
@app.route('/provbuild', methods = ['GET', 'POST'])
def provbuild():
   if request.method == 'POST':
		user_file = request.files['file']
		user_file.save(secure_filename(user_file.filename))

		user_name = request.form['username']
		
		file = open("session.txt", "w")
		file.write(user_name + ":" + user_file.filename + ":" + "PROVBUILD")

		print 'run ' + user_file.filename + ': Execute ' + user_file.filename
		timefile = open("time.txt", "a")
		timefile.write(user_name + "\t" + user_file.filename + "\n")
		timefile.write("PROVBUILD start first run: \t" + str(time.time()) + "\n")
		remove(".noworkflow")
		status, output = commands.getstatusoutput('python __init__.py run ' + user_file.filename)
		timefile.write("PROVBUILD end first run and we start here: \t" + str(time.time()) + "\n")

		f = open('ProvScript.py', 'w')
		initcode = "# This is the function declaration part\n# - Your previous script contains the following function definitions:\n###\n# This is the global variable declaration part\n# - Your previous script contains the following global variable:\n###\n\n# This is the parameter setup part\n# - We are going to setup the function parameters to make this script runnable\n# - Change the following values is useless\n\n# ProvScript Initialization\n"
		f.write(initcode)
		f.close()

		return render_template('provbuild.html', 
		 					user_file=user_file.filename, 
		 					message="Initial Done", 
		 					content=open(user_file.filename, 'r').read(), 
		 					status=status, 
		 					result=open("result.txt", "r").read(),
		 					output=output, 
		 					provscript=stripComments(open("ProvScript.py", "r").read().split("# This is the parameter setup part", 1)[1]))

### given function/variable modification
@app.route("/update", methods=['POST'])
def update():
	file = open("session.txt", "r") 
	info = file.readline().split(":")
	username = info[0]
	filename = info[1] 

	if not request.form['func_var']: 
		return render_template('provbuild.html', 
			user_file=filename, 
			message="unable to execute search -- no variable or function name", 
			content=session['content'], 
			status="", 
			result=open("result.txt", "r").read(),
			output="Please enter a variable or function name and click the 'search' button to generate a ProvScript.", 
			provscript="Please enter a variable or function name and click the 'search' button to generate a ProvScript.")	

	ret = request.form['func_var']
	file = open("session.txt", "a") 
	command = "python __init__.py update -t 1"
	if ret == 'function': 
		command += " -fn " + request.form['func_var_text'] + " --debug 0"
		file.write(":f:" + request.form['func_var_text'])
	elif ret == 'variable': 
		command += " -vn " + request.form['func_var_text'] + " --debug 0"
		file.write(":v:" + request.form['func_var_text'])

	
	print 'explore ' + filename + ": " + command
	timefile = open("time.txt", "a")
	timefile.write("PROVBUILD start update: \t" + str(time.time())  + "\n")
	status, output = commands.getstatusoutput(command)
	timefile.write("PROVBUILD end update: \t" + str(time.time())  + "\n")

	return render_template('provbuild.html', 
					user_file=filename, 
					message="Search Done: " + request.form['func_var_text'],
					content=open(filename, 'r').read(), 
					status=status, 
					result=open("result.txt", "r").read(),
					output=output, 
					provscript=stripComments(open("ProvScript.py", "r").read().split("# This is the parameter setup part", 1)[1]))

### ProvScript execution
@app.route("/runupdate", methods=['POST'])
def runupdate():
	file = open("session.txt", "r") 
	info = file.readline().split(":")
	username = info[0]
	filename = info[1] 
	fvtype = info[-2]
	fvname = info[-1]

	f = open('ProvScript.py', 'w')
	code = request.form['provscript'].replace("<br>", "\n").replace("<div>", "\n").replace("</div>", "\n")
	finalcode = cleanhtml(code)
	finalcode = finalcode.replace("&gt;", ">").replace("&lt;", "<")
	f.write(finalcode)
	f.close()

	# execute ProvScript.py
	print 'run ProvScript.py: ' + 'Execute ProvScript.py' 
	timefile = open("time.txt", "a")
	timefile.write("PROVBUILD start runupdate: \t" + str(time.time())  + "\n")
	status, output = commands.getstatusoutput('python ProvScript.py')
	print(status)
	print(output)
	errorflag = 0
	while status != 0:
		timefile.write("PROVBUILD end runupdate (need regeneration): \t" + str(time.time())  + "\n")
		if "NameError" in output and "is not defined" in output:
			lines = output.split('\n')
	        	funcname = getFuncname(lines[-1])

	        	print 'regenerate ProvScript.py: Regenerate ProvScript.py'
	        	timefile = open("time.txt", "a")
	        	timefile.write("PROVBUILD start regenerate: \t" + str(time.time())  + "\n")
	        	status, output = commands.getstatusoutput('python __init__.py regen -t 1 -f ' + funcname)
	        	timefile.write("PROVBUILD end regenerate: \t" + str(time.time())  + "\n")
	        	if "UNFOUND" in output:
	        		errorflag = 1
	        		break

	        	timefile.write("PROVBUILD start runupdate: \t" + str(time.time())  + "\n")
	        	status, output = commands.getstatusoutput('python ProvScript.py')
        	else: 
        		errorflag = 1
			break

	timefile.write("PROVBUILD end runupdate: \t" + str(time.time())  + "\n")
	if errorflag == 0:
		return render_template('provbuild.html', 
						user_file=filename, 
						message="Execute Done", 
						content=open(filename, 'r').read(), 
						status=status, 
						result=open("result.txt", "r").read(),
						output=output, 
						provscript=stripComments(open("ProvScript.py", "r").read()))
	else:
		return render_template('provbuild.html', 
						user_file=filename, 
						message="Unknown Error", 
						content=open(filename, 'r').read(), 
						status=status, 
						result="",
						output=output, 
						provscript="Unknown Error")

### merge ProvScript into the original script
@app.route("/merge", methods=['POST'])
def merge():
	# update merge time
	print 'merge: ' + ' Merge ProvScript into the original'
	timefile = open("time.txt", "a")
	timefile.write("PROVBUILD start merge: \t" + str(time.time()) + "\n")
	status, output = commands.getstatusoutput('python __init__.py merge -t 1')
	timefile.write("PROVBUILD end merge: \t" + str(time.time()) + "\n")

	file = open("session.txt", "r") 
	info = file.readline().split(":")
	username = info[0]
	filename = info[1] 
	# merge output - new script
	newfilename = "new-" + filename

	# keep the current script for second try
	copyfile(newfilename, filename)
	remove(newfilename)

	# generate provenance for new file
	print 'now we generate new provenance'
	print 'run ' + filename + ': Execute ' + filename
	timefile = open("time.txt", "a")
	timefile.write("PROVBUILD start another run: \t" + str(time.time()) + "\n")
	remove(".noworkflow")
	status, output = commands.getstatusoutput('python __init__.py run ' + filename)
	timefile.write("PROVBUILD end another run: \t" + str(time.time()) + "\n")


	newfile = open(filename, "r") 
	return render_template('provbuild.html', 
						user_file=filename, 
						message="Merge Done", 
						content=open(filename, 'r').read(),
						status=status, 
						result=open("result.txt", "r").read(),
						output=output, 
						provscript="Please enter a variable or function name and click the 'search' button to generate a ProvScript.")

### finalize the result and time record
@app.route("/provfinish", methods=['POST'])
def provfinish():
	# update finish time
	timefile = open("time.txt", "a")
	timefile.write("PROVBUILD finish: \t" + str(time.time())  + "\n")
	timefile.write("--------------------------------------\n")

	file = open("session.txt", "r") 
	info = file.readline().split(":")
	username = info[0]
	filename = info[1] 

	remove(filename)
	remove(".noworkflow")

	return render_template('index.html')


### main interface
@app.route("/")
def main():
	open('result.txt', 'w').close()
	return render_template('index.html')

if __name__ == "__main__":
	url = "http://127.0.0.1:5000"
	threading.Timer(1.25, lambda: webbrowser.open(url)).start()
	app.run(host='0.0.0.0',port=5000)
