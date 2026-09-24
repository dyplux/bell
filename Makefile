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

.PHONY: help install test test-py test-js test-worker demo base-rate liveness verify check check-offline check-live browser-audit clean

help: ## Show the targets a reviewer needs
	@echo "make demo     - answer one comparability question, keyless, ~1s"
	@echo "make base-rate- how often a comparison is safe at all, whole catalogue"
	@echo "make test     - every suite (Python + browser-independent JS + worker)"
	@echo "make verify   - re-hash the published receipt against its shipped inputs"
	@echo "make liveness - ask today's CMC API if it still answers in the shape we read"
	@echo "make check    - the full gate; drives a real browser if one is installed"
	@echo "make check-offline - the same gate with no network and no browser"
	@echo "make check-live- force the browser audit and fail if it cannot run"
	@echo "make install  - suites run without it; installs the browser for check"

install: ## Dev dependencies. The suites below run without them.
	$(PY) -m pip install --quiet --upgrade pip
	$(PY) -m pip install --quiet pytest hypothesis
	# Installing the browser here is what lets `make check` verify the live
	# interface rather than describe it. Failure is tolerated: the gate degrades
	# to the offline path and says so rather than refusing to run.
	-$(PY) -m pip install --quiet playwright
	-$(PY) -m playwright install chromium

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

liveness: ## Does today's CMC API still answer in the shape this build reads?
	# The only check here that calls CMC. Needs CMC_API_KEY; the dated receipt
	# it writes does not, and carries no payload, no row and no credential.
	PYTHONPATH=$(PKG) $(PY) $(PKG)/live_contract_probe.py

verify: ## Recompute the published receipt from the shipped inputs
	$(PY) $(PKG)/verify_integrity_receipt.py
	$(PY) $(PKG)/verify_catalogue_receipt.py

check-offline: test verify ## The gate with no network and no browser
	$(PY) $(PKG)/verify_submission.py

check: check-offline browser-audit ## The full gate; drives a real browser if one is installed

browser-audit: ## Drive the deployed site, or say plainly that nothing was driven
	@if $(PY) -c "import playwright" >/dev/null 2>&1; then \
		echo "browser audit: driving the deployed site"; \
		PYTHONPATH=$(PKG) $(PY) $(PKG)/verify_public_browser.py --channel ""; \
	else \
		echo "browser audit: SKIPPED - no Playwright in this environment."; \
		echo "  The interface behaviour below is NOT verified by this run:"; \
		echo "  search, decision brief, case-receipt download, wrapper comparison,"; \
		echo "  watchlist, mobile layout, and the network-failure fallback."; \
		echo "  Run 'make install' then 'make check', or 'make check-live', to verify it."; \
	fi

check-live: check-offline ## Force the browser audit and fail if it cannot run
	# `check` degrades to offline when no browser is present. This one does not:
	# it is how you find out that the live assertions have rotted, which they
	# had - the README shipped a command that failed for anyone who ran it.
	PYTHONPATH=$(PKG) $(PY) $(PKG)/verify_public_browser.py --channel ""

clean:
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
	find . -name '*.pyc' -delete
