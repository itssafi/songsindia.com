import smtplib, socket


def send_email(from_addr, email_password, to_addr, subject, email_body):
    try:
        SMTP_SESSION = smtplib.SMTP('smtp.gmail.com', 587)
        SMTP_SESSION.ehlo()
        SMTP_SESSION.starttls()
        SMTP_SESSION.ehlo()
        print 'Connecting to Gmail...'
        print 'Connected to Gmail Successfully.'
        try:
            SMTP_SESSION.login(from_addr, email_password)
            print 'Login successful.'
        except smtplib.SMTPException, err:
            print 'Authentication failed'
            print err
            SMTP_SESSION.close()
    except (socket.error, socket.herror, smtplib.SMTPException), err:
        print 'Connection to Gmail failed !.'
        print err
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
        print "Email couldn't be sent"
        SMTP_SESSION.close()
    print 'Email sent successfully'
    SMTP_SESSION.close()