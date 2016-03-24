# -*- coding: UTF-8 -*-
"""
Constants and Utility classes
"""

from django.core.mail import send_mail
from django.template import loader, Context

from datetime import datetime

# Limit results for ElasticSearch to this number by Default
ES_DEFAULT_LIMIT = 50


class EmailController():

    """
    Email utility controller, sends emails based on templates
    """

    sender = 'op@offenesparlament.com'
    fail_silently = False

    @classmethod
    def send(cls, recipient, context_params):
        """
        Renders email template and sends the resulting email
        """
        try:
            send_mail(
                cls.subject,
                cls.render_email(context_params),
                cls.sender,
                [recipient],
                fail_silently=cls.fail_silently)
        except:
            return False
        return True

    @classmethod
    def render_email(cls, context_params):
        """
        Finds and renders an email-template with the supplied kwargs.
        """

        template = loader.get_template(cls.template_file)
        context = Context(context_params)
        return template.render(context)


class EMAIL:

    class VERIFY_SUBSCRIPTION(EmailController):
        template_file = 'subscription/emails/verify_subscription.email'
        subject = 'Verify Thine Self!'

    class SUBSCRIPTION_LIST(EmailController):
        template_file = 'subscription/emails/subscription_list.email'
        subject = 'Your subscriptions @ OffenesParlament.at'

    class SUBSCRIPTION_CHANGES(EmailController):
        template_file = 'subscription/emails/subscription_changes.email'
        subject = 'Neuigkeiten von OffenesParlament'


class MESSAGES:

    class EMAIL:
        ALREADY_VERIFIED = "Dieses Abo ist bereits bestätigt. Sie erhalten bei Neuigkeiten zum Thema ein E-Mail."
        ALREADY_SUBSCRIBED = "Diese Seite ist bereits für diese E-Mail-Adresse abonniert!"
        SUCCESSFULLY_SUBSCRIBED = "Ihr Abo ist somit bestätigt und aktiv. Sie erhalten ab jetzt bei Neuigkeiten zum Thema ein E-Mail."
        OOPS = "Ups, da ist was schiefgelaufen - konnte das Abo für {} nicht finden oder nicht eindeutig zuordnen!"
        ERROR_SENDING_EMAIL = "Fehler beim Senden des E-Mails an '{}'."
        EMAIL_NOT_FOUND = "Falls wir Abos unter der E-Mail-Adresse '{}' in der Datenbank finden konnten, haben Sie soeben ein Login-E-Mail erhalten."
        SUBSCRIPTION_LINK_SENT = "Ein Login-Link wurde soeben an '{}' gesendet (falls wir ein Abo unter dieser Adresse in unserer Datenbank gefunden haben)."
        SUBSCRIPTION_DELETED = "Das Abo '{}' wurde gelöscht."
        VERIFICATION_SENT = "Ein Bestätigungslink wurde soeben an '{}' gesendet."


class ChangeMessageGenerator:

    MESSAGE_TEMPLATE = u""

    @classmethod
    def msg(cls, new_content):
        return cls.MESSAGE_TEMPLATE.format(new_content)


class LAW:

    class TITLE(ChangeMessageGenerator):
        MESSAGE_TEMPLATE = u"hat einen neuen Titel: {}"

    class DESCRIPTION(ChangeMessageGenerator):
        MESSAGE_TEMPLATE = u"hat eine neue Beschreibung: {}"


class PERSON:
    class OCCUPATION(ChangeMessageGenerator):
        MESSAGE_TEMPLATE = u"hat einen neuen Beruf angegeben: {}"

    class DEATH(ChangeMessageGenerator):
        MESSAGE_TEMPLATE = u"ist verstorben am: {}"

        @classmethod
        def msg(cls, new_content):
            try:
                dt = datetime.strptime(new_content, "%Y-%m-%dT%H:%M:%S")
                return cls.MESSAGE_TEMPLATE.format(dt.date().strftime("%d. %m. %Y"))
            except:
                # couldn't parse isoformat, return as is
                return cls.MESSAGE_TEMPLATE.format(new_content)


class DEBATE:
    pass
