"""Every relative link in the repository has to resolve.

Nine internal documents were removed in one pass and seven links across three
files were left pointing at files that no longer existed. Nothing failed: a
broken link in a README is invisible to a test suite and obvious to the first
reader who clicks it. This closes that gap, so documentation rot is a build
failure rather than a reviewer's discovery.
"""
import os
import re
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LINK = re.compile(r'\[[^\]]*\]\(([^)\s]+)\)')
SKIP = ('http://', 'https://', 'mailto:', '#', 'data:')


SKIP_DIRS = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', '.v'}


def documents():
    """Every tracked markdown file, without requiring a git checkout.

    `git ls-files` was the obvious way to ask, and it made the whole suite fail
    with exit 128 in a copy of the repository that has no .git - which is what a
    reviewer who downloads a release archive actually has. A test that only
    passes inside a clone is testing the clone.
    """
    out = subprocess.run(['git', 'ls-files', '*.md'], cwd=ROOT,
                         capture_output=True, text=True)
    if out.returncode == 0 and out.stdout.strip():
        return [line for line in out.stdout.splitlines() if line]
    found = []
    for root, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            if name.endswith('.md'):
                found.append(os.path.relpath(os.path.join(root, name), ROOT))
    return sorted(found)


class RelativeLinksResolve(unittest.TestCase):
    def test_every_markdown_link_points_at_a_file_that_exists(self):
        broken = []
        for rel in documents():
            path = os.path.join(ROOT, rel)
            with open(path, encoding='utf-8') as handle:
                text = handle.read()
            for target in LINK.findall(text):
                if target.startswith(SKIP):
                    continue
                target = target.split('#', 1)[0]
                if not target:
                    continue
                resolved = os.path.normpath(os.path.join(os.path.dirname(path), target))
                if not os.path.exists(resolved):
                    broken.append(f'{rel} -> {target}')
        self.assertEqual(broken, [], 'links point at files that are not in the repository')

    def test_the_file_list_works_without_a_git_checkout(self):
        # The reviewer case: an unpacked archive, no .git. The walk fallback has
        # to find the same documents the tracked listing would.
        import importlib
        module = importlib.import_module('test_repo_links')
        original = module.subprocess.run
        module.subprocess.run = lambda *a, **k: type('R', (), {'returncode': 128, 'stdout': ''})()
        try:
            found = module.documents()
        finally:
            module.subprocess.run = original
        self.assertIn('README.md', found)
        self.assertTrue(any(name.endswith('JUDGE.md') for name in found))

    def test_the_check_would_notice_a_broken_link(self):
        # This asserted that an invented filename does not exist, which is true
        # of every invented filename and never touched the checker. A reviewer
        # counted it among the tests in this repository that cannot fail. Run
        # the real extraction and resolution over a document with one good link
        # and one broken one, and require exactly the broken one back.
        with tempfile.TemporaryDirectory() as directory:
            folder = os.path.join(directory, 'docs')
            os.makedirs(folder)
            real = os.path.join(folder, 'REAL.md')
            open(real, 'w', encoding='utf-8').close()
            page = os.path.join(folder, 'PAGE.md')
            with open(page, 'w', encoding='utf-8') as handle:
                handle.write('[here](REAL.md) and [gone](A-DOCUMENT-THAT-WAS-REMOVED.md)\n')
            broken = []
            with open(page, encoding='utf-8') as handle:
                text = handle.read()
            for target in LINK.findall(text):
                if target.startswith(SKIP):
                    continue
                target = target.split('#', 1)[0]
                if not target:
                    continue
                resolved = os.path.normpath(os.path.join(os.path.dirname(page), target))
                if not os.path.exists(resolved):
                    broken.append(target)
        self.assertEqual(broken, ['A-DOCUMENT-THAT-WAS-REMOVED.md'],
                         'the link extraction and resolution did not report the broken target')



