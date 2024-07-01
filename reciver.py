import os
import argparse
import ssl
import subprocess
from aiosmtpd.smtp import SMTP
from aiosmtpd.controller import Controller
from aiosmtpd.handlers import Debugging

# Create cert and key if they don't exist
if not os.path.exists(f'cert/{os.path.sep}cert.pem') and not os.path.exists(f'cert{os.path.sep}key.pem'):
    subprocess.call(f'openssl req -x509 -newkey rsa:4096 -keyout cert{os.path.sep}key.pem -out cert{os.path.sep}cert.pem ' +
                    '-days 365 -nodes -subj "/CN=172.17.85.233"', shell=True)

# Load SSL context
context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain(f'cert{os.path.sep}cert.pem', f'cert{os.path.sep}key.pem')
class ExampleHandler:
    async def handle_RCPT(self, server, session, envelope, address, rcpt_options):
        if not address.endswith('@example.com'):
            return '550 not relaying to that domain'
        envelope.rcpt_tos.append(address)
        return '250 OK'

    async def handle_DATA(self, server, session, envelope):
        print(f'Message from {envelope.mail_from}')
        print(f'Message for {envelope.rcpt_tos}')
        print(f'Message data:\n{envelope.content.decode("utf8", errors="replace")}')
        print('End of message')
        return '250 Message accepted for delivery'


# Pass SSL context to aiosmtpd
class ControllerStarttls(Controller):
    def factory(self):
        return SMTP(self.handler, require_starttls=True, tls_context=context)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Email reciver to handel reciving and QQ of the messages")
    parser.add_argument("--ip", required=True)
    parser.add_argument("--port", required=True) 
    args = parser.parse_args()

    controller = ControllerStarttls(ExampleHandler(), port=args.port,  hostname=args.ip)
    controller.start()
    subprocess.call(f'swaks -tls -f test@test.com -t test@test.com --server {args.ip}:{args.port}', shell=True)
    input('Running STARTTLS server. Press enter to stop.\n')
    controller.stop()
    
