import smtplib, socket, logging


log = logging.getLogger(__name__)


def send_email(from_addr, email_password, to_addr, subject, email_body):
    try:
        log.info('Connecting to Gmail...')
        SMTP_SESSION = smtplib.SMTP('smtp.gmail.com', 587)
        SMTP_SESSION.ehlo()
        SMTP_SESSION.starttls()
        SMTP_SESSION.ehlo()
        log.info('Connected to Gmail Successfully.')
        try:
            SMTP_SESSION.login(from_addr, email_password)
            log.info('Administrator Gmail: login successful.')
        except smtplib.SMTPException, err:
            log.info('Administrator Gmail: Authentication failed !.')
            log.debug('Administrator Gmail: Authentication failed, reason: '.format(err))
            SMTP_SESSION.close()
    except (socket.error, socket.herror, smtplib.SMTPException), err:
        log.info('Connection to Gmail failed !.')
        log.debug('Connection to Gmail failed, reason: {0}'.format(err))
        return
        
    headers = "\r\n".join(["from: " + 'Songs India Team',
                           "subject: " + subject,
                           "reply-to: " + from_addr,
                           "to: " + to_addr,
                           "mime-version: 1.0",
                           "content-type: text/html"])
    # body_of_email can be plaintext or html!                                                                                                       
    content = headers + "\r\n\r\n" + email_body
    try:
        SMTP_SESSION.sendmail(from_addr, to_addr, content)
    except smtplib.SMTPException:
        log.debug("Email couldn't be sent to '{0}'".format(to_addr))
        SMTP_SESSION.close()
    log.debug("Email sent successfully to '{0}'".format(to_addr))
    SMTP_SESSION.close()