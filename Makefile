# Makefile

.PHONY: build_venv
build_venv:
	test -d .venv || python3.6 -m venv .venv --prompt Harvester
	.venv/bin/pip install -U pip setuptools wheel

.PHONY: dev
dev: build_venv
	.venv/bin/pip install -Ur requirements_cpu.txt -r requirements_dev.txt

.PHONY: clean
clean:
	rm -fr .venv/

