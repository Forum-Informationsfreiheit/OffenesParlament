from op_scraper.models import *
from django.conf import settings
from django.template import loader, Context
import json
import pprint
from tabulate import tabulate

from offenesparlament.constants import LAW, PERSON, DEBATE, EMAIL

current_content = {}
# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger('op_scraper.subscriptions.diff')

FIELD_BLACKLIST = ['text', 'ts']


class JsonDiffer(object):

    FIELD_MESSAGES = {}

    changes = {}
    current_content = {}

    def __init__(self, _content):
        self.content = _content
        self.old_content = _content.retrieve_latest_content()
        self.cur_content = _content.get_content()
        self.parse_content()
    
    def _disp(self,string):
        try:
            string = string.replace('\n','\\n')
            return (string[:20] + ' [...]') if len(string) > 20 else string
        except:
            return ""

    def parse_content(self):
    
        self.old_hashes = self.content.latest_content_hashes
        self.cur_hashes = self.content.generate_content_hashes(content=self.cur_content)

        # no changes, skip to the next one
        if self.old_hashes == self.cur_hashes:
            self.has_changes = False
            return
        try:
            self.old_hashes = json.loads(self.old_hashes)
        except Exception as e:
            logger.warn("[JsonDiffer] Error parsing archived content for subscription '{}': {}".format(
                self.content.title,
                e.message
                ))
            self.has_changes = False
            return

        try:
            self.cur_hashes = json.loads(self.cur_hashes)
        except Exception as e:
            logger.warn("[JsonDiffer] Error parsing current content for subscription '{}': {}".format(
                self.content.title,
                e.message
                ))
            self.has_changes = False
            return

        self.has_changes = True

    @classmethod
    def diff_dicts(cls, dict1, dict2):
        # Collect all keys in dict1 that aren't equal to dict2 or are not in dict2 at all
        dict1_diff_keys = [
                key for key in dict1.keys() if dict1[key] != dict2[key] or key not in dict2]
        # Collect all keys in dict2 that aren't equal to dict1 or are not in dict1 at all
        dict2_diff_keys = [
            key for key in dict2.keys() if dict1[key] != dict2[key] or key not in dict1]
        diff_keys = set(dict1_diff_keys + dict2_diff_keys)

        return diff_keys

    @classmethod
    def diff_arrays(cls,arr1,arr2):
        # Collect all the array entries from arr1 that aren't in arr2
        del_entries = [e for e in arr1 if e not in arr2]
        # Collect all the array entries from arr2 that aren't in arr1
        new_entries = [e for e in arr2 if e not in arr1]
        
        try:
            changed_entries = [e for e in new_entries if 'pk' in e and e['pk'] in [e2['pk'] for e2 in del_entries if 'pk' in e2]]
        except:
            # no biggie, just not a dict
            changed_entries = []
        
        new_entries = [e for e in new_entries if e not in changed_entries]
        
        for e in del_entries:
            if e in changed_entries:
                del_entries.remove(e)
            try:
                changed_pks = [e2['pk'] for e2 in changed_entries if 'pk' in e2]
                if changed_pks and 'pk' in e and e['pk'] in changed_pks:
                    del_entries.remove(e)
            except:
                # no biggie, just not a dict
                pass  
        
        return {'D': del_entries,
                'N': new_entries,
                'C': changed_entries}
        

    def print_changesets(self):
        if not self.has_changes:
            return None
        old_dict = dict((item['parl_id'], item) for item in self.old_content)
        cur_dict = dict((item['parl_id'], item) for item in self.cur_content)

        for parl_id in self.old_hashes:
            if parl_id in self.cur_hashes.keys():
                if self.cur_hashes[parl_id] != self.old_hashes[parl_id]:
                    logger.info("[{}] Changes:".format(parl_id))
                    old = old_dict[parl_id]
                    new = cur_dict[parl_id]
                    diff_arr = []
                    diff_keys = self.diff_dicts(old, new)
                    for key in diff_keys:
                        diff_arr.append([
                            u"{}".format(key),
                            self._disp(old[key]) if key in old else "",
                            self._disp(new[key]) if key in new else ""
                            ])
                    print tabulate(diff_arr, headers=['key','old value', 'new value'], tablefmt="fancy_grid")
                else:
                    logger.info("[{}] No Changes (hash equal)".format(parl_id))
            else:
                logger.info("[{}] Item deleted since last hash reset // reindex".format(parl_id))

    def collect_changesets(self):
        self.current_content = {}
        self.changes = {}

        if not self.has_changes:
            return {}

        changed_items = [
            parl_id for parl_id in self.old_hashes
            if parl_id in self.cur_hashes.keys()
            and self.cur_hashes[parl_id] != self.old_hashes[parl_id]]

        old_dict = dict((item['parl_id'], item) for item in self.old_content)
        cur_dict = dict((item['parl_id'], item) for item in self.cur_content)

        for parl_id in changed_items:
            old = old_dict[parl_id]
            new = cur_dict[parl_id]

            diff_keys = self.diff_dicts(old, new)

            self.current_content[parl_id] = new
            
            atomic_changeset = {}

            for key in diff_keys:
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

                # if list type, diff them as arrays
                if isinstance(atomic_changeset[key]['old'], list) and isinstance(atomic_changeset[key]['new'], list):
                    arr_changes = self.diff_arrays(atomic_changeset[key]['old'], atomic_changeset[key]['new'])
                    atomic_changeset[key] = arr_changes

            self.changes[parl_id] = atomic_changeset
        return self.changes

    def _build_messages(self, changeset):
        messages = []

        for field in changeset:
            if field in self.FIELD_MESSAGES:
                msg = self.FIELD_MESSAGES[field].msg(
                    changeset[field])
                if msg is not None:
                    messages.append(msg)
            elif field not in FIELD_BLACKLIST:
                logger.info(
                    "Ignored Changes for {}".format(field))
        return messages
            
