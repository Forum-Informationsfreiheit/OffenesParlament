# -*- coding: UTF-8 -*-
"""
Constants and Utility classes
"""

from django.core.mail import send_mail
from django.template import loader, Context

from datetime import datetime

# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

# Limit results for ElasticSearch to this number by Default
ES_DEFAULT_LIMIT = 50


class EmailController():

    """
    Email utility controller, sends emails based on templates
    """
    # Get an instance of a logger
    logger = logging.getLogger("EmailController")

    sender = 'op@offenesparlament.com'
    fail_silently = False

    @classmethod
    def send(cls, recipient, context_params):
        """
        Renders email template and sends the resulting email
        """
        try:
            rendered_mail = cls.render_email(context_params)

            send_mail(
                cls.subject,
                rendered_mail,
                cls.sender,
                [recipient],
                fail_silently=cls.fail_silently)
        except Exception as e:
            print e
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
    def msg(cls, changed_content):
        return cls.MESSAGE_TEMPLATE.format(changed_content['new'])


class LAW:

    class TITLE(ChangeMessageGenerator):
        MESSAGE_TEMPLATE = u"hat einen neuen Titel: {}"

    class DESCRIPTION(ChangeMessageGenerator):
        MESSAGE_TEMPLATE = u"hat eine neue Beschreibung: {}"

    class STEPS(ChangeMessageGenerator):
        MESSAGE_TEMPLATE = u"hat Statusänderungem im parl. Verfahren: {}"

        @classmethod
        def msg(cls, changed_content):
            old = changed_content['old']
            new = changed_content['new']
            steps_messages = u""
            for ph in new.keys():
                for st in new[ph]:
                    if ph in old and st in old[ph]:
                        continue
                    else:
                        steps_messages += u"\t<li>{}: {} am {}</li>\n".format(
                            ph,
                            st['title'],
                            st['date']
                        )
            return cls.MESSAGE_TEMPLATE.format(
                u"\n<ul>\n" + steps_messages + u"\n</ul>\n"
            )

    class KEYWORDS(ChangeMessageGenerator):
        MESSAGE_TEMPLATE = u"hat neue Schlagworte: {}"

        @classmethod
        def msg(cls, changed_content):
            old = changed_content['old']
            new = changed_content['new']

            kw_messages = u""
            for kw in new:
                if kw not in old:
                    kw_messages += u"\t<li>{}</li>\n".format(kw)

            return cls.MESSAGE_TEMPLATE.format(
                u"\n<ul>\n" + kw_messages + u"\n</ul>\n"
            )

    class OPINIONS(ChangeMessageGenerator):
        MESSAGE_TEMPLATE = u"hat neue Stellungnahmen: {}"

        @classmethod
        def msg(cls, changed_content):
            old = changed_content['old']
            new = changed_content['new']
            new_stns = [stn for stn in new if stn not in old]
            stn_messages = u""
            for stn in new_stns:
                stn_messages += u"\t<li>{}</li>\n".format(
                    stn['description'])

            return cls.MESSAGE_TEMPLATE.format(
                u"\n<ul>\n" + stn_messages + u"\n</ul>\n"
            )