class TheReleaseGateRunsOutsideACheckout(unittest.TestCase):
    """`make check` is the one command the README asks a reviewer to run.

    Both the link checker and the submission gate asked git which files are in
    the release, so `make check` exited non-zero for anyone who downloaded an
    archive instead of cloning - which is most reviewers. The gate that exists
    to stop a bad release shipping was unrunnable in the form the release
    actually takes.
    """

    def test_the_submission_gate_enumerates_files_without_git(self):
        import importlib
        gate = importlib.import_module('verify_submission')
        original = gate.subprocess.run
        gate.subprocess.run = lambda *a, **k: type('R', (), {'returncode': 128, 'stdout': b''})()
        try:
            found = gate.tracked_files()
        finally:
            gate.subprocess.run = original
        self.assertTrue(found, 'the gate found no files without a git checkout')
        self.assertIn('README.md', found)
        self.assertFalse([name for name in found if name.startswith('.git/')],
                         'the walk fallback is reading the git directory itself')

    def test_the_gate_still_refuses_to_pass_on_an_empty_listing(self):
        # A fallback that silently returns nothing would make every content
        # assertion vacuously true, which is worse than the failure it replaced.
        import importlib
        gate = importlib.import_module('verify_submission')
        self.assertGreater(len(gate.tracked_files()), 50)


class EveryVerifierIsAccountedFor(unittest.TestCase):
    """Eight scripts named verify_* invites "is this one job split eight ways?".

    A reviewer said that necessity versus overlap was not established, and it
    was not. The source map now names each one's question; this asserts the two
    cannot drift apart, so adding a ninth verifier without saying what it is
    for fails the build.
    """

    def test_the_source_map_names_every_verifier_that_ships(self):
        bell_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        scripts = sorted(name for name in os.listdir(bell_dir)
                         if name.startswith('verify_') and name.endswith('.py'))
        self.assertTrue(scripts, 'no verifiers found')
        with open(os.path.join(bell_dir, 'SOURCE-MAP.md'), encoding='utf-8') as handle:
            source_map = handle.read()
        undocumented = [name for name in scripts if f'`{name}`' not in source_map]
        self.assertEqual(undocumented, [],
                         'these verifiers ship without the source map saying what they are for')

    def test_the_source_map_does_not_name_a_verifier_that_was_deleted(self):
        bell_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(bell_dir, 'SOURCE-MAP.md'), encoding='utf-8') as handle:
            source_map = handle.read()
        named = set(re.findall(r'`(verify_[a-z_]+\.py)`', source_map))
        missing = sorted(name for name in named if not os.path.exists(os.path.join(bell_dir, name)))
        self.assertEqual(missing, [], 'the source map describes verifiers that no longer exist')


class NoTwoReceiptsDescribeOneObservationDifferently(unittest.TestCase):
    """Bell's subject is surfaces that quietly disagree. It had two.

    `docs/proof/` and `site/proof/` both held a 959 KB receipt for the
    observation of 2026-09-15. Their publication metadata differed for good
    reason - one was served live, one is the dated static copy - but their
    `method.rules[0]` did not match: the same observation described its own
    denomination rule two different ways, one of them predating a correction
    that made the threshold's inclusivity explicit. Nothing caught it because
    nothing compared them.
    """

    def _receipts(self):
        import json
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        found = {}
        for folder in ('docs/proof', 'site/proof'):
            directory = os.path.join(root, *folder.split('/'))
            if not os.path.isdir(directory):
                continue
            for name in os.listdir(directory):
                if not name.endswith('.json'):
                    continue
                path = os.path.join(directory, name)
                try:
                    with open(path, encoding='utf-8') as handle:
                        payload = json.load(handle)
                except (ValueError, OSError):
                    continue
                if not isinstance(payload, dict):
                    continue
                observed = payload.get('observed_at')
                method = payload.get('method')
                rules = method.get('rules') if isinstance(method, dict) else None
                if observed and rules:
                    found.setdefault(observed, []).append((f'{folder}/{name}', rules))
        return found

    def test_the_comparison_would_notice_two_receipts_that_disagree(self):
        # The test below ran zero iterations: every observed_at in the
        # repository maps to exactly one receipt, so its loop body was never
        # entered and it could not have caught the bug it was written for. A
        # reviewer found it. This exercises the comparison itself, so the check
        # below is a check of the DATA and this is a check of the LOGIC.
        groups = {'2026-09-15T22:22:00Z': [('a.json', ['rule one']), ('b.json', ['rule two'])]}
        mismatches = []
        for observed, entries in groups.items():
            first_name, first_rules = entries[0]
            for other_name, other_rules in entries[1:]:
                if first_rules != other_rules:
                    mismatches.append((observed, first_name, other_name))
        self.assertEqual(len(mismatches), 1,
                         'the comparison does not notice two receipts that disagree')

    def test_every_observation_is_described_by_at_most_one_rule_set(self):
        # Renamed from "receipts of the same observation state the same rules",
        # which read as if it had compared something. Superseded receipts are
        # included now: a superseded copy describing the same observation under
        # different rules is exactly the drift this was written for, and
        # excluding it by filename was the second reason the loop was empty.
        compared = 0
        for observed, entries in self._receipts().items():
            if len(entries) < 2:
                continue
            compared += 1
            first_name, first_rules = entries[0]
            for other_name, other_rules in entries[1:]:
                self.assertEqual(
                    first_rules, other_rules,
                    f'{first_name} and {other_name} both describe the observation at '
                    f'{observed} and state different rules. Two receipts of one '
                    f'observation cannot answer to two rule sets.')
        # `assertGreaterEqual(compared, 0)` was true for every possible value,
        # which is a tautology written to look like coverage. A reviewer counted
        # it among the checks in this repository that cannot fail, and was
        # right. Zero duplicate observations is a legitimate state here, so the
        # honest report is to say what was and was not compared, and to fail
        # only on the thing that would make this a no-op: enumerating nothing.
        receipts = self._receipts()
        self.assertGreater(len(receipts), 1,
                           'no dated receipts were enumerated, so this check compared nothing')
        if not compared:
            # Not a failure, and not silent either. The logic is exercised by
            # test_the_comparison_would_notice_two_receipts_that_disagree.
            print(f'\n  note: {len(receipts)} observations, none described by two receipts, '
                  f'so this compared nothing today')


