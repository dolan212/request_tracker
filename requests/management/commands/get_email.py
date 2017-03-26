import email
import logging
import mailbox
from os import listdir, unlink
from time import ctime

import re

from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.management import BaseCommand
from django.utils.translation import ugettext as _
from django.utils import six
from email_reply_parser import EmailReplyParser
from os.path import join, isfile

from request_tracker import settings
from requests import views
from requests.models import Queue, Ticket, Update

STRIPPED_SUBJECT_STRINGS = [
    "Re: ",
    "Fw: ",
    "RE: ",
    "FW: ",
]


class Command(BaseCommand):
    def __init__(self):
        BaseCommand.__init__(self)

    def handle(self, *args, **kwargs):
        process_email()

def process_email():
    for q in Queue.objects.filter(email_box_type__isnull=False):
        logger = logging.getLogger('django.requests.queue.' + q.name)
        logger.setLevel(logging.DEBUG)
        print "Processing queue " + q.name
        process_queue(q, logger=logger)


def process_queue(q, logger):
    logger.info("**** %s: Begin processing mail for requests" % ctime())

    # email_box_type = settings.QUEUE_EMAIL_BOX_TYPE or q.email_box_type
    #
    # if email_box_type == 'pop3':
    #     server = poplib.POP3_SSL(q.email_box_host or settings.QUEUE_EMAIL_BOX_HOST, int(q.email_box_port))
    #
    #     print ("Attempting POP3 server login")
    #     server.getwelcome()
    #     server.user(q.email_box_user or settings.QUEUE_EMAIL_BOX_USER)
    #     server.pass_(q.email_box_password or settings.QUEUE_EMAIL_BOX_PASSWORD)
    #
    #     messagesInfo = server.list()[1]
    #     print ("Received %d messages from POP3 server" % len(messagesInfo))
    #
    #     for msg in messagesInfo:
    #         msgNum = msg.split(" ")[0]
    #         logger.info("Processing message %s" % msgNum)
    #
    #         full_message = "\n".join(server.retr(msgNum)[1])
    #         ticket = ticket_from_message(message=full_message, queue=q, logger=logger)
    #
    #         if ticket:
    #             server.dele(msgNum)
    #             logger.info("Successfully processed message %s, deleted from POP3 server" % msgNum)
    #         else:
    #             logger.warn("Message %s was not successfully processed, and will be left on POP3 server" % msgNum)
    #
    #     server.quit()
    #
    # elif email_box_type == 'imap':
    #     server = imaplib.IMAP4_SSL(q.email_box_host or settings.QUEUE_EMAIL_BOX_HOST, int(q.email_box_port))
    #
    #     logger.info("Attempting IMAP server login")
    #
    #     server.login(q.email_box_user or settings.QUEUE_EMAIL_BOX_USER,
    #                  q.email_box_password or settings.QUEUE_EMAIL_BOX_PASSWORD)
    #     #pray that box type isn't IMAP

   # elif email_box_type == 'local':

    mbox = mailbox.mbox(settings.MAILBOX_PATH)

    logger.info("Found %d messages in local mailbox directory" % len(mbox))
    to_remove = []
    for key, message in mbox.iteritems():
        logger.info("Processing message %s" % key)
        ticket = ticket_from_message(message=message, queue=q, logger=logger)
        if ticket:
            to_remove.append(key)
            logger.info("Successfully processed message %s, deleting" % key)
        else:
            logger.warn("Could not process message %s, leaving in mbox" % key)

    mbox.lock()
    try:
        for key in to_remove:
            mbox.remove(key)
        mbox.flush()
    except:
        logger.error("Could not delete messages from mbox")
    finally:
        mbox.close()
        mbox.unlock()

def decodeUnknown(charset, string):
    if six.PY2:
        if not charset:
            try:
                return string.decode('utf-8', 'ignore')
            except:
                return string.decode('iso8859-1', 'ignore')
        return unicode(string, charset)
    elif six.PY3:
        if type(string) is not str:
            if not charset:
                try:
                    return str(string, encoding='utf-8', errors='replace')
                except:
                    return str(string, encoding='iso8859-1', errors='replace')
            return str(string, encoding=charset, errors='replace')
        return string

def decode_mail_headers(string):
    decoded = email.header.decode_header(string)
    if six.PY2:
        return u' '.join([unicode(msg, charset or 'utf-8') for msg, charset in decoded])
    elif six.PY3:
        return u' '.join([str(msg, encoding=charset, errors='replace') if charset else str(msg) for msg, charset in decoded])

def ticket_from_message(message, queue, logger):
    message = email.message_from_string(message)
    subject = message.get('subject', _('Created from e-mail'))
    subject = decode_mail_headers(decodeUnknown(message.get_charset(), subject))
    for affix in STRIPPED_SUBJECT_STRINGS:
        subject = subject.replace(affix, "")
    subject = subject.strip()

    sender = message.get('from', _('Unknown Sender'))
    sender = decode_mail_headers(decodeUnknown(message.get_charset(), sender))
    sender_email = email.utils.parseaddr(sender)[1]

    matchobj = re.match(r".*\[(?P<id>[0-9]+)\]", subject)

    if matchobj:
        ticket = matchobj.group('id')
        logger.info("Matched tracking ID %s-%s" % (queue.id, ticket))
    else:
        logger.info("No tracking ID matched.")
        ticket = None

    body = None
    counter = 0

    for part in message.walk():
        if part.get_content_maintype() == 'multipart':
            continue

        name = part.get_param('name')
        if name:
            name = email.utils.collapse_rfc2231_value(name)

        if part.get_content_maintype() == 'text' and name is None:
            if part.get_content_subtype() == 'plain':
                body = EmailReplyParser.parse_reply(decodeUnknown(part.get_content_charset(), part.get_payload(decode=True)))
                logger.debug("Discovered plain text MIME part")

        counter += 1


    if not body:
        body = _('No plain-text email body available')

    if ticket:
        try:
            t = Ticket.objects.get(id=ticket)
        except Ticket.DoesNotExist:
            logger.info("Tracking ID %s-%s not associated with existing ticket. Creating new ticket." % (queue.id, ticket))
            ticket = None
        else:
            logger.info("Found existing ticket with Tracking ID %s-%s" % (queue.id, t.id))
            if(t.status == 'C'):
                t.status = 'O'
                t.save()
            new = False


    try:
        user = User.objects.get(email=sender_email)
    except User.DoesNotExist:
        logger.info("User with email %s does not exist, adding to database." % (sender_email))
        user = User.objects.create(username=sender_email, email=sender_email)
        user.save()





    if ticket is None:
        new = True
        t = Ticket.objects.create(subject=subject, queue=queue, description=body, creator=user)
        logger.debug("Created new ticket %s-%s" % (t.queue.id, t.id))
    else:
        u = Update.objects.create(ticket=t, comment=body, user=user, status=t.status)
        u.save()
        logger.debug("Created update")

    if new:
        if sender_email:
            send_mail('Ticket [' + str(t.id) + ']',
                'Your ticket has been created, and will be dealt with shortly.\nPlease reference your ticket number in square brackets "[' + str(t.id) + ']"'
                + ' to update your ticket.',
                settings.EMAIL_HOST_USER,
                [sender_email],
                fail_silently=False
            )

        views.notify_workers(t)

    return t

if __name__ == '__main__':
    process_email()
