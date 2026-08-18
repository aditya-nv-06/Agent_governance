VENV=$(CURDIR)/backend/.venv
VENV_CS=$(CURDIR)/customer-service-backend/.venv
VENV_PY=$(VENV)/bin/python
VENV_PIP=$(VENV)/bin/pip
VENV_UVICORN=$(VENV)/bin/uvicorn
VENV_CS_PY=$(VENV_CS)/bin/python
VENV_CS_PIP=$(VENV_CS)/bin/pip
VENV_CS_UVICORN=$(VENV_CS)/bin/uvicorn
NPM=npm

LOG_DIR=logs
PID_DIR=tmp/pids

.PHONY: help install install-backend install-frontend install-customer-service create-venv create-venv-cs db-init dev start-dev stop status prod build prod-start

help:
	@echo "Makefile targets:"
	@echo "  make install            # install backend, customer-service, and frontend deps"
	@echo "  make dev                # start backend, customer-service, and frontend (all dev)"
	@echo "  make stop               # stop background services started by make dev/prod"
	@echo "  make status             # show running PIDs and tail logs"
	@echo "  make prod               # build frontend and start backend in production mode"
	@echo ""
	@echo "Backend targets:"
	@echo "  make install-backend    # install primary backend dependencies"
	@echo "  make start-backend-dev  # start primary backend (dev)"
	@echo ""
	@echo "Customer Service targets:"
	@echo "  make install-customer-service  # install customer service backend dependencies"
	@echo "  make start-cs-dev       # start customer service backend (dev)"

install-backend: create-venv
	$(VENV_PIP) install -r backend/requirements.txt

install-frontend:
	cd frontend && $(NPM) install

create-venv:
	python3 -m venv $(VENV)
	$(VENV_PIP) install --upgrade pip

create-venv-cs:
	python3 -m venv $(VENV_CS)
	$(VENV_CS_PIP) install --upgrade pip

install-customer-service: create-venv-cs
	$(VENV_CS_PIP) install -r customer-service-backend/requirements.txt

install: install-backend install-customer-service install-frontend

db-init:
	# Initialize DB schema (run migrations/initialization via app startup)
	$(VENV_PY) -c "from backend.app.startup import initialize_database; initialize_database()"

_ensure_dirs:
	mkdir -p $(LOG_DIR) $(PID_DIR)

dev: _ensure_dirs start-backend-dev start-cs-dev start-frontend-dev

start-backend-dev: _ensure_dirs
	@echo "Starting primary backend (dev) -> logs/backend.log"
	@bash -lc '$(VENV_UVICORN) backend.app.main:app --reload --port 8000 > "$(CURDIR)/$(LOG_DIR)/backend.log" 2>&1 & echo $$! > "$(CURDIR)/$(PID_DIR)/backend.pid"'

start-cs-dev: _ensure_dirs
	@echo "Starting customer service backend (dev) -> logs/customer-service.log"
	@bash -lc 'cd "$(CURDIR)/customer-service-backend" && $(VENV_CS_PY) run.py > "$(CURDIR)/$(LOG_DIR)/customer-service.log" 2>&1 & echo $$! > "$(CURDIR)/$(PID_DIR)/customer-service.pid"'

start-frontend-dev: _ensure_dirs
	@echo "Starting frontend (dev) -> logs/frontend.log"
	@bash -lc 'cd "$(CURDIR)/frontend" && $(NPM) run dev > "$(CURDIR)/$(LOG_DIR)/frontend.log" 2>&1 & echo $$! > "$(CURDIR)/$(PID_DIR)/frontend.pid"'

stop:
	@mkdir -p $(PID_DIR)
	@echo "Stopping services..."
	@found=0; \
	for f in $(PID_DIR)/*.pid; do \
		if [ -f "$$f" ]; then \
			found=1; \
			pid=$$(cat "$$f" 2>/dev/null || true); \
			if [ -n "$$pid" ] && kill -0 "$$pid" 2>/dev/null; then \
				echo "Killing $$pid"; \
				kill "$$pid" || true; \
			fi; \
			rm -f "$$f"; \
		fi; \
	done; \
	if [ "$$found" -eq 0 ]; then echo "No running services found."; fi

status:
	@mkdir -p $(LOG_DIR) $(PID_DIR)
	@echo "PIDs:"
	@if ls -1 $(PID_DIR)/*.pid >/dev/null 2>&1 2>/dev/null; then \
		ls -l $(PID_DIR)/*.pid; \
	else \
		echo "  No PIDs found (services not started yet)"; \
	fi
	@echo "Logs (tail):"
	@if ls $(LOG_DIR)/* >/dev/null 2>&1 2>/dev/null; then \
		tail -n 20 $(LOG_DIR)/*; \
	else \
		echo "  No log files found yet"; \
	fi

build:
	cd frontend && $(NPM) run build

prod: _ensure_dirs build prod-start

prod-start:
	@echo "Starting backend (prod) -> logs/backend.log"
	@bash -lc '$(VENV_UVICORN) backend.app.main:app --port 8000 --workers 4 > "$(CURDIR)/$(LOG_DIR)/backend.log" 2>&1 & echo $$! > "$(CURDIR)/$(PID_DIR)/backend.pid"'
	@echo "Starting customer service (prod) -> logs/customer-service.log"
	@bash -lc 'cd "$(CURDIR)/customer-service-backend" && $(VENV_CS_PY) run.py > "$(CURDIR)/$(LOG_DIR)/customer-service.log" 2>&1 & echo $$! > "$(CURDIR)/$(PID_DIR)/customer-service.pid"'
	@echo "Starting frontend (prod)"
	@echo "Run: cd frontend && npm run build && npm run preview"