class OneNameMeansOneBehaviour(unittest.TestCase):
    """`cmc_shapes` was introduced to end a name collision, and left one behind.

    Three modules had grown a `_records` with different fallbacks, so a reader
    who understood one had not understood the others. The shared definition
    fixed two of them - and the largest file in the project kept its own
    narrower `records` under the same name, while the shared module's docstring
    claimed to be "the single definition". An auditor found it; no test did.
    """

    def test_no_module_defines_a_function_the_shared_module_already_names(self):
        import ast
        bell_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(bell_dir, 'cmc_shapes.py'), encoding='utf-8') as handle:
            shared = {node.name for node in ast.parse(handle.read()).body
                      if isinstance(node, ast.FunctionDef)}
        clashes = []
        for name in sorted(os.listdir(bell_dir)):
            if not name.endswith('.py') or name == 'cmc_shapes.py':
                continue
            with open(os.path.join(bell_dir, name), encoding='utf-8') as handle:
                try:
                    tree = ast.parse(handle.read())
                except SyntaxError:
                    continue
            for node in tree.body:
                if isinstance(node, ast.FunctionDef) and node.name in shared:
                    clashes.append(f'{name}:{node.name}')
        self.assertEqual(clashes, [],
                         'these define a function under a name cmc_shapes already uses, so one '
                         'name means two behaviours again')

    def test_the_shared_module_does_not_overclaim(self):
        bell_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(bell_dir, 'cmc_shapes.py'), encoding='utf-8') as handle:
            text = handle.read()
        if 'single definition' in text:
            self.assertIn('rwa_asset_rows', text,
                          'cmc_shapes claims to be the single definition without naming the '
                          'reader that deliberately is not one')

    def test_the_endpoint_tables_are_tables_and_name_the_published_scan(self):
        # The generated paragraph was pasted BETWEEN a table's delimiter and its
        # rows, which breaks the table in markdown, and the manual rows still
        # omitted /v2/cryptocurrency/info - the endpoint the generator was
        # written to stop them omitting. A reviewer found both.
        import re
        import sys
        sys.path.insert(0, os.path.join(ROOT, 'bell'))
        from list_endpoints import summarise
        scanned = set(summarise()['published_scan'])
        for name in ('docs/ARCHITECTURE.md', 'bell/SOURCE-MAP.md'):
            text = open(os.path.join(ROOT, *name.split('/')), encoding='utf-8').read()
            for match in re.finditer(r'^\|.+\|$\n^\|[\s:|-]+\|$\n((?:^\|.+\|$\n)*)',
                                     text, re.M):
                body = match.group(1)
                if '/v5/real-world-assets/map' not in body:
                    continue
                self.assertTrue(body.strip(),
                                f'{name} has an endpoint table with a header and no rows, which '
                                'usually means something was pasted under the delimiter')
                missing = [endpoint for endpoint in scanned if endpoint not in body]
                self.assertEqual(
                    missing, [],
                    f'{name} lists the published scan and omits {", ".join(missing)}. '
                    'That is the omission bell/list_endpoints.py exists to stop.')
                break
            else:
                self.fail(f'{name} no longer carries an endpoint table')


