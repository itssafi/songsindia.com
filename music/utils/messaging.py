import os
import time
import socket
import logging
import smtplib
from urllib.parse import urlparse
from twilio.rest import TwilioRestClient
from twilio.rest.resources import Connection
from twilio.rest.resources.connection import PROXY_TYPE_HTTP
from server.settings import EMAIL_HOST_NAME, EMAIL_HOST_PASSWORD

log = logging.getLogger(__name__)


class SendEmailMessage:

    def __init__(self, smtp_server, port, from_email, password):

        self.port = port
        self.password = password
        self.from_email = from_email
        self.smtp_server = smtp_server

    def __get_smtp_connection(self):
        try:
            log.info('Connecting to Gmail...')
            self.smtp_session = smtplib.SMTP(self.smtp_server, self.port)
            self.smtp_session.ehlo()
            self.smtp_session.starttls()
            self.smtp_session.ehlo()
            log.info('Connected to Gmail Successfully.')
            try:
                self.smtp_session.login(self.from_email, self.password)
                log.info('Administrator Gmail: login successful.')
                return True
            except smtplib.SMTPException as err:
                log.info('Administrator Gmail: Authentication failed !.')
                log.debug('Administrator Gmail: Authentication failed, reason: '.format(err))
                self.smtp_session.close()
                return False

        except (socket.error, socket.herror, smtplib.SMTPException) as err:
            log.info('Connection to Gmail failed !.')
            log.debug('Connection to Gmail failed, reason: {0}'.format(err))
            return False

    def send_email(self, to_addr, subject, email_body):
        if self.__get_smtp_connection():
            headers = "\r\n".join(["from: " + 'Songs India Team',
                                   "subject: " + subject,
                                   "reply-to: " + self.from_email,
                                   "to: " + to_addr,
                                   "mime-version: 1.0",
                                   "content-type: text/html"])
            # body_of_email can be plaintext or html!
            content = headers + "\r\n\r\n" + email_body
            try:
                self.smtp_session.sendmail(self.from_email, to_addr, content)
            except smtplib.SMTPException:
                log.debug("Email couldn't be sent to '{0}'".format(to_addr))
                self.smtp_session.close()
            log.debug("Email sent successfully to '{0}'".format(to_addr))
            self.smtp_session.close()


class SendTextMessage(object):

    def __init__(self, sid=None, token=None):
        # host, port = urlparse(os.environ["http_proxy"]).netloc.split(":")
        # Connection.set_proxy_info(host, int(port), proxy_type=PROXY_TYPE_HTTP)
        self.twilio_client = TwilioRestClient(sid, token)

    def validate_phone_number(self, phone_no):
        try:
            if self.twilio_client.caller_ids.list(phone_number=phone_no):
                log_message = "Phone number, '{0}' is already verified.".format(phone_no)
                log.debug(log_message)
                return None
            response = self.twilio_client.caller_ids.validate(phone_no)
            return int(response['validation_code'])
        except Exception as err:
            log.info("Phone number validation failed, reason: {0}".format(err))
            log.debug("Phone number validation failed, reason: {0}".format(err))
            return None

    def send_sms(self, from_no, to_no, body_msg):
        try:
            message = self.twilio_client.messages.create(body=body_msg, from_=from_no, to=to_no)
            time.sleep(2)
            for index in range(4):
                updated_message = self.twilio_client.messages.get(message.sid)
                if not updated_message.status:
                    log.debug("SMS is not delivered to '{0}'".format(to_no))
                    log.info("SMS is not delivered to '{0}', Retry attempt: {1}".format(to_no, index + 1))
                else:
                    log.debug('SMS is delivered successfully to {0}'.format(to_no))
                    return True
        except Exception as err:
            log.info("SMS couldn't be sent, reason: {0}".format(err))
            log.debug("SMS couldn't be sent, reason: {0}".format(err))
            return None
