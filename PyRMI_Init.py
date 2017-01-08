#Import Libraries
import imaplib, email, datetime, os
from openpyxl import load_workbook

##########################################################################
###   User Email

#Login Information
mail = imaplib.IMAP4_SSL('imap.gmail.com')
mail.login('email', 'passkey')

#print(mail.list()) gives list of all "folders" aka labels in gmail.
mail.select('"Server/Leviathan"') #Connect to inbox, label Server/Leviathan - ensure label surrounded by both " and '

#User defined file names
FileNames = ["PrimaryKey.txt","Server Trends.xlsx"]

###
##########################################################################
###   File Directories - Mess around with this at your own risk

#Define path to where this script is
PyRMIPath = os.path.dirname(__file__)

#Primary Runtime Files and Primary Key
PrimKeyPath = os.path.join(PyRMIPath,FileNames[0])
wbName = os.path.join(PyRMIPath,FileNames[1])

#Load up files
PrimKey = open(PrimKeyPath,"w")
wb = load_workbook(wbName)

###
##########################################################################

#result is status of search for error checking, if required for any purpose
result, data = mail.search(None, "ALL")

#Fetches raw text of latest email body with some extra crap added to it -_-
body=mail.fetch(data[0].split()[-1],"(UID BODY[TEXT])")[1]

#To hold disk serials
adainfo=[]

#For each item split by SMART (some number of disks) except the first which is crap text and the last which should be da0 (USB boot)
for diskdat in str(body).split("S.M.A.R.T. [/dev/")[1:-1]:
    if diskdat[:2]=="da":
        continue

	#Extracts Serial of HDD
    adainfo.append((diskdat.split("Serial Number:")[1]).split("Firmware Version:")[0][:-4].strip())

adainfo.sort() #Then sort the Serial numbers - as this is also done in the base code

#Generate primkey file and initialize startdate of serer stats
iter=1
wb["Pool"].append([datetime.date.today(), 0, 0, 0])
PrimKey.write(str(datetime.date.today()) + "\r\n")  #.strftime("%B %d, %Y") + "\r\n")
for disks in adainfo:
	PrimKey.write(disks + "<=/=>0\r\n")
	wb["Disc " + str(iter)].append([datetime.date.today(), 0, 0, 0])
	iter+=1

PrimKey.close()
wb.save(wbName)