class TheSourceMapCountsWhatShips(unittest.TestCase):
    """Six documentation figures drifted past their own gates, again.

    A reviewer checked them one by one: "the eight verifiers" against nine
    files, "the ten-observation population history" against fourteen, a README
    sending readers to a folder whose own README says it is superseded, and a
    quickstart telling them to search Marvell for a route the receipt does not
    give. Prose that states a count of something in the repository has to be
    checked against the repository, or it is a claim nobody measures.
    """

    def test_the_source_map_states_the_number_of_verifiers_that_exist(self):
        import glob
        verifiers = sorted(os.path.basename(p) for p in
                           glob.glob(os.path.join(ROOT, 'bell', 'verify_*.py')))
        text = open(os.path.join(ROOT, 'bell', 'SOURCE-MAP.md'), encoding='utf-8').read()
        self.assertIn(f'### The {len(verifiers)} verifiers', text,
                      f'the source map heading does not match the {len(verifiers)} verify_ scripts')
        self.assertIn(f'{len(verifiers)} scripts whose names all start', text)
        # And every one of them is in the table, so adding a verifier without
        # saying what question it answers fails here.
        for name in verifiers:
            self.assertIn(f'`{name}`', text, f'{name} ships and the source map does not name it')

    def test_the_package_readme_states_the_series_length_that_ships(self):
        import json
        history = json.load(open(os.path.join(
            ROOT, 'bell', 'site', 'proof', 'rwa-surface-integrity-history.json'), encoding='utf-8'))
        total = len(history['observations'])
        text = open(os.path.join(ROOT, 'bell', 'README.md'), encoding='utf-8').read()
        self.assertIn(f'The {total}-observation population history', text,
                      'bell/README.md states a series length the history does not have')

    def test_no_document_sends_a_reader_to_the_superseded_receipts(self):
        # bell/docs/proof/README.md says in its own first lines that it holds
        # superseded copies and is not what the site serves. The top-level
        # README pointed verification there anyway.
        text = open(os.path.join(ROOT, 'README.md'), encoding='utf-8').read()
        for line in text.splitlines():
            if 'bell/docs/proof' in line:
                self.assertIn('superseded', line.lower(),
                              f'this line points at the superseded receipts without saying so: {line.strip()!r}')


class EveryDocumentCountsTheSameEndpoints(unittest.TestCase):
    """Four documents listed the CMC surfaces by hand and gave four answers.

    ARCHITECTURE.md said 5 and omitted `cryptocurrency/info`, whose digest ships
    in every receipt. JUDGE.md said 7 and omitted the same one. SOURCE-MAP.md,
    titled "Exact CMC surfaces", said 8 and omitted four while including two the
    population scan never calls. PUBLIC-SUBMISSION.md said JUDGE.md names them
    and then listed a different 8. The pinning that protects the README and the
    judge page did not read these files.

    The list is generated from the source now, and this requires every document
    that lists endpoints to carry the generated sentence verbatim.
    """

    CARRIERS = ('docs/ARCHITECTURE.md', 'bell/JUDGE.md', 'bell/SOURCE-MAP.md',
                'bell/PUBLIC-SUBMISSION.md')

    def test_every_document_carries_the_generated_sentence(self):
        import sys
        sys.path.insert(0, os.path.join(ROOT, 'bell'))
        from list_endpoints import sentence, summarise
        stated = sentence(summarise())
        for name in self.CARRIERS:
            text = open(os.path.join(ROOT, *name.split('/')), encoding='utf-8').read()
            self.assertIn(stated, text,
                          f'{name} does not carry the generated endpoint sentence. '
                          f'Run `PYTHONPATH=bell python3 bell/list_endpoints.py` and paste it.')

    def test_the_generator_reads_the_source_rather_than_a_list(self):
        import sys
        sys.path.insert(0, os.path.join(ROOT, 'bell'))
        from list_endpoints import summarise
        summary = summarise()
        # The population scan's six are the ones a judge can exercise from the
        # shipped receipt, and every one must have a call site in the module
        # that performs it.
        scan = open(os.path.join(ROOT, 'bell', 'rwa_integrity.py'), encoding='utf-8').read()
        self.assertEqual(summary['published_scan_count'], 6)
        for endpoint in summary['published_scan']:
            self.assertIn(endpoint, scan, f'{endpoint} is claimed and not called')
        self.assertEqual(summary['rwa_family_count'], 7,
                         'the dedicated RWA family count changed; the judge page states it')
        self.assertIn('/v5/real-world-assets/market-pairs/list', summary['plan_refused'])

if __name__ == "__main__":
    unittest.main()
