###### Export certain data to fixtures for testing
from django.db.models import Count

from itertools import chain

import subprocess
import os
from op_scraper.models import *

FNULL = open(os.devnull, 'w')

fixtures_path = u"/vagrant/offenesparlament/op_scraper/fixtures/"
yml_files = ['llps.yaml', 'categories.yaml', 'persons.yaml', 'laws.yaml', 'debates.yaml']

prelaws = []
laws = []
categories = {}
documents = []
keywords = []
steps = []
phases = []
opinions = []
entities = []
inquiries = []
inquiries_responses = []

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

    # print u"--- Calling subprocess {}".format(" ".join(args))
    subprocess.call(args, stdout=export_file, stderr=FNULL)

    print u"-- Written {} to file {}".format(model,abspath)

def _add_opinion(opinion):
    if opinion is None:
        return
    
    #print "---- Adding opinion {}".format(opinion)        
    global opinions
    global documents
    global keywords
    global entities
    
    opinions += [opinion]

    documents += opinion.documents.all()
    keywords += opinion.keywords.all()
    entities += [opinion.entity]
    _add_prelaw(opinion.prelaw)
    
def _add_prelaw(law):
    global prelaws
    
    #print u"--- Adding prelaw {}".format(law.title)
    
    prelaws.append(law)
    if law.references:
        _add_law(law.references)
    
    global categories
    if law.category_id in categories:
        categories[law.category_id] += 1
    else:
        categories[law.category_id] = 1
    
    global documents
    global keywords
    global steps
    global phases
    
    documents += law.documents.all()
    keywords += law.keywords.all()
    law_steps = law.steps.all()
    steps += law_steps
    [_add_opinion(step.opinion) for step in law_steps]
    phases += [step.phase for step in law_steps]
    

def _add_law(law):
    global laws
    #print u"--- Adding law {}".format(law.title)
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
    global steps
    global phases
    
    documents += law.documents.all()
    keywords += law.keywords.all()
    law_steps = law.steps.all()
    steps += law_steps
    [_add_opinion(opinion) for opinion in law.opinions.all()]
    phases += [step.phase for step in law_steps]
    
def _add_inq(inq):
    global inquiries
    #print u"--- Adding inq {}".format(law.title)
    inquiries.append(inq)
    if inq.references:
        _add_law(inq.references)
    
    global categories
    if inq.category_id in categories:
        categories[inq.category_id] += 1
    else:
        categories[inq.category_id] = 1
    
    global documents
    global keywords
    global steps
    global phases
    
    documents += inq.documents.all()
    keywords += inq.keywords.all()
    inq_steps = inq.steps.all()
    steps += inq_steps
    [_add_opinion(opinion) for opinion in inq.opinions.all()]
    phases += [step.phase for step in inq_steps]

def _add_inq_resp(inq):
    global inquiries_responses
    #print u"--- Adding inq {}".format(law.title)
    inquiries_responses.append(inq)
    if inq.references:
        _add_law(inq.references)
    
    global categories
    if inq.category_id in categories:
        categories[inq.category_id] += 1
    else:
        categories[inq.category_id] = 1
    
    global documents
    global keywords
    global steps
    global phases
    
    documents += inq.documents.all()
    keywords += inq.keywords.all()
    inq_steps = inq.steps.all()
    steps += inq_steps
    [_add_opinion(opinion) for opinion in inq.opinions.all()]
    phases += [step.phase for step in inq_steps]
    

