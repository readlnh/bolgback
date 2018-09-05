import subprocess
import datetime

def status():
    archivecmd = 'git status'
    process = subprocess.Popen(archivecmd, shell=True)
    process.wait()
    archivecmdreturncode = process.returncode
    if archivecmdreturncode != 0:
        print "error"
    else:
        add()

def add():
    archivecmd = 'git add --all'
    process = subprocess.Popen(archivecmd, shell=True)
    process.wait()
    archivecmdreturncode = process.returncode
    if archivecmdreturncode != 0:
        print "add error"
    else: 
        commit()

def commit():
    now_time = datetime.datetime.now()
    commitmessage = datetime.datetime.now().strftime('%Y-%m-%d')
    archivecmd = "git commit -m" + commitmessage 
    process = subprocess.Popen(archivecmd, shell=True)
    process.wait()
    archivecmdreturncode = process.returncode
    if archivecmdreturncode != 0:
        print "commit error"
    else: 
        push

def push():
    archivecmd = 'git push'
    process = subprocess.Popen(archivecmd, shell=True)
    process.wait()
    archivecmdreturncode = process.returncode
    if archivecmdreturncode != 0:
        print "push error"
    else: 
        print "success"

status()
