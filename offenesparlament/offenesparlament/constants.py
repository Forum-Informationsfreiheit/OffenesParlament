# -*- coding: UTF-8 -*-
"""
Constants and Utility classes
"""

from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.template import loader, Context

from django.conf import settings

from datetime import datetime

from op_scraper.models import User

import html2text

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

    sender = u'OffenesParlament <op@offenesparlament.at>'
    fail_silently = False

    @classmethod
    def send(cls, recipient, context_params):
        """
        Renders email template and sends the resulting email
        """
        try:
            user = User.objects.get(email=recipient)
            context_params['manage_subscriptions_link'] = reverse(
                'subscriptions_login2',
                kwargs={
                    'email': recipient,
                    'key': user.verification.verification_hash}
            )
            rendered_mail = cls.render_email(context_params)
            rendered_text_mail = html2text.html2text(rendered_mail)

            send_mail(
                cls.subject,
                rendered_text_mail,
                cls.sender,
                [recipient],
                fail_silently=cls.fail_silently,
                html_message=rendered_mail
            )
        except Exception as e:
            print e
            return None
        return rendered_mail

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
        template_file = u'subscription/emails/verify_subscription.email'
        subject = u'OffenesParlament.at - Abo bestätigen'

    class SUBSCRIPTION_LIST(EmailController):
        template_file = u'subscription/emails/subscription_list.email'
        subject = u'OffenesParlament.at - Abos und Inhalte verwalten: Login'

    class SUBSCRIPTION_CHANGES(EmailController):
        template_file = u'subscription/emails/subscription_changes.email'
        subject = u'Neuigkeiten von OffenesParlament'


class MESSAGES:

    class EMAIL:
        ALREADY_VERIFIED = u"Dieses Abo ist bereits bestätigt. Sie erhalten bei Neuigkeiten zum Thema ein E-Mail."
        ALREADY_SUBSCRIBED = u"Diese Seite ist bereits für diese E-Mail-Adresse abonniert!"
        SUCCESSFULLY_SUBSCRIBED = u"Ihr Abo ist somit bestätigt und aktiv. Sie erhalten ab jetzt bei Neuigkeiten zum Thema ein E-Mail."
        OOPS = u"Ups, da ist was schiefgelaufen - konnte das Abo für {} nicht finden oder nicht eindeutig zuordnen!"
        ERROR_SENDING_EMAIL = u"Fehler beim Senden des E-Mails an '{}'."
        EMAIL_NOT_FOUND = u"Falls wir Abos unter der E-Mail-Adresse '{}' in der Datenbank finden konnten, haben Sie soeben ein Login-E-Mail erhalten."
        SUBSCRIPTION_LINK_SENT = u"Ein Login-Link wurde soeben an '{}' gesendet (falls wir ein Abo unter dieser Adresse in unserer Datenbank gefunden haben)."
        SUBSCRIPTION_DELETED = u"Das Abo '{}' wurde gelöscht."
        VERIFICATION_SENT = u"Ein Bestätigungslink wurde soeben an '{}' gesendet."
        VERIFICATION_HASH_WRONG = u"Der Authentifizierungscode ist falsch. Bitte gehen Sie zu 'Abos verwalten' und loggen Sie sich ein."


class ChangeMessageGenerator:

    MESSAGE_TEMPLATE = u""

    @classmethod
    def msg(cls, changed_content):
        return cls.MESSAGE_TEMPLATE.format(changed_content['new'])


