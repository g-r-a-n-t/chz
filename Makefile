FE_DIR ?= ../fe
CARGO_TARGET_DIR ?= /tmp/chz-fe-target
ROOT_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
FE_SRCS := $(shell find src -type f -name '*.fe') fe.toml

VENV_PY := $(wildcard .venv/bin/python)
PY ?= $(if $(VENV_PY),$(VENV_PY),python3)
PYTHONUNBUFFERED ?= 1
export PYTHONUNBUFFERED

PERFT_DEPTH ?= 2
DIFF_ARGS ?= --skip-random

LONG_DIFF_GAMES ?= 10
LONG_DIFF_MAX_PLIES ?= 60
LONG_DIFF_SAMPLE_MOVES ?= 6

LONG_WALK_GAMES ?= 25
LONG_WALK_MAX_PLIES ?= 200
LONG_WALK_SEED ?= 1337
LONG_WALK_CHECK_EVERY ?= 25

LONG_PERFT_DEPTH ?= 3
LONG_PERFT_IDS ?= start position_3
LONG_PERFT_TIMEOUT_SECS ?= 900

DEAD_DIFF_SAMPLES ?= 2000

.PHONY: fe-check fe-test fe-build fe-build-rules verify mega-vectors metamorphic random-walk dead-diff mega-verify tui long-verify

fe-check:
	cd $(FE_DIR) && CARGO_TARGET_DIR=$(CARGO_TARGET_DIR) cargo run -q -p fe -- check $(ROOT_DIR)

fe-test:
	cd $(FE_DIR) && CARGO_TARGET_DIR=$(CARGO_TARGET_DIR) cargo run -q -p fe -- test $(ROOT_DIR) --backend sonatina

fe-build: out/ChzGame.runtime.bin out/PlayerProxy.runtime.bin out/ChzRules.runtime.bin out/ChzProofs.runtime.bin

out/ChzGame.runtime.bin: $(FE_SRCS)
	# Work around a Sonatina verifier bug when emitting multiple contracts in one run.
	# Build each contract independently.
	@mkdir -p out
	cd $(FE_DIR) && CARGO_TARGET_DIR=$(CARGO_TARGET_DIR) cargo run -q -p fe -- build $(ROOT_DIR) --backend sonatina --contract ChzGame

out/PlayerProxy.runtime.bin: $(FE_SRCS)
	@mkdir -p out
	cd $(FE_DIR) && CARGO_TARGET_DIR=$(CARGO_TARGET_DIR) cargo run -q -p fe -- build $(ROOT_DIR) --backend sonatina --contract PlayerProxy

out/ChzRules.runtime.bin: $(FE_SRCS)
	@mkdir -p out
	cd $(FE_DIR) && CARGO_TARGET_DIR=$(CARGO_TARGET_DIR) cargo run -q -p fe -- build $(ROOT_DIR) --backend sonatina --contract ChzRules

out/ChzProofs.runtime.bin: $(FE_SRCS)
	@mkdir -p out
	cd $(FE_DIR) && CARGO_TARGET_DIR=$(CARGO_TARGET_DIR) cargo run -q -p fe -- build $(ROOT_DIR) --backend sonatina --contract ChzProofs

fe-build-rules: out/ChzRules.runtime.bin out/ChzProofs.runtime.bin
	@true

verify: fe-build-rules
	@echo "== edge cases =="
	@$(PY) scripts/run_edge_cases.py
	@echo "== perft (depth=$(PERFT_DEPTH)) =="
	@$(PY) scripts/perft_hevm.py --depth $(PERFT_DEPTH)
	@echo "== hevm symbolic =="
	@scripts/hevm_symbolic.sh
	@echo "== differential (python-chess) =="
	@if $(PY) -c "import chess" >/dev/null 2>&1; then \
		$(PY) scripts/diff_vs_python_chess.py $(DIFF_ARGS); \
	else \
		echo "skipping diff: python-chess not installed (try: python3 -m venv .venv && .venv/bin/pip install python-chess)"; \
	fi

mega-vectors: fe-build-rules
	@echo "== mega reference vectors =="
	@$(PY) scripts/run_mega_vectors.py

metamorphic: fe-build-rules
	@echo "== metamorphic perft (rank mirror + color swap) =="
	@$(PY) scripts/metamorphic_perft.py --depth $(PERFT_DEPTH)

random-walk: fe-build-rules
	@echo "== random-walk agreement (python-chess) =="
	@$(PY) scripts/random_walk_agreement.py

dead-diff: fe-build-rules
	@echo "== dead-position diff (random minor-only) =="
	@$(PY) scripts/dead_position_diff.py --num-samples $(DEAD_DIFF_SAMPLES)

mega-verify: verify mega-vectors metamorphic dead-diff

tui: fe-build-rules
	@$(PY) scripts/tui_demo.py

long-verify: fe-build-rules
	@echo "== edge cases =="
	@$(PY) scripts/run_edge_cases.py
	@echo "== perft (depth=$(PERFT_DEPTH)) =="
	@$(PY) scripts/perft_hevm.py --depth $(PERFT_DEPTH)
	@echo "== mega reference vectors =="
	@$(PY) scripts/run_mega_vectors.py
	@echo "== metamorphic perft (rank mirror + color swap) =="
	@$(PY) scripts/metamorphic_perft.py --depth $(PERFT_DEPTH)
	@echo "== hevm symbolic =="
	@scripts/hevm_symbolic.sh
	@echo "== differential (python-chess, random) =="
	@if $(PY) -c "import chess" >/dev/null 2>&1; then \
		$(PY) scripts/diff_vs_python_chess.py --num-games $(LONG_DIFF_GAMES) --max-plies $(LONG_DIFF_MAX_PLIES) --sample-moves $(LONG_DIFF_SAMPLE_MOVES); \
	else \
		echo "skipping diff: python-chess not installed (try: python3 -m venv .venv && .venv/bin/pip install python-chess)"; \
	fi
	@echo "== random-walk agreement (python-chess) =="
	@if $(PY) -c "import chess" >/dev/null 2>&1; then \
		$(PY) scripts/random_walk_agreement.py --num-games $(LONG_WALK_GAMES) --max-plies $(LONG_WALK_MAX_PLIES) --seed $(LONG_WALK_SEED) --check-moves-every $(LONG_WALK_CHECK_EVERY); \
	else \
		echo "skipping random-walk: python-chess not installed"; \
	fi
	@echo "== perft subset (depth=$(LONG_PERFT_DEPTH)) =="
	@for id in $(LONG_PERFT_IDS); do \
		echo "-- perft id=$$id"; \
		if command -v timeout >/dev/null 2>&1; then \
			timeout $(LONG_PERFT_TIMEOUT_SECS) $(PY) scripts/perft_hevm.py --id $$id --depth $(LONG_PERFT_DEPTH); \
		else \
			$(PY) scripts/perft_hevm.py --id $$id --depth $(LONG_PERFT_DEPTH); \
		fi; \
	done
