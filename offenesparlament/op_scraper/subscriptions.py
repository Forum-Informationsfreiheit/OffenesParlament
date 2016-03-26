from op_scraper.models import SubscribedContent, Subscription, User
import json
import pprint

from offenesparlament.constants import LAW, PERSON, DEBATE, EMAIL

# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

FIELD_BLACKLIST = ['text', 'ts']


def collect_changesets(content):
    changes = {}

    old_content = content.latest_content
    cur_content = content.get_content()

    try:
        old_hashes = content.latest_content_hashes
        cur_hashes = content.generate_content_hashes(content=cur_content)
    except Exception as e:
        logger.warn(e)
        return None

    # no changes, skip to the next one
    if old_hashes == cur_hashes:
        return None

    old_hashes = json.loads(old_hashes)
    cur_hashes = json.loads(cur_hashes)
    old_content = json.loads(old_content)['result']
    cur_content = json.loads(cur_content)['result']

    old_dict = dict((item['parl_id'], item) for item in old_content)
    cur_dict = dict((item['parl_id'], item) for item in cur_content)

    changed_items = [
        parl_id for parl_id in old_hashes
        if parl_id in cur_hashes.keys()
        and cur_hashes[parl_id] != old_hashes[parl_id]]

    for parl_id in changed_items:
        old = old_dict[parl_id]
        new = cur_dict[parl_id]

        old_diff_keys = [
            key for key in old.keys() if old[key] != new[key] or key not in new]
        new_diff_keys = [
            key for key in new.keys() if old[key] != new[key] or key not in old]
        diffkeys = set(old_diff_keys + new_diff_keys)
        atomic_changeset = {
            'cur_content': new
        }
        for key in diffkeys:
            atomic_changeset[key] = {
                'old': old[key] if key in old else None,
                'new': new[key] if key in new else None,
            }
            try:
                atomic_changeset[key]['old'] = json.loads(old[key])
                atomic_changeset[key]['new'] = json.loads(new[key])
            except:
                # wasn't a json field, no biggie
                pass
        changes[parl_id] = atomic_changeset
    return changes

FIELD_MESSAGES = {
    'Person': {
        'deathdate': PERSON.DEATH,
        'occupation': PERSON.OCCUPATION,
        'debate_statements': PERSON.DEBATE_STATEMENTS,
        'statements': PERSON.STATEMENTS,
    },
    'Debatte': {},
    'Gesetz': {
        'title': LAW.TITLE,
        'description': LAW.DESCRIPTION,
        'steps': LAW.STEPS,
        'keywords': LAW.KEYWORDS,
    },
}


def check_subscriptions():

    emails_to_changesets = {}
    changes = {}

    for content in SubscribedContent.objects.all():
        changeset = collect_changesets(content)
        if not changeset:
            logger.info(u"No changes for {}".format(content.title))
            continue

        # Collect all the users we need to contact for this changeset/content
        emails = [sub.user.email for sub in content.subscriptions.all()]

        # changed_content
        changed_items = {
            'person': [],
            'debatte': [],
            'law': [],
            'search': [],
            'content': content
        }

        # iterate changed content
        for parl_id in changeset.keys():
            content_changes = changeset[parl_id]
            complete_result = content_changes.pop('cur_content')
            item_category = complete_result['category']
            item_index = item_category if item_category in [
                'Person', 'Debatte'] else 'Gesetz'

            change_item = {
                'parl_id': parl_id,
                'category': item_category,
                'messages': [],
                'item': complete_result
            }

            for field in content_changes:
                if field in FIELD_MESSAGES[item_index]:
                    msg = FIELD_MESSAGES[item_index][field].msg(
                        content_changes[field])
                    try:
                        print msg
                    except:
                        pass
                    change_item['messages'].append(msg)
                elif field not in FIELD_BLACKLIST:
                    logger.info(
                        "Ignored Changes for {}: {}".format(item_index, field))
                    import ipdb
                    ipdb.set_trace()

            changed_items[content.category].append(change_item)

        changes[content.id] = changed_items

        for email in emails:
            if email not in emails_to_changesets:
                emails_to_changesets[email] = []
            emails_to_changesets[email].append(content.id)

    process_emails(emails_to_changesets, changes)


def process_emails(emails_to_changesets, change_items):

    logger.info(
        "Preparing to send {} emails".format(len(emails_to_changesets)))
    for email in emails_to_changesets.keys():
        logger.info("Sending email to {}".format(email))

        # changed_content
        changed_items = {
            'person': [],
            'debatte': [],
            'law': [],
            'search': [],
        }

        for content_id in set(emails_to_changesets[email]):
            change_item = change_items[content_id]
            content = change_item['content']
            for category_key in ['person', 'debatte', 'law', 'search']:
                if change_item[category_key]:
                    if category_key != 'search':
                        changed_items[
                            category_key] += (change_item[category_key])
                    else:
                        changed_items[category_key].append({
                            'content_id': content.id,
                            'search_title': content.title,
                            'changes': change_item[category_key]
                        })
        template_parameters = {'changes': changed_items}
        email_sent = EMAIL.SUBSCRIPTION_CHANGES.send(
            email, template_parameters)
        if email_sent:
            logger.info("Email sent to {}".format(email))
