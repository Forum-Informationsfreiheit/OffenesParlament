from django.core.management.base import BaseCommand, CommandError
from op_scraper.subscriptions import check_subscriptions
import haystack
import datetime
from op_scraper.models import *
# import the logging library
import logging


class Command(BaseCommand):
    help = u'Trigger a bunch of changes for testing and debugging the subscription features'

    def init(self):
        # Get an instance of a logger
        self.logger = logging.getLogger(__name__)

        self.law_idx = haystack.connections.all(
        )[0].get_unified_index().get_index(Law)
        self.person_idx = haystack.connections.all(
        )[0].get_unified_index().get_index(Person)
        self.debate_idx = haystack.connections.all(
        )[0].get_unified_index().get_index(Debate)

        self.XXV = LegislativePeriod.get("XXV")
        self.XXIV = LegislativePeriod.get("XXIV")

        infomsg = """
            Init complete.

            Be sure to back up your database via

            vagrant provision --provision-with backup_db

            first so you can restore/reset it without scraping again later!

            This script will change the following objects/items/searches - make
            sure to subscribe to them first so you can actually run the subscription
            change emails after:

            Single Laws:

            * http://offenesparlament.vm:8000/gesetze/XXV/1_d.B./
            * http://offenesparlament.vm:8000/gesetze/XXV/51_d.B./
            * http://offenesparlament.vm:8000/gesetze/XXV/179_d.B./

            Single Persons:

            * http://offenesparlament.vm:8000/personen/PAD_35518/Heinz-Christian-Strache/
            * http://offenesparlament.vm:8000/personen/PAD_86603/Mag-G%C3%BCnther-Kumpitsch/
            * http://offenesparlament.vm:8000/personen/PAD_83132/Ing-Thomas-Schellenbacher/
            * http://offenesparlament.vm:8000/personen/PAD_83142/Dr-Jessi-Lintl/

            Searches:

            * http://offenesparlament.vm:8000/suche/gesetze?llps=XXV&category=Bundesrechnungsabschluss
            * http://offenesparlament.vm:8000/suche/personen?llps=XXV&party=FP%C3%96
        """

        self.logger.info(infomsg)
        msg = 'Shall I make the changes?'
        shall = raw_input("%s (y/N) " % msg).lower() == 'y'
        return shall

    def modify_laws(self):

        law1 = Law.objects.filter(
            parl_id="(1 d.B.)", legislative_period=self.XXV).get()
        law1.status = "NEUER STATUS"
        law1.title = "NEUER Titel: " + law1.title
        law1.description = "DIES IST DIE NEUE BESCHREIBUNG"
        law1.ts = datetime.datetime.today()
        law1.save()
        self.law_idx.update_object(law1)

        law51 = Law.objects.filter(
            parl_id="(51 d.B.)", legislative_period=self.XXV).get()

        law51_new_step = law51.steps.first()
        law51_new_step.title = "NEUER STEP"
        law51_new_step.pk = None
        law51_new_step.save()

        new_kw = Keyword.objects.exclude(
            id__in=[k.id for k in law51.keywords.all()]
        ).first()
        law51.keywords.add(new_kw)

        law51_new_doc = law51.documents.first()
        law51_new_doc.title = "NEUES DOKUMENT"
        law51_new_doc.pk = None
        law51_new_doc.save()

        law51.ts = datetime.datetime.today()
        law51.save()
        self.law_idx.update_object(law51)

        law179 = Law.objects.filter(
            parl_id="(179/ME)", legislative_period=self.XXV).get()
        law179_new_opinion = law179.opinions.first()
        law179_new_opinion.description = "NEUE BESCHREIBUNG"
        law179_new_opinion.parl_id += "_123"
        law179_new_opinion.pk = None
        law179_new_opinion.save()
        self.law_idx.update_object(law179)

        bralaws = Law.objects.filter(
            legislative_period=self.XXV, category__title='Bundesrechnungsabschluss').all()
        for bralaw in bralaws[:1]:
            bralaw.title = "NEUER TITEL: " + bralaw.title
        for bralaw in bralaws[1:]:
            bralaw.status = "NEUER STATUS: " + bralaw.status
        for bralaw in bralaws:
            bralaw.save()
            self.law_idx.update_object(bralaw)

    def modify_persons(self):
        p1 = Person.objects.get(full_name__contains="Heinz-Christian Strache")
        p1.deathdate = datetime.datetime.today()
        p1.occupation = "Schmissbubi"
        p1.save()
        self.person_idx.update_object(p1)

        for p in Person.objects.filter(latest_mandate__party__short__startswith="FP"):
            p.occupation += " JETZT NEU: rechter Recke "
            self.person_idx.update_object(p)
            p.save()

        p2 = Person.objects.get(full_name__contains="Kumpitsch")
        new_debate_statement = p2.debate_statements.first()
        new_debate_statement.pk = None
        new_debate_statement.full_text = "Ich Trottel"
        new_debate_statement.save()
        p2.save()
        self.person_idx.update_object(p2)

        p3 = Person.objects.get(full_name__contains="Schellenbacher")
        new_comittee_membership = p3.comittee_memberships.first()
        new_comittee_membership.pk = None
        new_comittee_membership.comittee_id -= 1
        new_comittee_membership.save()
        p3.save()
        self.person_idx.update_object(p3)

        p4 = Person.objects.get(full_name__contains="Lintl")
        last_inq = p4.inquiries_sent.first()
        if last_inq:
            last_inq.pk = None
            last_inq.title = "NEUES TEST INQUIRY"
            last_inq.save()
            p4.save()
            self.person_idx.update_object(p4)

    def modify_debates(self):
        pass

    def handle(self, *args, **options):

        # Initialize connections to indices, etc
        cont = self.init()
        if not cont:
            print "Exiting."
            return

        # Modify Laws
        self.modify_laws()

        # Modify Laws
        self.modify_persons()

        # Modify Laws
        self.modify_debates()
