# One entry point. Every target runs with no API key and no account.
#
# A reviewer should not have to read the README to find out how to run this, and
# should not have to know that the Python suites need bell/ on the import path.
# `make check` is the whole gate: suites, receipt verification, and the public
# surface audit.

PY ?= python3
PKG := bell
WORKER := cloudflare

.DEFAULT_GOAL := help

.PHONY: help install test test-py test-js test-worker demo base-rate verify check check-live clean

help: ## Show the targets a reviewer needs
	@echo "make demo     - answer one comparability question, keyless, ~1s"
	@echo "make base-rate- how often a comparison is safe at all, whole catalogue"
	@echo "make test     - every suite (Python + browser-independent JS + worker)"
	@echo "make verify   - re-hash the published receipt against its shipped inputs"
	@echo "make check    - test + verify + public-surface audit (the full gate)"
	@echo "make check-live- the gate plus a real browser against the deployed site"
	@echo "make install  - optional; only needed for coverage and property tests"

install: ## Dev dependencies. The suites below run without them.
	$(PY) -m pip install --quiet --upgrade pip
	$(PY) -m pip install --quiet pytest hypothesis

test: test-py test-js test-worker ## Every suite

test-py: ## Python suites (bell/ is put on the import path for you)
	PYTHONPATH=$(PKG) $(PY) -m unittest discover -s $(PKG)/tests -p 'test_*.py' -q

test-js: ## Browser-independent JavaScript suites
	node --test $(PKG)/tests/*.cjs

test-worker: ## Edge worker suite
	node --test $(WORKER)/tests/*.mjs

demo: ## The judged capability: one reference, resolved and explained, no key
	PYTHONPATH=$(PKG) $(PY) $(PKG)/demo.py

base-rate: ## How often a comparison is safe at all, over the whole catalogue
	PYTHONPATH=$(PKG) $(PY) $(PKG)/base_rate.py

verify: ## Recompute the published receipt from the shipped inputs
	$(PY) $(PKG)/verify_integrity_receipt.py
	$(PY) $(PKG)/verify_catalogue_receipt.py

check: test verify ## The full gate, as CI runs it
	$(PY) $(PKG)/verify_submission.py

check-live: check ## The gate plus a real browser against the deployed site
	# Not in `check` because it needs network and a browser; it is here so the
	# assertion cannot rot unnoticed again - it did, and the README shipped a
	# command that failed for anyone who ran it.
	$(PY) $(PKG)/verify_public_browser.py --channel chrome

clean:
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
	find . -name '*.pyc' -delete
