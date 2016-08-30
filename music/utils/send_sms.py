import os, time
from urlparse import urlparse
from twilio.rest import TwilioRestClient
from twilio.rest.resources import Connection
from twilio.rest.resources.connection import PROXY_TYPE_HTTP


class SendTextMessage(object):

    def __init__(self, sid=None, token=None):
        # host, port = urlparse(os.environ["http_proxy"]).netloc.split(":")
        # Connection.set_proxy_info(host, int(port), proxy_type=PROXY_TYPE_HTTP)
        self.twilio_client = TwilioRestClient(sid, token)

    def validate_phone_number(self, phone_no):
        try:
            response = self.twilio_client.caller_ids.validate(phone_no)
            return int(response['validation_code'])
        except Exception, err:
            print err
            return None

    def send_sms(self, from_no, to_no, body_msg):
        try:
            message = self.twilio_client.messages.create(body=body_msg,
                from_=from_no, to=to_no)
            time.sleep(2)
            updated_message = self.twilio_client.messages.get(message.sid)
            if not updated_message.status:
                print 'SMS not delivered to {0}'.format(to_no)
                return False

            print 'SMS delivered successfully to {0}'.format(to_no)
            return True
        except Exception, err:
            print err
            return None
