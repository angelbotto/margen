"""Linked identities must discover exactly what their grants permit."""
from unittest.mock import patch
from portal.test_account_ownership import AccountOwnershipTests
from portal.domain_access import verified_emails


class IdentitySharingTests(AccountOwnershipTests):
    def test_linked_domains_discover_shared_without_administrator_widening(self):
        with patch.dict('os.environ', {'BOTTIFACT_OWNER_ALIASES': 'admin@example.com,alias@team.test'}):
            self.author.put('/api/artifacts/' + self.other + '/access', json={
                'visibility': 'invited', 'domain_grants': [{'domain': 'team.test', 'role': 'commenter'}]})
            self.assertEqual(self.ids(self.admin, 'shared'), {self.other})
            self.assertNotIn(self.secret, self.ids(self.admin, 'shared'))
            self.assertEqual(self.ids(self.client('alias@team.test'), 'shared'), {self.other})
            self.author.put('/api/artifacts/' + self.other + '/access', json={'visibility': 'private'})
            self.assertEqual(self.ids(self.admin, 'shared'), set())

    def test_linked_grants_consistent_in_sql_legacy_search_and_direct_read(self):
        with patch.dict('os.environ', {'BOTTIFACT_OWNER_ALIASES': 'member@home.test,member@team.test,member@second.test'}):
            member = self.client('member@team.test')
            outsider = self.client('outsider@home.test')
            for legacy in (False, True):
                with self.subTest(legacy=legacy):
                    if legacy:
                        member.post('/api/bookmarks', json={'title': 'Old', 'url': 'https://example.com/member'})
                    shared = {'visibility': 'invited', 'grants': [], 'domain_grants': [
                        {'domain': 'team.test', 'role': 'viewer'}, {'domain': 'second.test', 'role': 'commenter'}]}
                    self.assertEqual(self.author.put('/api/artifacts/' + self.other + '/access', json=shared).status_code, 200)
                    for query in ['view=shared', 'view=shared&q=Team', 'view=shared&limit=1']:
                        result = member.get('/api/artifacts?' + query).json()
                        self.assertEqual(result['total'], 1)
                        self.assertEqual(len(result['artifacts']), 1)
                        self.assertEqual(result['artifacts'][0]['permissions']['role'], 'commenter')
                        self.assertIsNone(result.get('next_cursor'))
                    self.assertEqual(outsider.get('/api/artifacts/' + self.other).status_code, 404)
                    shared['grants'] = [{'email': 'member@second.test', 'role': 'viewer'}, {'email': 'member@home.test', 'role': 'editor'}]
                    self.author.put('/api/artifacts/' + self.other + '/access', json=shared)
                    self.assertEqual(member.get('/api/artifacts/' + self.other).json()['permissions']['role'], 'viewer')
                    self.assertEqual(member.get('/api/artifacts?view=shared').json()['artifacts'][0]['permissions']['role'], 'viewer')
                    # Personal invitation remains discoverable without domain access.
                    shared['domain_grants'] = []
                    self.author.put('/api/artifacts/' + self.other + '/access', json=shared)
                    self.assertEqual(self.ids(member, 'shared'), {self.other})
                    self.author.put('/api/artifacts/' + self.other + '/access', json={'visibility': 'private'})
                    self.assertEqual(member.get('/api/artifacts/' + self.other).status_code, 404)
                    self.assertEqual(self.ids(member, 'shared'), set())

    def test_unverified_and_client_supplied_aliases_cannot_expand_identity(self):
        with patch.dict('os.environ', {'BOTTIFACT_OWNER_ALIASES': 'admin@example.com,alias@team.test'}):
            self.assertEqual(verified_emails({'verified': False, 'email': 'alias@team.test'}), [])
            self.assertEqual(verified_emails({'verified': True, 'email': 'third@other.com', 'emails': ['alias@team.test']}), ['third@other.com'])
            self.assertEqual(verified_emails({'verified': True, 'email': 'ALIAS@TEAM.TEST'}), ['admin@example.com', 'alias@team.test'])
