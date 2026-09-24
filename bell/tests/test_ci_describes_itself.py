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


if __name__ == '__main__':
    unittest.main()
