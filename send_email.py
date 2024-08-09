# Import smtplib for the actual sending function
import smtplib
import sys
import getpass

assert sys.version_info.major >= 3

# Import the email modules we'll need
from email.message import EmailMessage

# Create a text/plain message
msg = EmailMessage()
msg.set_content(sys.argv[4])

# me == the sender's email address
# you == the recipient's email address
msg['Subject'] = sys.argv[3]
msg['From'] = sys.argv[1]
msg['To'] = sys.argv[2]

username = input('Username: ')
password = getpass.getpass()

s = smtplib.SMTP('smtp.office365.com', 587)
s.set_debuglevel(1)
s.starttls()
s.login(username, password)
s.send_message(msg)
s.quit()
