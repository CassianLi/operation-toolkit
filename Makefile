# operation-toolkit — unified ops entrypoints
.PHONY: help ping users root-users db-remind db-restore-docs

ENV ?= dev
ANSIBLE_DIR := apps/ansible
PB := cd $(ANSIBLE_DIR) && ansible-playbook

help:
	@echo "operation-toolkit"
	@echo ""
	@echo "  make ping ENV=dev|pro          Ansible ping host group"
	@echo "  make users ENV=dev|pro         setup_users playbook"
	@echo "  make root-users ENV=dev|pro    setup_root_users playbook"
	@echo "  make db-remind                 warn if db-restore due soon / overdue"
	@echo "  make db-restore-docs           print restore runbook paths"
	@echo ""
	@echo "Default ENV=$(ENV). Requires local $(ANSIBLE_DIR)/inventory/hosts.yml"

ping:
	cd $(ANSIBLE_DIR) && ansible $(ENV)_servers -m ping

users:
	$(PB) playbooks/setup_users.yml -e "target_env=$(ENV)"

root-users:
	$(PB) playbooks/setup_root_users.yml -e "target_env=$(ENV)"

db-remind:
	./scripts/db-remind.sh

db-restore-docs:
	@echo "calendar: docs/tech/ops-calendar.md"
	@echo "runbook:  docs/tech/db-restore.md"
	@echo "tool:     apps/tools/db-restore/"
	@echo "then:     make db-remind"
