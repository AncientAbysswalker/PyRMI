#  ____                                             _                      _           _     _              
# / ___|    ___   _ __  __   __   ___   _ __       / \     _ __     __ _  | |  _   _  | |_  (_)   ___   ___ 
# \___ \   / _ \ | '__| \ \ / /  / _ \ | '__|     / _ \   | '_ \   / _` | | | | | | | | __| | |  / __| / __|
#  ___) | |  __/ | |     \ V /  |  __/ | |       / ___ \  | | | | | (_| | | | | |_| | | |_  | | | (__  \__ \
# |____/   \___| |_|      \_/    \___| |_|      /_/   \_\ |_| |_|  \__,_| |_|  \__, |  \__| |_|  \___| |___/
#                                                                              |___/                        
#  ____   __   __       ____    __  __     ___           _                    __                       
# |  _ \  \ \ / /      |  _ \  |  \/  |   |_ _|  _ __   | |_    ___   _ __   / _|   __ _    ___    ___ 
# | |_) |  \ V /   __  | |_) | | |\/| |    | |  | '_ \  | __|  / _ \ | '__| | |_   / _` |  / __|  / _ \
# |  __/    | |   |__| |  _ <  | |  | |    | |  | | | | | |_  |  __/ | |    |  _| | (_| | | (__  |  __/
# |_|       |_|        |_| \_\ |_|  |_|   |___| |_| |_|  \__|  \___| |_|    |_|    \__,_|  \___|  \___|
#                                                                                                        
#  __  __                  _        _____       _       ____  
# |  \/  |   __ _   _ __  | | __   |___ /      / |     |___ \ 
# | |\/| |  / _` | | '__| | |/ /     |_ \      | |       __) |
# | |  | | | (_| | | |    |   <     ___) |  _  | |  _   / __/ 
# |_|  |_|  \__,_| |_|    |_|\_\   |____/  (_) |_| (_) |_____|


#The following are useful links that were used in initial development
#https://yuji.wordpress.com/2011/06/22/python-imaplib-imap-example-with-gmail/
#http://www.voidynullness.net/blog/2013/07/25/gmail-email-with-python-via-imap/
#http://stackoverflow.com/questions/19540192/imap-get-sender-name-and-body-text

#!/usr/bin/python2.7
# -*- coding: utf8 -*-

#Import Libraries
import imaplib, datetime
from os import path
from openpyxl import load_workbook
from collections import namedtuple
from math import ceil

#Define namedtuple to hold disk information
hardDisk=namedtuple('hardDisk',['Brand','Serial','Ada','errMaj','errMin','errStr','errList','timLast','timNew','timDel'])

##########################################################################
###   User Email

#Login Information
mail = imaplib.IMAP4_SSL('imap.gmail.com')
mail.login('email', 'passkey')

#Select folder/label to search - print(mail.list()) gives list of all "folders" aka labels if needed
mail.select('"Server/Leviathan"') #Ensure label surrounded by both " and '

#User defined file names
FileNames = ["PrimaryKey.txt","HumanSummary.txt","RM_LevVar.txt","Server Trends.xlsx"]

###
##########################################################################
###   File Directories - Mess around with this at your own risk

#Define path to where this script is
PyRMIPath = path.dirname(__file__)

#Primary Runtime Files and Primary Key
PrimKeyPath = path.join(PyRMIPath,FileNames[0])
SummaryPath = path.join(PyRMIPath,FileNames[1])
RainmeterPath = path.join(PyRMIPath,FileNames[2])
wbName = path.join(PyRMIPath,FileNames[3])

#Load up files
Summary = open(SummaryPath,"w")
Rainmeter = open(RainmeterPath,"w")
wb = load_workbook(wbName)

#Digest Primkey data
PrimKey = open(PrimKeyPath,"r")
timStmp=((PrimKey.read()).strip()).splitlines()
print( timStmp )
[lastDate,timStmp]=[timStmp[0],timStmp[1:]]
timStmp[:] = [disc.split("<=/=>") for disc in timStmp]
print(  repr(timStmp) )
PrimKey.close()
PrimKey = open(PrimKeyPath,"w")

###
##########################################################################



#result is status of search for error checking, if required for any purpose
result, data = mail.search(None, "ALL")

#Fetches raw text of latest email body with some extra crap added to it -_- Then logout of email
body=mail.fetch(data[0].split()[-1],"(UID BODY[TEXT])")[1]
mail.close()

#Locate datapool usage and convert to bytes
[_,_,SpUse,body]=((str(body).split("ZFS pool list")[1]).split("\\r\\n",3)[3]).split(None,3)	#Looks at text after "ZFS pool list" > split the body by three newlines and use the text afterwards > split the text by 3 unknown length whitespaces and return the four strings to the array
SpUse+='B'

#Locate Scrubbing Data
[_,scrubFix,_,_,_,scrubErr,body]=(body.split("scan: scrub rep")[1]).split(' ',6)	#Look for scrub flag and split with 6 whitespaces to get num of fixes and unfixable errors 

