#!/usr/bin/env python
# -*- coding: utf-8; -*-

##  This file is part of the t4 Python module collection. 
##
##  Copyright 2003-2021 by Diedrich Vorberg <diedrich@tux4web.de>
##
##  All Rights Reserved
##
##  For more Information on orm see the README file.
##
##  This program is free software; you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software Foundation; either version 2 of the License, or
##  (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUtest@test.deT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License
##  along with this program; if not, write to the Free Software
##  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
##
##  I have added a copy of the GPL in the file COPYING


import sys, os, os.path as op, types, smtplib, socket, subprocess

from t4.res import email_re

try:
    from ll.xist import xsc
except ImportError:
    xsc = None

from email import encoders
from email.message import Message
from email.mime.base import MIMEBase
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from email.header import Header

# Send UTF-8 text parts encoded Quoted Printable (rather than base64)
from email import charset
charset.add_charset("utf-8", charset.SHORTEST, charset.QP)


class sendmail_attachment:
    def __init__(self, filename, data, mime_type=None,
                 content_disposition="attachment", headers={}):
        self.filename = filename
        self.data = data

        if mime_type is None:
            mime_type, encoding = mimetypes.guress_type(filename)
            if mime_type is None or encoding is None:
                mime_type = "application/octet-stream"
                
        self.mime_type = mime_type
        self.content_disposition = content_disposition
        self.headers = headers

    def part(self):
        maintype, subtype = self.mime_type.split("/", 1)
        if maintype == "text":
            # Note: we should handle calculating the charset
            msg = MIMEText(self.data, _subtype=subtype)
        elif maintype == "image":
            msg = MIMEImage(self.data, _subtype=subtype)
        elif maintype == "audio":
            msg = MIMEAudio(self.data, _subtype=subtype)
        else:
            msg = MIMEBase(maintype, subtype)
            msg.set_payload(self.data)
            # Encode the payload using Base64
            encoders.encode_base64(msg)
            
        # Set the filename parameter
        msg.add_header("Content-Disposition",
                       self.content_disposition,
                       filename=self.filename)

        for key, value in self.headers.items():
            msg.add_header(key, value)
        
        return msg

    
def sendmail(from_name, from_email,
             to_name, to_email,
             subject, message, attachments=[], headers={}, bcc=[],             
             text_subtype="plain", encoding="utf-8", multipart_subtype="mixed"):
    # Verify all the e-Mail Addresses
    def verify_email_address(email):
        if email_re.match(email) is None:
            raise ValueError("Not a valid e-mail address: %s" % repr(email))

    map(verify_email_address, bcc)
    verify_email_address(from_email)
    verify_email_address(to_email)
        
    if xsc is not None and isinstance(message, xsc.Node):
        message = message.string(encoding=encoding)
        if text_subtype == "plain":
            text_subtype = "html"

    if isinstance(message, MIMEBase):
        outer = message

        if len(attachments) > 0:
            raise ValueError("Can’t have sendmail()-style attachments "
                             "when supplying your own email.mime.MIME* "
                             "instance as message.")
    else:
        textpart = MIMEText(message, text_subtype, encoding)
    
        if len(attachments) == 0:
            outer = textpart
        else:
            outer = MIMEMultipart(multipart_subtype)
            outer.attach(textpart)

        
    outer["Subject"] = Header(subject)
    outer["To"] = formataddr( (to_name, to_email,) )
    outer["From"] = formataddr( (from_name, from_email,) )
    
    for name, value in headers.items():
        outer[name] = value

    if not outer.preamble:
        outer.preamble = "You will not see this in a MIME-aware mail reader.\n"

    for a in attachments:
        assert isinstance(a, sendmail_attachment), TypeError
        outer.attach(a.part())

    composed = outer.as_string()

    if socket.gethostname().startswith("leela."):
        s = smtplib.SMTP("hermes.tux4web.de")
        s.sendmail(from_email, to_email, composed)
        for email in bcc: s.sendmail(from_email, email, composed)
        s.quit()
    else:
        state = subprocess.run(
            ["/usr/sbin/sendmail",
             "-f", from_email, # Set the envelope sender.
             to_email] + bcc,
            input=composed,
            capture_output=True,
            encoding="utf-8")

        if state.returncode != 0: raise IOError(state.stderr)
    
