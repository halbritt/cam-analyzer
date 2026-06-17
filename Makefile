# cam-analyzer — local enforcement of the honesty guards (S1 / WS-ENFORCE).
#
# Thesis (D007): honesty is enforced by MECHANISM, not reviewer vigilance.
# This box is local-first / no-cloud, so the mechanism is a `make check`
# target plus a local pre-push hook — not cloud CI.
#
# `make check` runs the four guards in order:
#   1. test    — pytest (the C1 AST boundary test, conformance traps, …)
#   2. types   — mypy --strict (the phantom-type harness)
#   3. lint    — ruff
#   4. imports — import-linter (the C1 contract in [tool.importlinter])
#
# Graceful degradation: mypy and import-linter are optional install-time deps
# (`.[dev]`). When absent, the `types`/`imports` targets print a clear
# "SKIPPED: ... not installed" and succeed, so `make check` is green on a
# bare checkout. Install them with `pip install -e '.[dev]'`.
#
# CAM_ANALYZER_REQUIRE_MYPY semantics (deliberate):
#   The conformance/typing test treats a *missing* mypy as a HARD FAILURE
#   only when CAM_ANALYZER_REQUIRE_MYPY=1 — otherwise it skips. To keep
#   `make check` green here today (mypy genuinely absent) yet ENFORCE mypy
#   the instant it is installed, we DO NOT blanket-export the var. Instead
#   the `test` target sets CAM_ANALYZER_REQUIRE_MYPY=1 *only when mypy is
#   importable*. Net effect:
#     - mypy absent  -> var unset    -> typing trap skips      -> green
#     - mypy present -> var=1        -> typing trap must pass   -> enforced
#   The `types` target additionally runs mypy directly, so an installed-but-
#   failing mypy is caught two ways (the trap and the direct run).

PYTHON ?= python3

.PHONY: check test types lint imports hooks

# Full local guard suite. Mirrors what the .githooks/pre-push hook runs.
check: test types lint imports

# pytest. CAM_ANALYZER_REQUIRE_MYPY is exported to the test process ONLY when
# mypy is importable — so the typing trap enforces under an installed mypy but
# skips (green) on a bare checkout where mypy is genuinely absent.
test:
	@if $(PYTHON) -c "import mypy" >/dev/null 2>&1; then \
		echo "mypy present -> CAM_ANALYZER_REQUIRE_MYPY=1 (typing trap enforced)"; \
		CAM_ANALYZER_REQUIRE_MYPY=1 $(PYTHON) -m pytest -q; \
	else \
		echo "mypy absent -> CAM_ANALYZER_REQUIRE_MYPY unset (typing trap may skip)"; \
		$(PYTHON) -m pytest -q; \
	fi

# mypy --strict (config in [tool.mypy], files = src/cam_analyzer). Skips cleanly
# when mypy is not installed.
types:
	@if $(PYTHON) -c "import mypy" >/dev/null 2>&1; then \
		$(PYTHON) -m mypy; \
	else \
		echo "SKIPPED: mypy not installed (pip install -e '.[dev]')"; \
	fi

# ruff. Always available in this env; a real failure must fail the target.
lint:
	$(PYTHON) -m ruff check .

# import-linter (the C1 contract). Skips cleanly when not installed. The
# always-on equivalent is tests/test_architecture_boundary.py (runs under `test`).
imports:
	@if $(PYTHON) -c "import importlinter" >/dev/null 2>&1; then \
		$(PYTHON) -m importlinter lint; \
	else \
		echo "SKIPPED: import-linter not installed (pip install -e '.[dev]')"; \
	fi

# Activate the local pre-push hook (runs `make check` before every push).
# Opt-in: run once per clone. Does not touch any tracked file.
hooks:
	git config core.hooksPath .githooks
	@echo "pre-push hook enabled (core.hooksPath=.githooks). It runs 'make check'."
