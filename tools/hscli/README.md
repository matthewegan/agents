# hscli

Agent-friendly CLI for HubSpot CMS. JSON to stdout, errors to stderr, stable exit codes.

## Install

```bash
uv tool install --from ./tools/hscli hscli
```

## Authentication

hscli automatically uses the HubSpot CLI's personal access key — no separate token setup required.

### Quick start

If you already have the HubSpot CLI authenticated, hscli works immediately:

```bash
hscli auth check
```

### First-time setup

If you haven't authenticated the HubSpot CLI yet:

```bash
npm install -g @hubspot/cli@latest
hs account auth
```

Follow the prompts to enter your personal access key (found at **Development > Keys > Personal Access Key** in HubSpot).

### How it works

hscli looks for credentials in this order:

1. `HUBSPOT_ACCESS_TOKEN` environment variable (override)
2. `~/.hscli/config.yml` (HubSpot CLI config) — reads the personal access key and automatically exchanges it for a short-lived API token

The HubSpot CLI path is the recommended default. Token refresh is automatic and transparent.

## Commands

### Landing Pages

```bash
# List all landing pages
hscli cms landing-pages list

# List published landing pages
hscli cms landing-pages list --state PUBLISHED

# Filter by name
hscli cms landing-pages list --name "campaign"

# Get a specific page
hscli cms landing-pages get <page-id>

# Find pages using a specific module
hscli cms landing-pages find-by-module "rich_text"
hscli cms landing-pages find-by-module "custom-button" --state PUBLISHED

# Limit results returned
hscli cms landing-pages find-by-module "rich_text" --limit 5

# Limit pages scanned from API
hscli cms landing-pages find-by-module "rich_text" --scan-limit 100
```

### Raw / Escape Hatch

```bash
# Any authenticated GET
hscli raw GET /cms/v3/pages/site-pages

# With query params
hscli raw GET /cms/v3/pages/landing-pages -q state=PUBLISHED -q limit=5

# JSON body from string or file
hscli raw POST /some/endpoint -d '{"key": "value"}'
hscli raw POST /some/endpoint -d @payload.json

# Paginate any endpoint
hscli paginate /cms/v3/pages/landing-pages -q state=PUBLISHED --limit 20
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Unexpected error |
| 2 | CLI usage error (bad flags/args) |
| 3 | Not found (404) |
| 4 | Validation / bad input |
| 5 | Missing config / credentials |
| 10 | Auth failure (401/403) |