#To hold ada disk info for following code
diskInfo=[]

#Error flag in case ANY drive has a major error
errflag=0

#For each item split by SMART (some number of disks) except the first which is crap text and the last which should be da0 (USB boot)
for diskdat in body.split("S.M.A.R.T. [/dev/")[1:-1]:
	errDiscMajor=0
	errDiscMinor=0
	if diskdat[:2]=="da":
		continue
	
	discAda=diskdat[:4] #Temp var to hold ada number
	errString="" #Temp var to store all the error codes
	
	#Extracts Manufacturer and Model of HDD - Alternatively use "Device Model:" and "Serial Number:" to get model number
	discName=(diskdat.split("Model Family:")[1]).split("Device Model:")[0][:-4].strip()
	#Extracts Serial of HDD
	discSerial=(diskdat.split("Serial Number:")[1]).split("Firmware Version:")[0][:-4].strip()
	#Extracts Time Running
	discTimeNew=int((((diskdat.split("9 Power_On_")[1]).split("\r\n")[0]).split("-")[1]).split("h+")[0].strip())
	#Extract Timestamp from last running
	for sublist in timStmp:
		if sublist[0] == discSerial:
			discTimeLast=int(sublist[1])
	
	#Split remaining text into their respective errors and look at them all ignoring the first garbage text
	diskdat=diskdat.split("\\r\\n\\r\\nError ")
	
	errList=[]
	
	for errlog in diskdat[1:]:
	#if time of error is newer
		if int((errlog.split("lifetime: ",1)[1]).split(" hours")[0]) > discTimeLast:
			errString+="  Error " + errlog.split(' ',1)[0] + " @ " + (errlog.split("lifetime: ",1)[1]).split(')',1)[0] + ")\r\n"
			errList.append(["Error " + errlog.split(' ',1)[0]  ,  (errlog.split("lifetime: ",1)[1]).split(' hours',1)[0]])
			if errlog.split(' ',1)[0]=='5' or errlog.split(' ',1)[0]=='187' or errlog.split(' ',1)[0]=='188' or errlog.split(' ',1)[0]=='197' or errlog.split(' ',1)[0]=='198':
				errDiscMajor+=1 #Bad error found
				errflag=1
			else:
				errDiscMinor+=1
	
	#Append all data for current disk into struct
	diskInfo.append(hardDisk(discName,discSerial,discAda,errDiscMajor,errDiscMinor,errString,errList[::-1],discTimeLast,discTimeNew,discTimeNew-discTimeLast))
diskInfo.sort() #Then sort it by Serial number - used to be by ada but ada can change

#Write all data to the rainmeter data file or the summary file
Rainmeter.write("[Variables]\r\npoolUse=" + str(SpUse) + "\r\nscrubFix=" + scrubFix + "\r\nscrubErr=" + scrubErr + '\r\nlastDate="' + (datetime.date.today()).strftime("%B %d, %Y") + '"')
Summary.write("Scrubing of datapool repaired " + scrubFix + " and found " + scrubErr + " to be unrepairable.\r\n")


maxTime=max(disks.timDel for disks in diskInfo)

wb["Pool"].append([datetime.datetime.strptime(lastDate,"%Y-%m-%d").date(), 168*(ceil(maxTime)/168)-maxTime, int(scrubFix), int(scrubErr)])
wb["Pool"].append([datetime.date.today(), 168*(ceil(maxTime)/168)-maxTime, int(scrubFix), int(scrubErr)])
wb["Pool"].append([datetime.date.today(), 0, 0, 0])

#Write SMART output for RM
if errflag==1:
	Rainmeter.write('\r\nSMART="Serious problems with pool disks were identified"')
else:
	Rainmeter.write('\r\nSMART="No serious problems were found with pool disks"')
	
iter=1
PrimKey.write(str(datetime.date.today()) + "\r\n")
for disks in diskInfo:
	Summary.write("<" + disks.Brand.split(' ')[0] + " " + disks.Serial + ">-------------------------------------------<" + disks.Ada + ">\r\n" + disks.errStr + "\r\n")
	PrimKey.write(disks.Serial + "<=/=>" + str(disks.timNew) + "\r\n")
	
	wb["Disc " + str(iter)].append([datetime.datetime.strptime(lastDate,"%Y-%m-%d").date(), maxTime-disks.timDel, disks.errMin, disks.errMaj])
	wb["Disc " + str(iter)].append([datetime.date.today(), maxTime-disks.timDel, disks.errMin, disks.errMaj])
	wb["Disc " + str(iter)].append([datetime.date.today(), 0, 0, 0])
	for errors in disks.errList:
		wb["Disc " + str(iter) + " SMART"].append(['','',errors[0],(datetime.datetime.now()-datetime.timedelta(days=7)+datetime.timedelta(hours=(int(errors[1])-disks.timLast))).strftime("%b %d, %Y %H") + u":00 ± " + str(0) + "hours",errors[1]])
	iter+=1

Summary.close()
Rainmeter.close()
wb.save(wbName)