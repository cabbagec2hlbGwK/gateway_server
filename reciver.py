from email.message import EmailMessage
import requests
import base64
import os
import argparse
import ssl
import subprocess
import smtplib
from aiosmtpd.smtp import SMTP
from aiosmtpd.controller import Controller
from email import message_from_bytes
from email.policy import default


#------------Section for setingup cert and args--------------------------------
parser = argparse.ArgumentParser(description="Email reciver to handel reciving and QQ of the messages")
parser.add_argument("--ip", required=True)
parser.add_argument("--port", required=True) 
parser.add_argument("--api", required=True) 
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
        body = message.get_payload()
        emailMess = None
        attachments = list()
        if not isinstance(body, str) and len(body)>1:
            emailMess = body[0]
            attachments = body[1:]
        else:
            emailMess = body
        print(f"Message: {emailMess}, Attachments: {len(attachments)}")

        for attachment in attachments:
            metadata = attachment.get("Content-Type").split(";")
            contentType = metadata[0].strip()
            name = metadata[1].split("=")[1].replace('"','').strip()
            files =  {'test': (name, base64.b64decode(attachment.get_payload()), contentType)}
            url = f"http://{args.api}:5000/extract"
            res = requests.post(url, files=files)
            print(type(res.text))

        with smtplib.SMTP(host='smtp-relay.gmail.com', port=587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.send_message(message, mailfrom, rcpttos)
            smtp.quit()
        return '250 OK' ### ADDED RETURN

# Pass SSL context to aiosmtpd
class ControllerStarttls(Controller):
    def factory(self):
        return SMTP(self.handler, require_starttls=True, tls_context=context)



#---------------------------------runner---------------------------------------
if __name__ == "__main__":
    controller = ControllerStarttls(MessageHandler(), port=args.port,  hostname=args.ip)
    controller.start()
    input('Running STARTTLS server. Press enter to stop.\n')
    controller.stop()
    
