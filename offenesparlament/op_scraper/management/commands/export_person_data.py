from django.core.management.base import BaseCommand
from op_scraper.models import Person, Inquiry, LegislativePeriod
import csv
from os import system


class Command(BaseCommand):
    help = 'Exports Data'

    def get_person_cur_mandates(self, person):
        llp = [LegislativePeriod.objects.get(number=x) for x in self.ALLOWED_LLPS]
        return person.mandate_set.filter(legislative_period__in=llp).filter(function__title__contains='Nationalrat')

    def handle(self, *args, **options):
        self.ALLOWED_LLPS = [26]
        ps = Person.objects.all()
        r = []
        for p in ps:
            cm = self.get_person_cur_mandates(p)
            if cm.count()>0:
                r.append(p)

        with open('output.csv','w') as f:
            cw = csv.writer(f)
            cw.writerow(['id','person','foto','beruf','photocredit','geburtsdatum','link'])
            for p in r:
                cw.writerow([x.encode('utf-8') for x in [
                    p.pk,
                    p.full_name,
                    p.occupation,
                    p.photo_link,
                    p.photo_copyright,
                    str(p.birthdate),
                    p.source_link
                    ]])
                system('wget "{}" -O images/{}.jpg'.format(p.photo_link,p.pk))

