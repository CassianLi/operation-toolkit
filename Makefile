# operation-toolkit — unified ops entrypoints
.PHONY: help ping users root-users db-remind db-restore-docs

TARGET_ENV ?= dev
ANSIBLE_DIR := apps/ansible
PB := cd $(ANSIBLE_DIR) && ansible-playbook

help:
	@echo "operation-toolkit"
	@echo ""
	@echo "  make ping TARGET_ENV=dev|pro          Ansible ping host group"
	@echo "  make users TARGET_ENV=dev|pro         setup_users playbook"
	@echo "  make root-users TARGET_ENV=dev|pro    setup_root_users playbook"
	@echo "  make db-remind                        warn if db-restore due soon / overdue"
	@echo "  make db-restore-docs                  print restore runbook paths"
	@echo ""
	@echo "Default TARGET_ENV=$(TARGET_ENV). Requires local $(ANSIBLE_DIR)/inventory/hosts.yml"

ping:
	cd $(ANSIBLE_DIR) && ansible $(TARGET_ENV)_servers -m ping

users:
	$(PB) playbooks/setup_users.yml -e "target_env=$(TARGET_ENV)"

root-users:
	$(PB) playbooks/setup_root_users.yml -e "target_env=$(TARGET_ENV)"

db-remind:
	./scripts/db-remind.sh

db-restore-docs:
	@echo "calendar: docs/tech/ops-calendar.md"
	@echo "runbook:  docs/tech/db-restore.md"
	@echo "tool:     apps/tools/db-restore/"
	@echo "then:     make db-remind"
