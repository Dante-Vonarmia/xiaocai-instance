SHELL := /bin/bash

COMPOSE ?= docker-compose
ENV_FILE ?= .env
INSTANCE_PROJECT ?= inst-xiaocai-dev
INSTANCE_COMPOSE_FILE ?= compose.instance.yml
DEVLIB_COMPOSE_FILE ?= compose.devlib-flare.yml
INSTANCE_COMPOSE := $(COMPOSE) -p $(INSTANCE_PROJECT) -f $(INSTANCE_COMPOSE_FILE)
DEV_COMPOSE := $(COMPOSE) -p $(INSTANCE_PROJECT) -f $(INSTANCE_COMPOSE_FILE) -f $(DEVLIB_COMPOSE_FILE)

.PHONY: help init env-check \
	start stop restart \
	up-instance down-instance build-instance ps-instance logs-instance \
	up-dev down-dev build-dev ps-dev logs-dev logs-devlib \
	config-instance config-dev db-migrate backup-db restore-db domain-pack-check pack-registry-check domain-acceptance health api-smoke acceptance clean-logs

help:
	@echo "xiaocai deploy targets"
	@echo ""
	@echo "  make init           # create .env from .env.example (if missing)"
	@echo "  make start          # alias of up-instance"
	@echo "  make stop           # alias of down-dev + down-instance"
	@echo "  make restart        # stop + start"
	@echo ""
	@echo "  make up-instance    # start instance-only stack (delivery baseline)"
	@echo "  make down-instance  # stop instance-only stack"
	@echo "  make build-instance # build instance images"
	@echo "  make ps-instance    # instance stack status"
	@echo "  make logs-instance  # instance stack logs"
	@echo "  make config-instance# validate instance compose"
	@echo ""
	@echo "  make up-dev         # start instance + devlib flare kernel"
	@echo "  make down-dev       # stop instance + devlib stack"
	@echo "  make build-dev      # build instance + devlib images"
	@echo "  make ps-dev         # instance + devlib status"
	@echo "  make logs-dev       # instance + devlib logs"
	@echo "  make logs-devlib    # devlib flare kernel logs"
	@echo "  make config-dev     # validate instance + devlib compose"
	@echo "  make domain-pack-check # validate xiaocai domain-pack consistency"
	@echo "  make pack-registry-check # validate base profile registry + tenant bindings refs"
	@echo "  make domain-acceptance # domain-pack-check + api-smoke release gate"
	@echo "  make db-migrate     # run xiaocai storage migrations"
	@echo "  make backup-db      # backup PostgreSQL to deploy/backups/"
	@echo "  make restore-db FILE=... # restore PostgreSQL from sql file"
	@echo ""
	@echo "  make health         # run health check"
	@echo "  make api-smoke      # auth/chat run/chat stream smoke"
	@echo "  make acceptance     # write Gate logs"
	@echo "  make clean-logs     # remove generated *.log files"

init:
	@if [ -f "$(ENV_FILE)" ]; then \
		echo "$(ENV_FILE) already exists"; \
	else \
		cp .env.example "$(ENV_FILE)"; \
		echo "created $(ENV_FILE) from .env.example"; \
	fi

env-check:
	@if [ ! -f "$(ENV_FILE)" ]; then \
		echo "$(ENV_FILE) not found. Run: make init"; \
		exit 1; \
	fi

start: up-instance

stop: down-dev down-instance

restart: stop start

up-instance: env-check
	$(INSTANCE_COMPOSE) up -d

down-instance:
	$(INSTANCE_COMPOSE) down

build-instance: env-check
	$(INSTANCE_COMPOSE) build

ps-instance:
	$(INSTANCE_COMPOSE) ps

logs-instance:
	$(INSTANCE_COMPOSE) logs -f

config-instance: env-check
	$(INSTANCE_COMPOSE) config

up-dev: env-check
	$(DEV_COMPOSE) up -d

