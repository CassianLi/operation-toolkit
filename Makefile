# operation-toolkit — unified ops entrypoints
.PHONY: help ping users-simple users-legacy root-users-legacy db-remind db-restore-docs

TARGET_ENV ?= dev
LIMIT ?=
ANSIBLE_DIR := apps/ansible
PB := cd $(ANSIBLE_DIR) && ansible-playbook
LIMIT_FLAG := $(if $(LIMIT),--limit $(LIMIT),)

help:
	@echo "operation-toolkit"
	@echo ""
	@echo "  【新机 simple — 推荐】"
	@echo "  make ping TARGET_ENV=dev|pro [LIMIT=host]"
	@echo "  make users-simple TARGET_ENV=… LIMIT=host"
	@echo ""
	@echo "  【旧机 legacy — 已部署勿改目录属组】"
	@echo "  make users-legacy TARGET_ENV=… [LIMIT=host]"
	@echo "  make root-users-legacy TARGET_ENV=… [LIMIT=host]"
	@echo ""
	@echo "  make db-remind / make db-restore-docs"
	@echo ""
	@echo "策略: docs/tech/account-policy.md"
	@echo "备忘: simple 目录 root:root，写 /opt|/data 用 sudo"

ping:
	cd $(ANSIBLE_DIR) && ansible $(TARGET_ENV)_servers -m ping $(LIMIT_FLAG)

users-simple:
	@test -n "$(LIMIT)" || (echo "users-simple 必须指定 LIMIT=主机名"; exit 1)
	$(PB) playbooks/setup_users_simple.yml -e "target_env=$(TARGET_ENV)" --limit "$(LIMIT)"

users-legacy:
	$(PB) playbooks/legacy/setup_users.yml -e "target_env=$(TARGET_ENV)" $(LIMIT_FLAG)

root-users-legacy:
	$(PB) playbooks/legacy/setup_root_users.yml -e "target_env=$(TARGET_ENV)" $(LIMIT_FLAG)

db-remind:
	./scripts/db-remind.sh

db-restore-docs:
	@echo "calendar: docs/tech/ops-calendar.md"
	@echo "runbook:  docs/tech/db-restore.md"
	@echo "tool:     apps/tools/db-restore/"
