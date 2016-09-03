import os, time, logging
from urlparse import urlparse
from twilio.rest import TwilioRestClient
from twilio.rest.resources import Connection
from twilio.rest.resources.connection import PROXY_TYPE_HTTP

log = logging.getLogger(__name__)


class SendTextMessage(object):

    def __init__(self, sid=None, token=None):
        host, port = urlparse(os.environ["http_proxy"]).netloc.split(":")
        Connection.set_proxy_info(host, int(port), proxy_type=PROXY_TYPE_HTTP)
        self.twilio_client = TwilioRestClient(sid, token)

    def validate_phone_number(self, phone_no):
        try:
            if self.twilio_client.caller_ids.list(phone_number=phone_no):
                log_message = "Phone number, '{0}' is already verified.".format(phone_no)
                log.debug(log_message)
                return None
            response = self.twilio_client.caller_ids.validate(phone_no)
            return int(response['validation_code'])
        except Exception, err:
            log.info("Phone number validation failed, reason: {0}".format(err))
            log.debug("Phone number validation failed, reason: {0}".format(err))
            return None

    def send_sms(self, from_no, to_no, body_msg):
        try:
            message = self.twilio_client.messages.create(body=body_msg,
                from_=from_no, to=to_no)
            time.sleep(2)
            for index in range(4):
                updated_message = self.twilio_client.messages.get(message.sid)
                if not updated_message.status:
                    log.debug("SMS is not delivered to '{0}'".format(to_no))
                    log.info("SMS is not delivered to '{0}', Retry attempt: {1}".format(to_no, index + 1))
                else:
                    log.debug('SMS is delivered successfully to {0}'.format(to_no))
                    return True
        except Exception, err:
            log.info("SMS couldn't be sent, reason: {0}".format(err))
            log.debug("SMS couldn't be sent, reason: {0}".format(err))
            return None