class PersonDiffer(JsonDiffer):
    FIELD_MESSAGES = {
        'deathdate': PERSON.DEATH,
        'occupation': PERSON.OCCUPATION,
        'debate_statements': PERSON.DEBATE_STATEMENTS,
        'mandates': PERSON.MANDATES,
        'inquiries_sent': PERSON.INQUIRIES_SENT,
        'inquiries_received': PERSON.INQUIRIES_RECEIVED,
        'inquiries_answered': PERSON.INQUIRIES_ANSWERED,
        'comittee_memberships': PERSON.COMITTEE_MEMBERSHIPS,
    }
    SNIPPET_TEMPLATE_FILE = 'subscription/emails/snippets/person_changes.email'
    
    def _get_item(self, parl_id):
        try:
            return Person.objects.get(parl_id=parl_id)
        except:
            return None

    def render_snippets(self):
        # Plausibility
        if len(self.current_content) != 1:
            logger.warn("[PersonDiffer] Expected single Person to diff, got {} persons".format(
                len(self.current_content)
            ))
            import ipdb; ipdb.set_trace()
            return None

        if len(self.changes) == 0:
            return None
            
        snippets = []
        for parl_id, changeset in self.changes.iteritems():
            item_category = self.current_content[parl_id]['category']
            person = self._get_item(parl_id)

            messages = self._build_messages(changeset)
            change_item = {
                    'parl_id': parl_id,
                    'ui_url': self.content.ui_url,
                    'category': item_category,
                    'messages': messages,
                    'item': self.current_content[parl_id],
                    'short_css_class':   person.party.short_css_class
                }
            c = Context(change_item)
            snippets.append(
                loader.get_template(self.SNIPPET_TEMPLATE_FILE).render(c, None))
        
        return u'\n'.join(snippets)

class LawDiffer(JsonDiffer):
    FIELD_MESSAGES = {
        'title': LAW.TITLE,
        'description': LAW.DESCRIPTION,
        'steps': LAW.STEPS,
        'keywords': LAW.KEYWORDS,
        'opinions': LAW.OPINIONS
    }
    SNIPPET_TEMPLATE_FILE = 'subscription/emails/snippets/law_changes.email'

    def _get_item(self, parl_id):
        try:
            return Law.objects.get(parl_id=parl_id)
        except:
            return None

    def render_snippets(self):
        # Plausibility
        if len(self.current_content) != 1:
            logger.warn("[LawDiffer] Expected single Law to diff, got {} laws".format(
                len(self.current_content)
                ))
            return None

        if len(self.changes) == 0:
            return None

        snippets = []
        for parl_id, changeset in self.changes.iteritems():
            item_category = self.current_content[parl_id]['category']
            law = self._get_item(parl_id)

            messages = self._build_messages(changeset)
            change_item = {
                    'parl_id': parl_id,
                    'ui_url': self.content.ui_url,
                    'category': item_category,
                    'messages': messages,
                    'item': self.current_content[parl_id]
                }
            c = Context(change_item)
            snippets.append(
                loader.get_template(self.SNIPPET_TEMPLATE_FILE).render(c, None))
        
        return u'\n'.join(snippets)

class DebateDiffer(JsonDiffer):
    FIELD_MESSAGES = {}

class SearchDiffer(JsonDiffer):
    pass

CATEGORY_DIFFERS = {
    'person': PersonDiffer,
    'law': LawDiffer,
    'debate': DebateDiffer,
    'search': SearchDiffer,
}

def check_subscriptions():

    emails_to_changesets = {}
    changes = {}

    for content in SubscribedContent.objects.all():
        diff_class = CATEGORY_DIFFERS[content.category]


        differ = JsonDiffer(content)
        changeset = differ.collect_changesets(content)
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
                'ui_url': content.ui_url,
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
                    # import ipdb
                    # ipdb.set_trace()

            changed_items[content.category].append(change_item)

        changes[content.id] = changed_items

        for email in emails:
            if email not in emails_to_changesets:
                emails_to_changesets[email] = []
            emails_to_changesets[email].append(content.id)

    process_emails(emails_to_changesets, changes)

    # Reset the content hashes for all SubscribedContent items we just
    # processed
    if settings.DEBUG_SUBSCRIPTIONS:
        print 'skipping content has reset, because settings.DEBUG_SUBSCRIPTIONS'
    else:
        for content in SubscribedContent.objects.all():
            content.reset_content_hashes()


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
                            'ui_url': content.ui_url,
                            'search_title': content.title,
                            'changes': change_item[category_key]
                        })
        template_parameters = {'changes': changed_items}
        email_sent = EMAIL.SUBSCRIPTION_CHANGES.send(
            email, template_parameters)
        if email_sent:
            logger.info("Email sent to {}".format(email))