down-dev:
	$(DEV_COMPOSE) down

build-dev: env-check
	$(DEV_COMPOSE) build

ps-dev:
	$(DEV_COMPOSE) ps

logs-dev:
	$(DEV_COMPOSE) logs -f

logs-devlib:
	$(DEV_COMPOSE) logs -f devlib-flare-kernel

config-dev: env-check
	$(DEV_COMPOSE) config

db-migrate: env-check
	$(INSTANCE_COMPOSE) run --rm --no-deps inst-xiaocai-api python -m xiaocai_instance_api.storage.migrate

backup-db: env-check
	./scripts/backup-db.sh

restore-db: env-check
	@if [ -z "$(FILE)" ]; then \
		echo "usage: make restore-db FILE=./backups/xxx.sql"; \
		exit 1; \
	fi
	./scripts/restore-db.sh "$(FILE)"

domain-pack-check:
	ruby ../domain-pack/scripts/validate_domain_pack.rb

pack-registry-check:
	bash ../scripts/pack-registry-check.sh

domain-acceptance: env-check
	@$(MAKE) domain-pack-check
	@$(MAKE) api-smoke
	@if ! grep -q '"access_token":"' auth-test.log; then \
		echo "domain acceptance failed: auth-test.log missing access_token"; \
		exit 1; \
	fi
	@if ! grep -q '"message":"' chat-run-test.log; then \
		echo "domain acceptance failed: chat-run-test.log missing message"; \
		exit 1; \
	fi
	@if ! grep -q 'event: done' chat-stream-test.log; then \
		echo "domain acceptance failed: chat-stream-test.log missing done event"; \
		exit 1; \
	fi
	@echo "domain acceptance passed: domain-pack-check + api-smoke assertions"

health:
	./scripts/health-check.sh

api-smoke:
	@MOCK=$${MOCK_AUTH:-true}; \
	if [ "$$MOCK" = "true" ]; then \
		AUTH_PAYLOAD='{"mock": true, "mock_user_id": "root-local-dev"}'; \
	else \
		ROOT_TOKEN=$${ROOT_AUTH_TOKEN:-root-local-dev-token}; \
		AUTH_PAYLOAD=$$(printf '{"root_token":"%s"}' "$$ROOT_TOKEN"); \
	fi; \
	AUTH_JSON=$$(curl -sS -X POST http://localhost:$${API_PORT:-8001}/auth/exchange \
		-H 'Content-Type: application/json' \
		-d "$$AUTH_PAYLOAD"); \
	printf '%s\n' "$$AUTH_JSON" > auth-test.log; \
	TOKEN=$$(printf '%s' "$$AUTH_JSON" | sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p'); \
	curl -sS -X POST http://localhost:$${API_PORT:-8001}/chat/run \
		-H 'Content-Type: application/json' \
		-H "Authorization: Bearer $${TOKEN}" \
		-d '{"message":"你好","session_id":"test-123"}' \
		> chat-run-test.log; \
	curl -sS -N --max-time 10 -X POST http://localhost:$${API_PORT:-8001}/chat/stream \
		-H 'Content-Type: application/json' \
		-H "Authorization: Bearer $${TOKEN}" \
		-d '{"message":"你好","session_id":"test-123"}' \
		> chat-stream-test.log; \
	echo "api smoke logs generated: auth-test.log chat-run-test.log chat-stream-test.log"

acceptance: env-check
	$(DEV_COMPOSE) config > config-check.log 2>&1
	$(DEV_COMPOSE) ps > containers.log
	./scripts/health-check.sh > health.log 2>&1
	$(DEV_COMPOSE) logs > service.log 2>&1
	curl -f http://localhost:$${WEB_PORT:-3001} > frontend.log 2>&1
	@$(MAKE) api-smoke
	@echo "acceptance logs generated in deploy/"

clean-logs:
	rm -f config-check.log containers.log health.log service.log frontend.log auth-test.log chat-run-test.log chat-stream-test.log
