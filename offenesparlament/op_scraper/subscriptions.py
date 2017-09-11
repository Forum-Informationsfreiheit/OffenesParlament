from op_scraper.models import *
from django.conf import settings
from django.template import loader, Context
import json
import pprint
from tabulate import tabulate

from offenesparlament.constants import LAW, PERSON, DEBATE, EMAIL, SEARCH

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

        # Don't run this twice if we already have collected changes in self.changes
        # OR if there aren't any changes
        if self.changes or not self.has_changes:
            return self.changes

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
            return None

        if len(self.changes) == 0:
            return None

        snippets = []
        for parl_id, changeset in self.changes.iteritems():
            item_category = self.current_content[parl_id]['category']
            person = self._get_item(parl_id)

            messages = self._build_messages(changeset)
            if not messages:
                continue

            # create ui_url_param to mark all the fields that are new or have changes
            ui_url_params = u"&mark_fields=".join(changeset.keys())

            change_item = {
                    'parl_id': parl_id,
                    'ui_url': self.content.ui_url + ('?' if not '?' in self.content.ui_url else '&') + ui_url_params[1:],
                    'category': item_category,
                    'messages': messages,
                    'item': self.current_content[parl_id],
                    'short_css_class':   person.party.short_css_class
                }
            c = Context(change_item)
            snippets.append(
                loader.get_template(self.SNIPPET_TEMPLATE_FILE).render(c, None))
        if not snippets:
            return None
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
            if not messages:
                continue

            # create ui_url_param to mark all the fields that are new or have changes
            ui_url_params = u"?mark_fields=" + u"&mark_fields=".join(changeset.keys())

            change_item = {
                    'parl_id': parl_id,
                    'ui_url': self.content.ui_url + ui_url_params,
                    'category': item_category,
                    'messages': messages,
                    'item': self.current_content[parl_id]
                }
            c = Context(change_item)
            snippets.append(
                loader.get_template(self.SNIPPET_TEMPLATE_FILE).render(c, None))

        if not snippets:
            return None
        return u'\n'.join(snippets)

class InquiryDiffer(LawDiffer):
    @property
    def FIELD_MESSAGES(self):
        fm = super(InquiryDiffer, self).FIELD_MESSAGES
        fm['response_id'] = LAW.RESPONSE
        return fm

class SearchDiffer(JsonDiffer):
    new = []
    deleted = []

    SNIPPET_TEMPLATE_FILE = 'subscription/emails/snippets/search_changes.email'

    SEARCH_MESSAGES = {
        'new': SEARCH.NEW,
        'changed': SEARCH.CHANGED,
        }

    def collect_new(self):
        self.new = []

        # Don't run this twice if we already have collected changes in self.changes
        # OR if there aren't any changes
        if self.new or not self.has_changes:
            return self.new

        self.new = [
            parl_id for parl_id in self.cur_hashes
            if parl_id not in self.old_hashes]

        return self.new

    def collect_deleted(self):
        self.deleted = []

        # Don't run this twice if we already have collected changes in self.changes
        # OR if there aren't any changes
        if self.deleted or not self.has_changes:
            return self.deleted

        self.deleted = [
            parl_id for parl_id in self.old_hashes
            if parl_id not in self.cur_hashes]

        return self.deleted

    def render_snippets(self):

        new = self.collect_new()

        new_msg = self.SEARCH_MESSAGES['new'].msg(new)
        changed_msg = self.SEARCH_MESSAGES['changed'].msg(self.changes)

        # create ui_url_param to mark all the parl_ids that are new or have changes
        mark_ids = set(self.changes.keys() + self.new)
        ui_url_params = u"&mark_id=".join(mark_ids)

        if not new_msg and not changed_msg:
            return None
        changes = {
                    'ui_url': self.content.ui_url + ('?' if '?' not in self.content.ui_url else '&') + ui_url_params[1:],
                    'title': self.content.title,
                    'messages': [new_msg,changed_msg]
                }
        c = Context(changes)
        snippet = loader.get_template(self.SNIPPET_TEMPLATE_FILE).render(c, None)

        if not snippet:
            return None
        return snippet


CATEGORY_DIFFERS = {
    'person': PersonDiffer,
    'law': LawDiffer,
    'inquiry': InquiryDiffer,
    'search': SearchDiffer,
    'search_laws': SearchDiffer,
    'search_debates': SearchDiffer,
    'search_persons': SearchDiffer,
}

def check_subscriptions():

    emails_to_changesets = {}
    change_snippets = {}

    for content in SubscribedContent.objects.all():
        diff_class = CATEGORY_DIFFERS[content.category]
        differ = diff_class(content)
        if not differ.has_changes or not differ.collect_changesets():
            logger.info(u"No changes for {}".format(content.title))
            continue

        snippet = differ.render_snippets()
        if snippet is None:
            logger.info(u"Only untracked changes for {}".format(content.title))
            continue

        category = 'search' if 'search' in content.category else content.category

        change_snippets[content.id] = {
            'snippet': snippet,
            'category': category
        }

        # Collect all the users we need to contact for this changeset/content
        emails = [sub.user.email for sub in content.subscriptions.all()]

        for email in emails:
            if email not in emails_to_changesets:
                emails_to_changesets[email] = []
            emails_to_changesets[email].append(content.id)

    process_emails(emails_to_changesets, change_snippets)

    # Reset the content hashes for all SubscribedContent items we just
    # processed
    if settings.DEBUG_SUBSCRIPTIONS:
        print 'skipping content has reset, because settings.DEBUG_SUBSCRIPTIONS'
    else:
        for content in SubscribedContent.objects.all():
            content.reset_content_hashes()

def process_emails(emails_to_changesets, change_snippets):

    logger.info(
        "Preparing to send {} emails".format(len(emails_to_changesets)))
    for email in emails_to_changesets.keys():
        logger.info("Sending email to {}".format(email))

        # changed_content
        changed_items = {
            'person': [],
            'law': [],
            'search': [],
            'inquiry': [],
        }

        for content_id in set(emails_to_changesets[email]):
            snippets = change_snippets[content_id]
            snippet = snippets['snippet']
            category = snippets['category']
            changed_items[category].append(snippet)

        template_parameters = {'changes': changed_items}
        email_sent = EMAIL.SUBSCRIPTION_CHANGES.send(
            email, template_parameters)
        if email_sent:
            logger.info(u"Email sent to {}: {}".format(email, email_sent))
            # logger.info(u"Email sent to {}".format(email))
