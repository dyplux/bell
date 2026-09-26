#!/usr/bin/env python3
"""Make each dated observation tamper-evident, not just the two with payloads.

A reviewer rewrote one summary-only observation into an invented day that was
internally consistent - 791 references, every one no_flags, every signal zero -
and the verifier returned ok. Swapping a source hash for sixty-four zeros passed
too. Two of the twelve observations ship their full payload and are cross-checked
against it; the other ten were only checked for shape, so a coherent forgery was
indistinguishable from a record.

The digest of the whole file was printed at the end of verification and pinned
nowhere, so there was no reference value to compare against.

This chains them. Each observation carries the digest of the one before it, and
its own digest covers that link, so altering any observation invalidates every
digest after it as well as its own. Rewriting the series then means rewriting all
of it, and the head digest is committed, so that rewrite shows up in the diff.

It is not a signature and does not pretend to be: anyone who can rewrite the file
can rewrite the chain and the committed head together. What it removes is the
quiet single-record edit, which is the attack that actually succeeded.
"""

from __future__ import annotations

import hashlib
import json

CHAIN_VERSION = "bell.history_chain.v1"
LINK_FIELDS = ("sha256", "prev_sha256", "chain_version")


def canonical(observation: dict) -> bytes:
    """The bytes an observation's digest is taken over.

    Everything except the observation's own digest, so the link field can carry
    the result without being part of its own input. `prev_sha256` IS included,
    which is what makes the records a chain rather than a set of independent
    checksums.
    """
    body = {key: value for key, value in observation.items() if key != "sha256"}
    return json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def link(observation: dict, previous_digest: str | None) -> dict:
    """Return the observation with its chain fields set."""
    linked = {key: value for key, value in observation.items() if key not in LINK_FIELDS}
    linked["chain_version"] = CHAIN_VERSION
    linked["prev_sha256"] = previous_digest
    linked["sha256"] = hashlib.sha256(canonical(linked)).hexdigest()
    return linked


def rebuild(observations: list[dict]) -> list[dict]:
    """Re-link a whole series in observation order."""
    out: list[dict] = []
    previous = None
    for observation in observations:
        linked = link(observation, previous)
        out.append(linked)
        previous = linked["sha256"]
    return out


def verify(observations: list[dict]) -> str:
    """Check every link and return the head digest.

    Raises ValueError naming the first observation that does not verify, because
    "the history is wrong" is not an actionable message when there are twelve of
    them.
    """
    previous = None
    for index, observation in enumerate(observations):
        label = f"observation {index + 1} ({observation.get('observed_at', 'undated')})"
        if observation.get("chain_version") != CHAIN_VERSION:
            raise ValueError(f"{label} carries no {CHAIN_VERSION} link")
        if observation.get("prev_sha256") != previous:
            raise ValueError(
                f"{label} points at {observation.get('prev_sha256')!r} but follows {previous!r}: "
                "an observation was inserted, removed or reordered")
        recomputed = hashlib.sha256(canonical(observation)).hexdigest()
        if recomputed != observation.get("sha256"):
            raise ValueError(f"{label} does not match its own digest: its contents were edited")
        previous = observation["sha256"]
    if previous is None:
        raise ValueError("the history carries no observations to verify")
    return previous
