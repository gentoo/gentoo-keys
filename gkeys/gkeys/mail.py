from __future__ import print_function

import os
import smtplib
import sys
import email.utils

from email.mime.text import MIMEText
from snakeoil.demandload import demandload

if sys.version_info[0] >= 3:
    py_input = input
    _unicode = str
else:
    py_input = raw_input
    _unicode = unicode

demandload(
    "gkeys.base:Args",
    "json:load",
)

class Emailer(object):
    '''Send an email reminder about the status of the user's GPG key'''

    def __init__(self, login, logger):
        self.logger = logger
        self.email_from = _unicode(login['login_email'])
        self.sender_full_name = _unicode(login['full_name'])
        login_passwd = login['passwd']
        server = login['server']
        self.mail = smtplib.SMTP(server, 587)
        self.mail.ehlo()
        self.mail.starttls()
        self.mail.login(self.email_from, login_passwd)
        self.logger.debug(_unicode("Login successfull"))

    def send_email(self, uid, message):
        self.logger.debug(_unicode('Sending email with message %s') % _unicode(message))
        subject = "Expiring Key"
        email_to = uid
        msg = MIMEText(message, 'plain')
        msg['Subject'] = subject
        msg['From'] = email.utils.formataddr((self.sender_full_name, self.email_from))
        msg['To'] = email_to
        self.logger.info(_unicode('Sending the email reminder from %s to %s') \
            % (self.email_from, email_to))
        self.mail.sendmail(self.email_from, email_to, msg.as_string())

    def email_quit(self):
        self.mail.quit()
