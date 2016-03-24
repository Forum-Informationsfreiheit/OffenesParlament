from op_scraper.models import SubscribedContent, Subscription, User
import json
import pprint

from offenesparlament.constants import LAW, PERSON, DEBATE, EMAIL


def collect_changesets(content):
    changes = {}
    try:
        old_hashes = content.latest_content_hashes
        cur_hashes = content.generate_content_hashes()
    except Exception as e:
        # FIXME This happens b/c we can't subscribe detail pages yet
        import ipdb
        ipdb.set_trace()
        return None

    old_content = content.latest_content
    cur_content = content.get_content()

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
        'occupation': PERSON.OCCUPATION
    },
    'Debatte': {},
    'Gesetz': {
        'title': LAW.TITLE,
        'description': LAW.DESCRIPTION,
    },
}


def check_subscriptions():

    for content in SubscribedContent.objects.all():
        changeset = collect_changesets(content)
        if not changeset:
            print u"No changes for {}".format(content.title)
            continue

        # Collect all the users we need to contact for this changeset/content
        emails = [sub.user.email for sub in content.subscriptions.all()]

        # changed_content
        changed_items = {
            'person': [],
            'debatte': [],
            'gesetz': [],
            'search': [],
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
                'messages': []
            }

            if item_category == 'Person':
                change_item['photo_link'] = complete_result['photo_link']

            for field in content_changes:
                if field in FIELD_MESSAGES[item_index]:
                    msg = FIELD_MESSAGES[item_index][field].msg(
                        content_changes[field]['new'])
                    change_item['messages'].append(msg)
                else:
                    print "Ignored Changes for {}: {}".format(item_index, field)

            changed_items[content.category].append(change_item)

        # TODO don't forget to recalculate the hashes and shit so we don't
        # re-send any changes
        template_parameters = {
            'changes': changed_items
        }

        for email in emails:
            print "Sending email to {}".format(email)
            email_sent = EMAIL.SUBSCRIPTION_CHANGES.send(
                email, template_parameters)
