from django.core.mail import send_mail as core_send_mail

import threading
import string
import random
from django.core.mail.message import EmailMultiAlternatives,DEFAULT_ATTACHMENT_MIME_TYPE
import os
import codecs
from django.utils.encoding import smart_str
import mimetypes


class EmailEncodeUTF8(EmailMultiAlternatives):
    def _create_attachment(self, filename, content, mimetype=None):
        """
        Converts the filename, content, mimetype triple into a MIME attachment
        object.
        """
        if mimetype is None:
            mimetype, _ = mimetypes.guess_type(filename)
            if mimetype is None:
                mimetype = DEFAULT_ATTACHMENT_MIME_TYPE
        attachment = self._create_mime_attachment(content, mimetype)
        if filename:
            attachment.add_header('Content-Disposition', 'attachment',
                filename=('utf-8','',filename)) # Changed here!!! 
        return attachment

    # def attach_file(self, path, mimetype=None):
    #         """Attaches a file from the filesystem."""
    #         filename = os.path.basename(path)
    #         filename = smart_str(filename)
    #         content = codecs.open(unicode(path,'utf-8'), 'rb','utf-8').read()
    #         self.attach(filename, content, mimetype)

class EmailThread(threading.Thread):
    def __init__(self, subject, body, from_email, recipient_list, fail_silently, html):
        self.subject = subject
        self.body = body
        self.recipient_list = recipient_list
        self.from_email = from_email
        self.fail_silently = fail_silently
        self.html = html
        threading.Thread.__init__(self)

    def run (self):
        msg = EmailMultiAlternatives(self.subject, self.body, self.from_email, self.recipient_list)
        if self.html:
          msg.attach_alternative(self.html, "text/html")
          msg.send(self.fail_silently)
          

def send_mail(subject, recipient_list, body='', from_email='daeseung23@gmail.com', fail_silently=False, html=None, *args, **kwargs):
  EmailThread(subject, body, from_email, recipient_list, fail_silently, html).start()

def email_auth_num():
    LENGTH = 8

    string_pool = string.ascii_letters + string.digits

    auth_num = ""
    for i in range(LENGTH):
        auth_num += random.choice(string_pool)
    return auth_num