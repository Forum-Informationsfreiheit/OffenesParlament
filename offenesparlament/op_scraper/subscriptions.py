from op_scraper.models import SubscribedContent, Subscription, User
import json
from datadiff import diff


def check_subscriptions():
    changes = {}
    for sub in Subscription.objects.all():
        old_hashes = sub.content.latest_content_hashes
        cur_hashes = sub.content.generate_content_hashes()

        old_content = sub.content.latest_content
        cur_content = sub.content.get_content()

        # no changes, skip to the next one
        if old_hashes == cur_hashes:
            continue

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
            diffkeys = set([
                d[1][0][0]
                for d
                in diff(old, new).diffs
                if d[0] != 'equal'
                and d[0] != 'context_end_container'])
            atomic_changeset = {}
            for key in diffkeys:
                atomic_changeset[key] = {
                    'old': old[key],
                    'new': new[key],
                }
            changes[parl_id] = atomic_changeset
        print changes
