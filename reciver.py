import os
import argparse
import ssl
import subprocess
import smtplib
from aiosmtpd.smtp import SMTP
from aiosmtpd.controller import Controller
from aiosmtpd.handlers import Debugging
from email import message_from_bytes
from email.policy import default


#------------Section for setingup cert and args--------------------------------
parser = argparse.ArgumentParser(description="Email reciver to handel reciving and QQ of the messages")
parser.add_argument("--ip", required=True)
parser.add_argument("--port", required=True) 
args = parser.parse_args()

# Create cert and key if they don't exist
if not os.path.exists(f'cert/{os.path.sep}cert.pem') and not os.path.exists(f'cert{os.path.sep}key.pem'):
    subprocess.call(f'openssl req -x509 -newkey rsa:4096 -keyout cert{os.path.sep}key.pem -out cert{os.path.sep}cert.pem ' +
                    '-days 365 -nodes -subj "/CN={}"', shell=True)
# Load SSL context
context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain(f'cert{os.path.sep}cert.pem', f'cert{os.path.sep}key.pem')

#------------------------------------------------------------------------------

class MessageHandler:
    async def handle_DATA(self, server, session, envelope):
        peer = session.peer
        mailfrom = envelope.mail_from
        rcpttos = envelope.rcpt_tos
        message = message_from_bytes(envelope.content, policy=default)
        #HERE MAYBE WOULD BE SAFER TO WALK CONTENTS AND PARSE/MODIFY ONLY MAIL BODY, BUT NO SIDE EFFECTS UNTIL NOW WITH MIME, ATTACHMENTS...
        messagetostring = message.as_string() ### smtplib.sendmail WANTED BYTES or STRING, NOT email OBJECT.
        print(messagetostring)
        server = smtplib.SMTP('smtp.gmail.com', 25)
        server.send_message(mailfrom, rcpttos, messagetostring) ### NEEDED TO INVERT ARGS ORDER
        server.quit()
        return '250 OK' ### ADDED RETURN

# Pass SSL context to aiosmtpd
class ControllerStarttls(Controller):
    def factory(self):
        return SMTP(self.handler, require_starttls=True, tls_context=context)
#---------------------------------runner---------------------------------------
if __name__ == "__main__":
    controller = ControllerStarttls(MessageHandler(), port=args.port,  hostname=args.ip)
    controller.start()
    subprocess.call(f'swaks -tls -f test@test.com -t test@test.com --server {args.ip}:{args.port}', shell=True)
    input('Running STARTTLS server. Press enter to stop.\n')
    controller.stop()
    