class LAW:

    class TITLE(ChangeMessageGenerator):
        MESSAGE_TEMPLATE = u"hat einen neuen Titel: {}"

    class RESPONSE(ChangeMessageGenerator):
        MESSAGE_TEMPLATE = u"hat eine neue Antwort"

    class DESCRIPTION(ChangeMessageGenerator):
        MESSAGE_TEMPLATE = u"hat eine neue Beschreibung: {}"

    class STEPS(ChangeMessageGenerator):
        MESSAGE_TEMPLATE = u"hat {} Statusänderung{} im parl. Verfahren: {}"

        @classmethod
        def msg(cls, changed_content):
            # Only new ones relevant
            new = 0
            if 'N' in changed_content:
                new = len(changed_content['N'])
            if new:
                steps_messages = u""
                for st in changed_content['N']:
                    steps_messages += u"\t<li>{}: {} am {}</li>\n".format(
                                st['phase'],
                                st['title'],
                                st['date']
                            )

                message = cls.MESSAGE_TEMPLATE.format(
                    u"eine" if new == 1 else new,
                    u"en" if new > 1 else "",
                    u"\n<ul>\n" + steps_messages + u"\n</ul>\n"
                )
                return message
            else:
                return None

    class KEYWORDS(ChangeMessageGenerator):
        MESSAGE_TEMPLATE = u"hat {} neue{} Schlagwort{}: {}"

        @classmethod
        def msg(cls, changed_content):
            # Only new ones relevant
            new = 0
            if 'N' in changed_content:
                new = len(changed_content['N'])
            if new:
                kw_messages = u""
                for kw in changed_content['N']:
                    kw_messages += u"\t<li>{}</li>\n".format(kw)

                message = cls.MESSAGE_TEMPLATE.format(
                    u"ein" if new == 1 else new,
                    u"s" if new == 1 else "",
                    u"e" if new > 1 else "",
                    u"\n<ul>\n" + kw_messages + u"\n</ul>\n"
                )
                return message
            else:
                return None

    class OPINIONS(ChangeMessageGenerator):
        MESSAGE_TEMPLATE = u"hat {} neue Stellungnahme{}: {}"

        @classmethod
        def msg(cls, changed_content):
            # Only new ones relevant
            new = 0
            if 'N' in changed_content:
                new = len(changed_content['N'])
            if new:
                op_messages = u""
                for op in changed_content['N']:
                    op_messages += u"\t<li>{}</li>\n".format(op['entity'])

                message = cls.MESSAGE_TEMPLATE.format(
                    u"eine" if new == 1 else new,
                    u"n" if new > 1 else "",
                    u"\n<ul>\n" + op_messages + u"\n</ul>\n"
                )
                return message
            else:
                return None


