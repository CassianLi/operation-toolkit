# operation-toolkit Scaffold Reorg Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (inline; user requested execute after plan). Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align the repo to `docs/` + `tmp/` + `apps/`, merge two Ansible projects into `apps/ansible/`, relocate DB tools under `apps/tools/`, and add `make db-remind` against an ops calendar.

**Architecture:** Scaffold first; migrate Ansible by copying roles/playbooks and pointing `vars_files` at `vars/`; merge inventories into one gitignored `hosts.yml` plus a redacted `hosts.yml.example`; move tools with rename; root `Makefile` is the only recommended CLI entry.

**Tech Stack:** Ansible (YAML), Make, POSIX shell for `db-remind`, Markdown docs.

## Global Constraints

- No raw IPs, real passwords, private key material, or production DB connection strings in committed files or chat.
- `ansible_host` / docs use local domain names only; examples use placeholders.
- Do not change playbook/role business logic beyond path renames (`global_vars` → `vars`) and doc cleanup.
- Root `.gitignore` must not ignore entire `docs/`.
- Prefer deletion of obsolete duplicate docs over rewriting them.

## File map

| Path | Responsibility |
|------|----------------|
| `README.md` | Root entry: layout + `make` commands |
| `Makefile` | `help`, `ping`, `users`, `root-users`, `db-remind`, `db-restore-docs` |
| `.gitignore` | Unified secrets/tmp ignores |
| `docs/product/*` | Vision + PDS stubs |
| `docs/tech/ops-calendar.md` | Machine-parseable db-restore schedule |
| `docs/tech/ansible.md` | Ansible usage (no secrets) |
| `docs/tech/db-restore.md` | Three-year restore runbook |
| `docs/agent/README.md` | Agent hard constraints |
| `scripts/db-remind.sh` | Parse calendar; exit 1 in warn window |
| `tmp/**/.gitkeep` | Scratch placeholders |
| `apps/ansible/**` | Merged Ansible project |
| `apps/tools/db-restore/**` | From `tools/rds-bak-tools` |
| `apps/tools/db-history-cleanup/**` | From `tools/prod-db-history-cleanup` |

---

### Task 1: Branch + scaffold skeleton

**Files:**
- Create: `docs/product/README.md`, `docs/product/vision.md`, `docs/product/product-design-specification.md`
- Create: `docs/design/README.md`, `docs/tech/README.md`, `docs/agent/README.md`
- Create: `tmp/cases/.gitkeep`, `tmp/logs/.gitkeep`, `tmp/out/.gitkeep`, `tmp/store/.gitkeep`
- Create: `apps/README.md`
- Modify: `.gitignore` (expand per design §6)
- Create: `README.md` (minimal; fill commands in Task 5)

**Interfaces:**
- Produces: directory layout ready for migrations

- [ ] **Step 1: Create branch**

```bash
git checkout -b chore/scaffold-reorg
```

- [ ] **Step 2: Create dirs and stub docs**

Create product/agent/tech/design stubs (Chinese, short). Create `tmp/*/.gitkeep` and `apps/README.md`.

- [ ] **Step 3: Expand root `.gitignore`**

Ensure ignores cover: `tmp/*` with `!tmp/**/.gitkeep`, `.env*`, `*.pem`, `**/inventory/hosts.yml`, `**/vars/{users,root_users,ssh_keys,groups}.yml`, `**/config/database.yaml`, `apps/tools/**/{backups,logs}/`, `*.log`. Keep existing `*.tar.gz` / `root_users.yml` patterns or fold into the vars rules.

- [ ] **Step 4: Write minimal root `README.md`**

Purpose one-liner + directory table; command table can say “see Makefile / `make help`” until Task 5.

- [ ] **Step 5: Verify layout**

```bash
test -d docs/product && test -d tmp/logs && test -f apps/README.md && test -f README.md
```

Expected: exit 0

- [ ] **Step 6: Commit**

```bash
git add README.md .gitignore docs/product docs/design docs/tech docs/agent apps/README.md tmp
git commit -m "chore: scaffold docs/tmp/apps workspace layout"
```

---

### Task 2: Merge Ansible into `apps/ansible/`

**Files:**
- Create: `apps/ansible/` tree (roles, playbooks, ansible.cfg, vars, inventory)
- Modify: all playbooks `vars_files` paths `../global_vars/` → `../vars/`
- Create: `apps/ansible/inventory/hosts.yml.example` (redacted)
- Create: local `apps/ansible/inventory/hosts.yml` (gitignored; merge of both old inventories)
- Create: `apps/ansible/vars/*.example` from existing examples + sanitized stubs
- Create: `apps/ansible/README.md`, `docs/tech/ansible.md`
- Create: `apps/ansible/logs/.gitkeep`

