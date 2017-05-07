###### Export certain data to fixtures for testing
import subprocess
import os
from op_scraper.models import *

FNULL = open(os.devnull, 'w')

fixtures_path = u"/vagrant/offenesparlament/op_scraper/fixtures/"
yml_files = ['llps.yaml', 'categories.yaml', 'persons.yaml', 'laws.yaml']

laws = []
categories = {}
documents = []
keywords = []

def _clear_old_fixtures():
    print "Clearing old fixture files"
    for f in yml_files:
        abspath = u"{}{}".format(fixtures_path, f)
        if os.path.isfile(abspath):
            print "-- Removing {}".format(abspath)
            os.remove(abspath)

def _call_dump(export_filename, model, pks=None):
    abspath = u"{}{}".format(fixtures_path, export_filename)
    export_file = open(abspath, "a")
    model = "op_scraper.{}".format(model)
    args = ["python", "manage.py", "dumpdata", model, "--format=yaml", "--indent=4"]
    if pks:
        args += ["--pks", pks]

    subprocess.call(args, stdout=export_file, stderr=FNULL)
    print u"-- Written to file {}".format(abspath)

def _add_law(law):
    global laws
    
    laws.append(law)
    if law.references:
        _add_law(law.references)
    
    global categories
    if law.category_id in categories:
        categories[law.category_id] += 1
    else:
        categories[law.category_id] = 1
    
    global documents
    global keywords
    documents += law.documents.all()
    keywords += law.keywords.all()

def _person_fixtures():
    # Persons and dependecies
    print "Exporting first 10 Persons and Mandates"
    persons = Person.objects.filter(latest_mandate__legislative_period__number=25).all()[:10]
    mandates = []
    for p in persons:
        mandates += (p.mandates.all())

    person_pks = ",".join([p.pk for p in persons])
    mandates_pks = ",".join([str(m.pk) for m in mandates])

    _call_dump("persons.yaml", 'Person', person_pks)
    _call_dump("persons.yaml", 'Mandate', mandates_pks)

    print u"-- Exported {} Persons with {} Mandates".format(len(persons), len(mandates))

def _basic_fixtures():
    # Basic Data (LLPS)

    print "Exporting all LegislativePeriods"
    _call_dump("llps.yaml", 'LegislativePeriod')

    print "Exporting all Categories"
    _call_dump("categories.yaml", 'Category')

    print "Exporting all Functions"
    _call_dump('persons.yaml', 'Function')
    print "Exporting all Partys"
    _call_dump('persons.yaml', 'Party')
    print "Exporting all States"
    _call_dump('persons.yaml', 'State')
    print "Exporting all Administrations"
    _call_dump('persons.yaml', 'Administration')

def _law_fixtures():
    # Laws and dependencies
    print u"Exporting Laws with Documents, Keywords"
    
    for law in Law.objects.all():
        if law.category_id in categories and categories[law.category_id] > 2:
            continue
        _add_law(law)
        
    laws_pks = ",".join([str(l.pk) for l in laws])
    doc_pks = ",".join([str(d.pk) for d in documents])
    kw_pks = ",".join([str(kw.pk) for kw in keywords])

    _call_dump("laws.yaml", 'Keyword', kw_pks)
    _call_dump("laws.yaml", 'Document', doc_pks)
    _call_dump("laws.yaml", 'Law', laws_pks)

    print u"-- Exported {} Laws, {} Documents, {} Keywords".format(
        len(laws),
        len(documents),
        len(keywords))


def regen_fixtures():
    # Clear old fixtures
    _clear_old_fixtures()

    _basic_fixtures()
    
    _person_fixtures()

    _law_fixtures()