class PERSON:

    class COMITTEE_MEMBERSHIPS(ChangeMessageGenerator):
        MESSAGE_TEMPLATE = u"Hat neue Ausschusstätigkeiten: {}"

        @classmethod
        def msg(cls, changed_content):
            old = changed_content.get('D',[])
            new = changed_content.get('N',[])
            new_cms = [cm for cm in new if cm not in old]
            cm_changes = u""
            for cm in new_cms:
                cm_changes += u"\t<li>{}</li>\n".format(cm)
            return cls.MESSAGE_TEMPLATE.format(
                u"\n<ul>\n" + cm_changes + u"\n</ul>\n"
            )

    class INQUIRIES_SENT(ChangeMessageGenerator):
        MESSAGE_TEMPLATE = u"hat {} neue parlamentarische Anfrage{} gestellt"

        @classmethod
        def msg(cls, changed_content):
            # Only new ones relevant
            new = 0
            if 'N' in changed_content:
                new = len(changed_content['N'])
            if new:
                message = cls.MESSAGE_TEMPLATE.format(
                    "eine" if new == 1 else new,
                    "n" if new > 1 else ""
                )
                return message
            else:
                return None

    class INQUIRIES_RECEIVED(ChangeMessageGenerator):
        MESSAGE_TEMPLATE = u"hat {} neue parlamentarische Anfrage{} erhalten"

        @classmethod
        def msg(cls, changed_content):
            # Only new ones relevant
            new = 0
            if 'N' in changed_content:
                new = len(changed_content['N'])
            if new:
                message = cls.MESSAGE_TEMPLATE.format(
                    "eine" if new == 1 else new,
                    "n" if new > 1 else ""
                )
                return message
            else:
                return None

    class INQUIRIES_ANSWERED(ChangeMessageGenerator):
        MESSAGE_TEMPLATE = u"hat {} neue parlamentarische Anfrage{} beantwortet"

        @classmethod
        def msg(cls, changed_content):
            # Only new ones relevant
            new = 0
            if 'N' in changed_content:
                new = len(changed_content['N'])
            if new:
                message = cls.MESSAGE_TEMPLATE.format(
                    "eine" if new == 1 else new,
                    "n" if new > 1 else ""
                )
                return message
            else:
                return None

    class DEBATE_STATEMENTS(ChangeMessageGenerator):
        MESSAGE_TEMPLATE = u"hat {}{}{} Redebeiträg(e)"
        MESSAGE_NEW = u"{} neue{}"
        MESSAGE_CHANGED = u"{} geänderte{}"

        @classmethod
        def msg(cls, changed_content):

            changed = 0
            new = 0
            if 'C' in changed_content:
                changed = len(changed_content['C'])

            if 'N' in changed_content: new = len(changed_content['N'])
            if changed or new:
                message = cls.MESSAGE_TEMPLATE.format(
                    cls.MESSAGE_NEW.format(
                        "einen" if new == 1 else new,
                        "n" if new == 1 else "") if new else "",
                    u" und " if new and changed else "",
                    cls.MESSAGE_CHANGED.format(
                        "einen" if changed == 1 else changed,
                        "en" if changed == 1 else "") if changed else ""
                )
                return message
            else:
                return None
    # Removed 05.06.2017 by lk because
    # - will always be confusing w/ debate statements.
    # - has no relevant information connected (no content to statement)
    #
    # class STATEMENTS(ChangeMessageGenerator):
    #     MESSAGE_TEMPLATE = u"hat neue Redebeiträge: {}"

    #     @classmethod
    #     def msg(cls, changed_content):
    #         old = changed_content['old']
    #         new = changed_content['new']
    #         changed_statements = [s for s in new if s not in old]
    #         statement_changes = u""
    #         for st in changed_statements:
    #             statement_changes += u"\t<li>am {} zu {}</li>\n".format(
    #                 st['date'],
    #                 st['law'],
    #             )
    #         return cls.MESSAGE_TEMPLATE.format(
    #             u"\n<ul>\n" + statement_changes + u"</ul>\n"
    #         )

    class MANDATES(ChangeMessageGenerator):
        MESSAGE_TEMPLATE = u"hat {}{}{} Mandat(e)"
        MESSAGE_NEW = u"{} neue{}"
        MESSAGE_CHANGED = u"{} geänderte{}"

        @classmethod
        def msg(cls, changed_content):
            changed = 0
            new = 0
            if 'C' in changed_content:
                changed = len(changed_content['C'])

            if 'N' in changed_content: new = len(changed_content['N'])
            if changed or new:
                message = cls.MESSAGE_TEMPLATE.format(
                    cls.MESSAGE_NEW.format(
                        u"ein" if new == 1 else new,
                        u"s" if new == 1 else "") if new else "",
                    u" und " if new and changed else "",
                    cls.MESSAGE_CHANGED.format(
                        u"ein" if changed == 1 else changed,
                        u"s" if changed == 1 else "") if changed else ""
                )
                return message
            else:
                return None

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

class SEARCH:
    class NEW(ChangeMessageGenerator):
        MESSAGE_TEMPLATE = u"{} neue{} Ergebnis{}:{}"

        @classmethod
        def msg(cls, new):
            if len(new) < 1:
                return None

            return u"<li>{}</li>".format(
                cls.MESSAGE_TEMPLATE.format(
                    len(new) if len(new) > 1 else "ein ",
                    u"s" if len(new) == 1 else "",
                    u"se" if len(new) > 1 else ""
                    ,
                    u'<ul>{}</ul>'.format(u''.join([u'<li><a href="{}">{}</a></li>'.format(
                        settings.SITE_BASE_URL+x['internal_link'],
                        x.get('full_name',x.get('title'))) for x in new]))
                    )
                )

    class CHANGED(ChangeMessageGenerator):
        MESSAGE_TEMPLATE = u"{} geänderte{} Ergebnis{}:{}"

        @classmethod
        def msg(cls, changed):
            if len(changed) < 1:
                return None

            return u"<li>{}</li>".format(
                cls.MESSAGE_TEMPLATE.format(
                    len(changed) if len(changed) > 1 else u"ein",
                    u"" if len(changed) > 1 else "s",
                    u"" if len(changed) == 1 else "se",
                    u'<ul>{}</ul>'.format(
                        u''.join([u'<li>{}</li>'.format(x) for x in changed])
                        )
                    )
                )

class DEBATE:
    pass
