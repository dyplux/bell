"""The CI file has to describe the CI file.

Its comment said the browser audit "runs in `make check` locally and in the
release job below". There was no job below. A comment describing a job nobody
had written, in a repository whose subject is surfaces that quietly disagree
with each other - and nothing could catch it, because no test had ever read the
workflow.

These tests read it.
"""
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORKFLOW = os.path.join(ROOT, '.github', 'workflows', 'bell-quality.yml')


class TheWorkflowDescribesItself(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(WORKFLOW, encoding='utf-8') as handle:
            cls.text = handle.read()
        cls.jobs = re.findall(r'^  ([a-z][a-z0-9-]*):$', cls.text, re.M)

    def test_a_comment_promising_a_job_below_has_one(self):
        if 'job below' in self.text or 'release job' in self.text:
            self.assertGreaterEqual(
                len(self.jobs), 2,
                f'the workflow refers to another job but declares only {self.jobs}')

    def test_the_deployed_interface_is_actually_audited_somewhere(self):
        self.assertIn('verify_public_browser.py', self.text,
                      'CI never drives the deployed interface, so nothing outside a '
                      'developer machine ever checks it')

    def test_the_interface_audit_does_not_run_on_a_push(self):
        # A site outage must not redden a commit that is fine. That is the whole
        # reason the push job runs the offline gate.
        block = self.text.split('deployed-interface:')[-1]
        self.assertIn("github.event_name == 'schedule'", block)
        self.assertIn('workflow_dispatch', block)

    def test_ci_checks_the_live_published_surface_without_a_secret(self):
        # The published receipt is credential-free by construction, so there is
        # no excuse for CI never looking at it. A scan that silently reverted to
        # refusing every reference should redden a build, not wait to be noticed.
        self.assertIn('verify_public_surface.py', self.text)
        self.assertNotIn('secrets.', self.text,
                         'this workflow now depends on a secret; the live checks were '
                         'chosen precisely because they need none')

    def test_the_push_job_runs_the_offline_gate_and_says_why(self):
        self.assertIn('make check-offline', self.text)
        self.assertIn('enforces strictly LESS than the local gate', self.text,
                      'the workflow no longer admits that it checks less than `make check`')



class TheOtherWorkflowsDescribeThemselves(unittest.TestCase):
    """The quality gate proves the repository's claims about its own data. It
    says nothing about whether the code is safe to run or whether a credential
    ever entered the history, and those are the two questions a reader of a
    credential-free receipt will ask next."""

    def read(self, name: str) -> str:
        path = os.path.join(ROOT, '.github', 'workflows', name)
        self.assertTrue(os.path.exists(path), f'{name} is missing')
        with open(path, encoding='utf-8') as handle:
            return handle.read()

    def test_codeql_analyses_both_languages_this_repository_ships(self):
        text = self.read('codeql.yml')
        self.assertIn('github/codeql-action/init', text)
        self.assertIn('github/codeql-action/analyze', text)
        # Bell is Python plus the browser bundle and the edge worker. Scanning
        # one of the two would be a badge rather than a check.
        self.assertIn('python', text)
        self.assertIn('javascript-typescript', text)
        self.assertIn('security-events: write', text)

    def test_the_secret_scan_reads_history_not_only_the_diff(self):
        text = self.read('secrets.yml')
        self.assertIn('gitleaks', text)
        # A key committed once and removed in the next commit is still in the
        # history and still compromised, so a shallow checkout would miss the
        # only case that matters.
        self.assertIn('fetch-depth: 0', text)

    def test_no_credential_shaped_string_is_tracked(self):
        # The claim the whole product rests on is that the CMC key never leaves
        # the publisher process. Assert it here too, so it holds even in a
        # checkout where the scanner has not run.
        import subprocess
        tracked = subprocess.run(['git', 'grep', '-nIE',
                                  r'(CMC_PRO_API_KEY|XAI_API_KEY)\s*[:=]\s*["\x27][A-Za-z0-9_-]{16,}'],
                                 cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(tracked.stdout.strip(), '',
                         f'a credential-shaped assignment is tracked: {tracked.stdout[:200]}')


if __name__ == "__main__":
    unittest.main()