def _person_fixtures():
    # Persons and dependecies
    print "Exporting first 10+ Persons, Mandates, Debates and Inquiries / Responses"
    persons_nr = Person.objects\
        .annotate(num_statements=Count('debate_statements'))\
        .filter(num_statements__gt=0)\
        .filter(num_statements__lt=20)\
        .filter(latest_mandate__legislative_period__number=25)\
        .filter(latest_mandate__function__title__contains='Nationalrat')[:2].all()
    persons_br = Person.objects\
        .annotate(num_statements=Count('debate_statements'))\
        .filter(num_statements__gt=0)\
        .filter(num_statements__lt=20)\
        .filter(latest_mandate__legislative_period__number=25)\
        .filter(latest_mandate__function__title__contains='Bundesrat')[:2].all()
    persons_inq_s = Person.objects\
        .annotate(num_inq_s=Count('inquiries_sent'))\
        .filter(num_inq_s__gt=2)\
        .filter(latest_mandate__legislative_period__number=25)\
        .filter(latest_mandate__function__title__contains='Nationalrat')[:2].all()
    persons_inq_r = Person.objects\
        .annotate(num_inq_r=Count('inquiries_received'))\
        .filter(num_inq_r__gt=2)\
        .filter(latest_mandate__legislative_period__number=25)\
        .filter(latest_mandate__function__title__contains='Nationalrat')[:2].all()
    persons_inq_a = Person.objects\
        .annotate(num_inq_a=Count('inquiries_answered'))\
        .filter(num_inq_a__gt=2)\
        .filter(latest_mandate__legislative_period__number=25)\
        .filter(latest_mandate__function__title__contains='Nationalrat')[:2].all()

    persons = list(chain(
        persons_br, 
        persons_nr, 
        persons_inq_s, 
        persons_inq_r, 
        persons_inq_a))
    
    inq_persons = []
    global laws
    for p in persons:
        for inq in p.inquiries_answered.all()[:2]:
            _add_inq(inq)

        for inq in p.inquiries_sent.all()[:2]:
            _add_inq(inq)
            inq_persons.append(inq.receiver)
            if inq.response:
                _add_inq_resp(inq.response)
                inq_persons.append(inq.response.sender)
        for inq in p.inquiries_received.all()[:2]:
            _add_inq(inq)
            inq_persons += inq.sender.all()
            if inq.response:
                _add_inq_resp(inq.response)
                inq_persons.append(inq.response.sender)
    
    persons = set(persons + inq_persons)

    mandates = []
    for p in persons:
        mandates += (p.mandates.all())
    
    debate_statements = []
    for p in persons:
        debate_statements += (p.debate_statements.all()[:2])
    
    debates = []
    for st in debate_statements:
        if st.debate not in debates: 
            debates += [st.debate]

    person_pks = ",".join([p.pk for p in persons])
    mandates_pks = ",".join([str(m.pk) for m in mandates])
    debates_pks = ",".join([str(d.pk) for d in debates])
    debate_statements_pks = ",".join([str(s.pk) for s in debate_statements])

    _call_dump("persons.yaml", 'Person', person_pks)
    _call_dump("persons.yaml", 'Mandate', mandates_pks)
    _call_dump("debates.yaml", 'Debate', debates_pks)
    _call_dump("debates.yaml", 'DebateStatement', debate_statements_pks)

    print u"-- Exported {} Persons with {} Mandates, {} Debate Statements and {} Debates".format(
        len(persons), 
        len(mandates),
        len(debate_statements),
        len(debates))

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
        if law.category_id is not None and law.category_id in categories and categories[law.category_id] > 1:
            continue
        _add_law(law)
    
    inq_pks = ",".join([str(l.pk) for l in set(inquiries)])
    inq_resp_pks = ",".join([str(l.pk) for l in set(inquiries_responses)])
    prelaws_pks = ",".join([str(l.pk) for l in set(prelaws) if l not in inquiries and l not in inquiries_responses])
    laws_pks = ",".join([str(l.pk) for l in set(laws) if l not in prelaws and l not in inquiries and l not in inquiries_responses])
    
    doc_pks = ",".join([str(d.pk) for d in documents])
    kw_pks = ",".join([str(kw.pk) for kw in keywords])
    st_pks = ",".join([str(st.pk) for st in steps])
    op_pks = ",".join([str(op.pk) for op in opinions])
    ph_pks = ",".join([str(ph.pk) for ph in phases])
    en_pks = ",".join([str(en.pk) for en in entities])
    
    print u"-- Exporting {} Laws, {} Prelaws, {} Inquiries, {} Inquiry Responses, {} Documents, {} Keywords, {} Steps, {} Phases, {} Opinions".format(
        len(laws),
        len(prelaws),
        len(inq_pks),
        len(inq_resp_pks),
        len(documents),
        len(keywords),
        len(steps),
        len(phases),
        len(opinions))

    if kw_pks:
        _call_dump("laws.yaml", 'Keyword', kw_pks)
    if doc_pks:
        _call_dump("laws.yaml", 'Document', doc_pks)
    if ph_pks:
        _call_dump("laws.yaml", 'Phase', ph_pks)
    if st_pks:
        _call_dump("laws.yaml", 'Step', st_pks)
    if en_pks:
        _call_dump("laws.yaml", 'Entity', en_pks)
    if inq_resp_pks:
        _call_dump("laws.yaml", 'Law', inq_resp_pks)
        _call_dump("laws.yaml", 'InquiryResponse', inq_resp_pks)
    if inq_pks:
        _call_dump("laws.yaml", 'Law', inq_pks)
        _call_dump("laws.yaml", 'Inquiry', inq_pks)
    if prelaws_pks:
        _call_dump("laws.yaml", 'Law', prelaws_pks)
    if op_pks:
        _call_dump("laws.yaml", 'Opinion', op_pks)
    if laws_pks:
        _call_dump("laws.yaml", 'Law', laws_pks)   

def regen_fixtures():
    # Clear old fixtures
    _clear_old_fixtures()

    _basic_fixtures()
    
    _person_fixtures()

    _law_fixtures()