**Interfaces:**
- Consumes: `operation/ansible-asl/**`, `operation/ansible-asl-ser-root/**`
- Produces: runnable tree under `apps/ansible/` with `vars_files: ../vars/...`

- [ ] **Step 1: Copy structural files**

```bash
mkdir -p apps/ansible/{inventory,vars,roles,playbooks,scripts,logs}
cp operation/ansible-asl/ansible.cfg apps/ansible/
# merge roles
cp -R operation/ansible-asl/roles/* apps/ansible/roles/
cp -R operation/ansible-asl-ser-root/roles/* apps/ansible/roles/
# merge playbooks
cp operation/ansible-asl/playbooks/*.yml apps/ansible/playbooks/
cp operation/ansible-asl-ser-root/playbooks/*.yml apps/ansible/playbooks/
cp operation/ansible-asl/scripts/* apps/ansible/scripts/ 2>/dev/null || true
# vars: copy non-secret + examples
cp operation/ansible-asl/global_vars/system.yml apps/ansible/vars/
cp operation/ansible-asl/global_vars/users.yml.example apps/ansible/vars/
cp operation/ansible-asl-ser-root/global_vars/system.yml apps/ansible/vars/system-root.yml
# prefer single system.yml: keep asl system.yml; copy cleanup from root project
cp operation/ansible-asl-ser-root/global_vars/cleanup_users.yml apps/ansible/vars/
cp operation/ansible-asl-ser-root/global_vars/ssh_keys.yml.example apps/ansible/vars/
```

Copy local secret/real config for operator use only (do not `git add`):

```bash
cp operation/ansible-asl/global_vars/users.yml apps/ansible/vars/ 2>/dev/null || true
cp operation/ansible-asl/global_vars/groups.yml apps/ansible/vars/ 2>/dev/null || true
cp operation/ansible-asl-ser-root/global_vars/root_users.yml apps/ansible/vars/ 2>/dev/null || true
```

Create `groups.yml.example` and `root_users.yml.example` with placeholder usernames only (no real keys).

- [ ] **Step 2: Merge inventory locally + example**

- Write `hosts.yml` as union of both inventories (prefer ser-root as base if it has more hosts). Do not commit.
- Generate `hosts.yml.example`: same hostnames/groups; set `ansible_host` to `<hostname>.example.local`, `ansible_user` to `CHANGE_ME`, key path to `~/.ssh/id_ed25519`.

- [ ] **Step 3: Rewrite playbook vars_files**

In every `apps/ansible/playbooks/*.yml`, replace `../global_vars/` with `../vars/`. Update any user-facing message that says `global_vars/`.

Also set `log_path` friendly: keep `logs/ansible.log` under `apps/ansible/`.

- [ ] **Step 4: Docs**

- `apps/ansible/README.md`: short; point to `make` and `docs/tech/ansible.md`
- `docs/tech/ansible.md`: how to copy examples, `ENV=dev|pro`, main playbooks; no IPs

- [ ] **Step 5: Verify**

```bash
rg -n 'global_vars' apps/ansible/playbooks && echo FAIL || echo OK
test -f apps/ansible/inventory/hosts.yml.example
# list hosts without dumping ansible_host values:
ansible-inventory -i apps/ansible/inventory/hosts.yml --list 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(sorted(d.get('_meta',{}).get('hostvars',{}).keys()) or 'no-local-hosts')"
```

Expected: `OK`; example exists; hostnames print without needing to show IPs (if local hosts.yml present).

- [ ] **Step 6: Commit (tracked files only)**

```bash
git add apps/ansible docs/tech/ansible.md
git status   # confirm hosts.yml / users.yml / root_users.yml / groups.yml / ssh_keys.yml NOT staged
git commit -m "feat: merge ansible projects under apps/ansible"
```

---

### Task 3: Move DB tools + ops calendar + db-remind

**Files:**
- Move: `tools/rds-bak-tools` → `apps/tools/db-restore`
- Move: `tools/prod-db-history-cleanup` → `apps/tools/db-history-cleanup`
- Create: `docs/tech/ops-calendar.md`, `docs/tech/db-restore.md`
- Create: `scripts/db-remind.sh`
- Delete or leave empty: old `tools/` (remove `*.tar.gz` from tracking consideration via gitignore)

**Interfaces:**
- `scripts/db-remind.sh` reads `docs/tech/ops-calendar.md` section `## db-restore` fields `next_due`, `warn_days`
- Exit `0` if `today < next_due - warn_days`; exit `1` if within window or overdue; print checklist path

