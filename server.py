import asyncore
import smtpd

import os
import logging
import logging.handlers

BIND_ADDRESS: str = '127.0.0.1'
BIND_PORT: int = 2525
RELAY_HOST: str = 'smtp.remote.com'
RELAY_PORT: int  = 25
ALLOW_RELAY_FROM: list = ['127.0.0.1']

LOG_FILE = 'smtp.log'
LOG_LEVEL = logging.INFO  # logging.DEBUG // .ERROR...

os.chdir(os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))))
LOG_PATH = os.path.join(os.getcwd(), LOG_FILE)

logging.basicConfig(
    format='%(asctime)s - [%(levelname)s] %(message)s',
    level=LOG_LEVEL,
    handlers=[
        logging.StreamHandler(),
        logging.handlers.RotatingFileHandler(
            LOG_PATH,
            maxBytes=10000000,   # 10 MB
            backupCount=5
        )
    ]
)
logger = logging.getLogger(__name__)


class RelayService(smtpd.PureProxy):

    def process_message(self, peer, mailfrom, rcpttos, data , **kwargs):
        logger.info(f'Receieved a message from {mailfrom} to {rcpttos} ({peer}) {data}')
        logger.debug(data)
        if not RelayService.is_whitelisted(peer=peer):
            logger.warning('Delivering peer not part of whitelist – rejecting')
            return
        refused = self._deliver(mailfrom, rcpttos, data)
        
    def is_whitelisted(peer: tuple) -> bool:
        return isinstance(peer, tuple) and len(peer) >= 1 and peer[0] in ALLOW_RELAY_FROM


if __name__ == "__main__":
    logger.info('Running mini-mail relay')
    smtp_server = RelayService(
        localaddr=(BIND_ADDRESS, BIND_PORT), 
        remoteaddr=(RELAY_HOST, RELAY_PORT), 
        data_size_limit=0
    )
    try:
        asyncore.loop()
    except KeyboardInterrupt:
        smtp_server.close()