class PERSON:

    class COMITTEE_MEMBERSHIPS(ChangeMessageGenerator):
        MESSAGE_TEMPLATE = u"Hat neue Ausschusstätigkeiten: {}"

        @classmethod
        def msg(cls, changed_content):
            old = changed_content['old']
            new = changed_content['new']
            new_cms = [cm for cm in new if cm not in old]
            cm_changes = u""
            for cm in new_cms:
                cm_changes += u"\t<li>{}</li>\n".format(cm)
            return cls.MESSAGE_TEMPLATE.format(
                u"\n<ul>\n" + cm_changes + u"\n</ul>\n"
            )

    class INQUIRIES_SENT(ChangeMessageGenerator):
        MESSAGE_TEMPLATE = u"Hat neue Anfragen gestellt: {}"

        @classmethod
        def msg(cls, changed_content):
            old = changed_content['old']
            new = changed_content['new']
            new_inqs = [inq for inq in new if inq not in old]
            inq_changes = u""
            for inq in new_inqs:
                inq_changes += u"\t<li>{}: {} an {}</li>\n".format(
                    inq['category'],
                    inq['title'],
                    inq['receiver_name'])
            return cls.MESSAGE_TEMPLATE.format(
                u"\n<ul>\n" + inq_changes + u"\n</ul>\n"
            )

    class INQUIRIES_RECEIVED(ChangeMessageGenerator):
        MESSAGE_TEMPLATE = u"Hat neue Anfragen erhalten: {}"

        @classmethod
        def msg(cls, changed_content):
            old = changed_content['old']
            new = changed_content['new']
            new_inqs = [inq for inq in new if inq not in old]
            inq_changes = u""
            for inq in new_inqs:
                inq_changes += u"\t<li>{}: {} von {}</li>\n".format(
                    inq['category'],
                    inq['title'],
                    u", ".join(inq['sender_names']))
            return cls.MESSAGE_TEMPLATE.format(
                u"\n<ul>\n" + inq_changes + u"\n</ul>\n"
            )

    class INQUIRIES_ANSWERED(ChangeMessageGenerator):
        MESSAGE_TEMPLATE = u"Hat neue Anfragen beantwortet: {}"

        @classmethod
        def msg(cls, changed_content):
            old = changed_content['old']
            new = changed_content['new']
            new_inqs = [inq for inq in new if inq not in old]
            inq_changes = u""
            for inq in new_inqs:
                inq_changes += u"\t<li>{}: {} von {}</li>\n".format(
                    inq['category'],
                    inq['title'],
                    u", ".join(inq['sender_names']))
            return cls.MESSAGE_TEMPLATE.format(
                u"\n<ul>\n" + inq_changes + u"\n</ul>\n"
            )

    class DEBATE_STATEMENTS(ChangeMessageGenerator):
        MESSAGE_TEMPLATE = u"hat neue Redeeinträge: {}"

        @classmethod
        def msg(cls, changed_content):
            old = changed_content['old']
            new = changed_content['new']
            changed_dstatements = [ds for ds in new if ds not in old]
            statement_changes = u""
            for ds in changed_dstatements:
                ds_full_text = ds['full_text']
                if len(ds_full_text) > 100:
                    ds_full_text = ds_full_text[:100]
                    ds_full_text = ds_full_text[
                        :ds_full_text.rindex(u' ')] + u" [...]"
                statement_changes += u"\t<li>{}</li>\n".format(ds_full_text)
            return cls.MESSAGE_TEMPLATE.format(
                u"\n<ul>\n" + statement_changes + u"\n</ul>\n"
            )

    class STATEMENTS(ChangeMessageGenerator):
        MESSAGE_TEMPLATE = u"hat neue Redebeiträge: {}"

        @classmethod
        def msg(cls, changed_content):
            old = changed_content['old']
            new = changed_content['new']
            changed_statements = [s for s in new if s not in old]
            statement_changes = u""
            for st in changed_statements:
                statement_changes += u"\t<li>am {} zu {}</li>\n".format(
                    st['date'],
                    st['law'],
                )
            return cls.MESSAGE_TEMPLATE.format(
                u"\n<ul>\n" + statement_changes + u"</ul>\n"
            )

    class OCCUPATION(ChangeMessageGenerator):
        MESSAGE_TEMPLATE = u"hat einen neuen Beruf angegeben: {}"

    class DEATH(ChangeMessageGenerator):
        MESSAGE_TEMPLATE = u"ist verstorben am: {}"

        @classmethod
        def msg(cls, new_content):
            try:
                dt = datetime.strptime(new_content['new'], "%Y-%m-%dT%H:%M:%S")
                return cls.MESSAGE_TEMPLATE.format(
                    dt.date().strftime("%d. %m. %Y"))
            except:
                # couldn't parse isoformat, return as is
                return cls.MESSAGE_TEMPLATE.format(new_content)


class DEBATE:
    pass