- [ ] **Step 1: Move directories**

```bash
mkdir -p apps/tools
git mv tools/rds-bak-tools apps/tools/db-restore 2>/dev/null || mv tools/rds-bak-tools apps/tools/db-restore
git mv tools/prod-db-history-cleanup apps/tools/db-history-cleanup 2>/dev/null || mv tools/prod-db-history-cleanup apps/tools/db-history-cleanup
```

Update internal README paths that say `tools/rds-bak-tools` → `apps/tools/db-restore` (and cleanup similarly). Do not commit `.env` or `database.yaml` if present.

- [ ] **Step 2: Write `docs/tech/ops-calendar.md`**

Include:

```markdown
## db-restore
- last_run: 2025-07-23
- next_due: 2028-07-23
- warn_days: 90
- runbook: ./db-restore.md
```

(Adjust `last_run` only if a known safe public milestone date exists in old docs; otherwise use the design example dates.)

- [ ] **Step 3: Write `docs/tech/db-restore.md`**

Checklist: copy `env.example` → `.env` locally; place backup file; start compose; verify. No passwords. Point to `apps/tools/db-restore/`.

- [ ] **Step 4: Implement `scripts/db-remind.sh`**

Parse the four fields under `## db-restore` with `awk`/`sed`. Compare dates with `date -j` (macOS) or `date -d` (Linux); detect OS. Print status; exit 1 in warn/overdue.

Minimal self-check:

```bash
# with a temp calendar where next_due is yesterday → expect exit 1
```

- [ ] **Step 5: Commit**

```bash
git add apps/tools docs/tech/ops-calendar.md docs/tech/db-restore.md scripts/db-remind.sh
git commit -m "feat: relocate DB tools and add ops calendar remind"
```

---

### Task 4: Root Makefile

**Files:**
- Create: `Makefile`
- Modify: `README.md` (command table)

**Interfaces:**
- `make help`
- `make ping ENV=dev|pro` → `cd apps/ansible && ansible <ENV>_servers -m ping`
- `make users ENV=…` → `setup_users.yml -e target_env=$(ENV)`
- `make root-users ENV=…` → `setup_root_users.yml -e target_env=$(ENV)`
- `make db-remind` → `scripts/db-remind.sh`
- `make db-restore-docs` → print paths to runbook + calendar

- [ ] **Step 1: Write Makefile** with `.PHONY` and `help` default goal; `ENV ?= dev`

- [ ] **Step 2: Verify**

```bash
make help
make db-remind; echo exit:$?
```

- [ ] **Step 3: Commit**

```bash
git add Makefile README.md
git commit -m "feat: add root Makefile for ansible and db-remind"
```

---

### Task 5: Remove old trees + finalize docs

**Files:**
- Delete: `operation/ansible-asl`, `operation/ansible-asl-ser-root`, empty `operation/`, empty `tools/`
- Delete or relocate: `podman-vs-docker-comparison.md` → `docs/tech/` or delete if obsolete
- Handle: `docs/deployment_guide.md` — if it contains IPs/secrets, leave untracked or scrub before add; prefer scrub placeholders then add under `docs/tech/` only if still useful
- Create: short `MOVED.md` at repo root only if needed for one release; otherwise skip (YAGNI — Makefile is enough)

- [ ] **Step 1: Remove old ansible/tools dirs via `git rm -r` where tracked**

- [ ] **Step 2: Grep committed tree for IP-like patterns in docs**

```bash
rg -nN '\b([0-9]{1,3}\.){3}[0-9]{1,3}\b' docs apps/ansible/README.md apps/ansible/inventory/hosts.yml.example README.md Makefile || true
```

Replace any hits in tracked files with domain placeholders.

- [ ] **Step 3: Final verify**

```bash
make help && make db-remind; test -d apps/ansible/roles/user_management; test -d apps/tools/db-restore; test ! -d operation/ansible-asl
```

- [ ] **Step 4: Commit**

```bash
git add -A
git status   # re-check no secrets staged
git commit -m "chore: remove legacy operation/ and tools/ paths"
```

---

## Spec coverage checklist

| Spec item | Task |
|-----------|------|
| docs/tmp/apps layout | 1 |
| Merge ansible | 2 |
| DB tools move | 3 |
| ops-calendar + db-remind | 3–4 |
| Makefile commands | 4 |
| Security gitignore / no IP | 1, 2, 5 |
| Remove old paths | 5 |
| Non-goals (no logic rewrite, no Vault) | honored throughout |
