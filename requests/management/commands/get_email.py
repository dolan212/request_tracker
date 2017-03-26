import email
import logging
from sys import stdin

import re

from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.management import BaseCommand
from django.utils.translation import ugettext as _
from django.utils import six
from email_reply_parser import EmailReplyParser

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

    # def add_arguments(self, parser):
    #     parser.add_argument('message', type=str)

    def handle(self, *args, **options):
        msg = stdin.read()
        #print options['message']
        process_email(msg=msg)

def process_email(msg):
    q = Queue.objects.filter(everybody=True).first()
    logger = logging.getLogger('django.requests.queue.' + q.name)
    logger.setLevel(logging.DEBUG)
    process_queue(q=q, message=msg, logger=logger)


def process_queue(q, message, logger):
    ticket_from_message(message=message, queue=q, logger=logger)
    # logger.info("**** %s: Begin processing mail for requests" % ctime())
    #
    # mailbox_path = join(settings.MAILBOX_PATH, q.mailbox)
    # mbox = mailbox.mbox(mailbox_path)
    #
    # logger.info("Found %d messages in local mailbox directory" % len(mbox))
    # to_remove = []
    # for key, message in mbox.iteritems():
    #     logger.info("Processing message %s" % key)
    #     ticket = ticket_from_message(message=str(message), queue=q, logger=logger)
    #     if ticket:
    #         to_remove.append(key)
    #         logger.info("Successfully processed message %s, deleting" % key)
    #     else:
    #         logger.warn("Could not process message %s, leaving in mbox" % key)
    #
    # mbox.lock()
    # try:
    #     for key in to_remove:
    #         mbox.remove(key)
    #     mbox.flush()
    # except:
    #     logger.error("Could not delete messages from mbox")
    # finally:
    #     mbox.close()
    #     mbox.unlock()

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
            send_mail('Ticket [' + str(t.id) + '] - ' + t.subject,
                'Your ticket has been created, and will be dealt with shortly.\nPlease reference your ticket number in square brackets "[' + str(t.id) + ']"'
                + ' in the subject field to comment on your ticket.',
                settings.EMAIL_HOST_USER,
                [sender_email],
                fail_silently=False
            )

        views.notify_workers(t)
    elif u.user.email is not sender_email:
        send_mail('Ticket [' + str(t.id) + '] - ' + t.subject,
                u.user.username + ":\n" + u.comment,
                settings.EMAIL_HOST_USER,
                [t.creator.email],
                fail_silently=False)

    return t

if __name__ == '__main__':
    process_email()
