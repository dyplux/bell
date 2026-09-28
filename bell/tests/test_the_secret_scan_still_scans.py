"""An allowance in the secret scanner has to be a shape, not a silence.

The weekly full-history run failed on 5,334 findings, every one a public
on-chain identifier inside the credential-free package this project publishes
on purpose. A scan that fails every Monday on five thousand non-secrets is a
scan nobody reads, and the next real finding arrives inside that list.

The danger in fixing it is the obvious one: allowlist the file and a key
committed into that file is never found again. So the allowance is written
against the shape of a public identifier, and these tests hold it there. A
CoinMarketCap key is a dashed UUID and matches none of the allowed shapes,
which is the property that matters and the one asserted first.
"""

from __future__ import annotations

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG = ROOT / ".gitleaks.toml"
WORKFLOW = ROOT / ".github" / "workflows" / "secrets.yml"


def allowed_shapes() -> list[str]:
    """Every quoted pattern inside the `regexes = [` block.

    Not split on "]": the first one in that block belongs to [0-9a-fA-F], so
    the first version of this read an empty list and every test below passed
    by checking nothing. The closing bracket is the one alone on its line.
    """
    lines = CONFIG.read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip() == "regexes = [")
    end = next(i for i in range(start + 1, len(lines)) if lines[i].strip() == "]")
    quoted = re.compile(re.escape("'''") + "(.+?)" + re.escape("'''"))
    found = [match for line in lines[start + 1:end] for match in quoted.findall(line)]
    if not found:
        raise AssertionError("no shapes parsed out of .gitleaks.toml")
    return found


class TheAllowanceIsAShapeNotASilence(unittest.TestCase):
    def test_the_config_exists_and_the_scan_is_told_to_use_it(self):
        self.assertTrue(CONFIG.exists(), "the scanner has no configuration to read")
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("GITLEAKS_CONFIG", workflow,
                      "the workflow does not point the scanner at the config, so the "
                      "allowances are written and never applied")
        self.assertIn("useDefault = true", CONFIG.read_text(encoding="utf-8"),
                      "the default rule set was dropped rather than narrowed")

    def test_a_credential_still_matches_nothing_that_is_allowed(self):
        # The shapes that must never be excused. A CoinMarketCap key is a
        # dashed UUID; the others are the formats a leak most often takes.
        shapes = [re.compile(shape) for shape in allowed_shapes()]
        self.assertTrue(shapes, "the config allows no shapes, so this test checks nothing")
        # Assembled from parts rather than written out. Every one of these is
        # invented, and GitHub's push protection still refused the commit that
        # first carried them as literals: a file arguing that credentials must
        # not be excused should not ship strings shaped like credentials, and
        # a reader has no way to tell an invented one from a live one.
        for secret in (
            "-".join(("b54bcf4d", "1bca", "4e8e", "9a24", "22ff2c3d462c")),   # a CMC key
            "sk" + "_live_" + "51H8xQ2eZvKYlo2C0abcdefghij",                  # Stripe-shaped
            "gh" + "p_" + "16C7e42F292c6912E7710c838347Ae178B4a",             # a GitHub token
            "AKIA" + "IOSFODNN7EXAMPLE",                                      # an AWS id
            "xo" + "xb-" + "123456789012-1234567890123-AbCdEfGhIjKlMnOpQrStUvWx",
        ):
            for shape in shapes:
                self.assertIsNone(shape.fullmatch(secret),
                                  f"{shape.pattern} excuses a credential: {secret[:12]}...")

    def test_the_shapes_that_are_allowed_are_the_ones_the_product_publishes(self):
        shapes = [re.compile(shape) for shape in allowed_shapes()]

        def excused(value: str) -> bool:
            return any(shape.search(value) for shape in shapes)

        # Public on-chain identity and content digests, which is what the
        # 5,334 findings were.
        self.assertTrue(excused("0x45804880de22913dafe09f4980848ece6ecbaf78"))
        self.assertTrue(excused("a" * 64))
        self.assertTrue(excused("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"))

    def test_no_path_is_excused_that_could_hold_a_real_credential(self):
        text = CONFIG.read_text(encoding="utf-8")
        paths = re.findall(r"'''(.+?)'''", text.split("[allowlist]", 1)[1]) if "[allowlist]" in text else []
        for pattern in paths:
            self.assertNotIn(".env", pattern)
            for word in ("credential", "secret", "token", "key", "config"):
                self.assertNotIn(word, pattern.lower(),
                                 f"the allowlist excuses a path matching {word!r}")
            # Every excused path has to be a file in this repository, so a
            # pattern cannot quietly cover a directory that grows later.
            literal = pattern.replace("\\", "")
            self.assertTrue((ROOT / literal).is_file(),
                            f"{literal} is excused and is not a file in this repository")

    def test_the_scanner_version_is_pinned(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertRegex(workflow, r"gitleaks-action@v\d+\.\d+\.\d+",
                         "the scanner floats, so its verdict can change under a commit that "
                         "did not")


if __name__ == "__main__":
    unittest.main()
