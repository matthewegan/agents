# agents

Skills and tools I use with [Claude Code](https://docs.anthropic.com/en/docs/claude-code).

## Skills

Claude Code skills are markdown files that teach the agent how to use a tool or follow a workflow. Each skill lives in `skills/<name>/SKILL.md`.

| Skill | Description |
|-------|-------------|
| `aws-cdk-ts` | AWS CDK v2 with TypeScript reference |
| `aws-redshift-data-api` | AWS Redshift Data API reference |
| `bbcli` | Bitbucket Cloud CLI (`bb`) — pairs with `tools/bbcli` |
| `contentstack-js-management-sdk` | Contentstack JS Management SDK guide |
| `contentstack-ts-delivery-sdk` | Contentstack TS Delivery SDK guide |
| `obsidian` | Obsidian vault interaction via the Obsidian CLI |
| `tailwindcss-v4` | Tailwind CSS v4 reference |

### Using a skill

Symlink the skill directory into your Claude Code skills folder:

```sh
ln -s /path/to/agents/skills/bbcli ~/.claude/skills/bbcli
```

Or symlink all of them:

```sh
for skill in skills/*/; do
  name=$(basename "$skill")
  ln -s "$(pwd)/$skill" ~/.claude/skills/"$name"
done
```

## Tools

### bbcli

An agent-friendly CLI for Bitbucket Cloud. JSON output, stable exit codes, automatic pagination.

```sh
uv tool install ./tools/bbcli
```

See `tools/bbcli/README.md` for full details and [skills/bbcli/SKILL.md](skills/bbcli/SKILL.md) for the Claude Code skill that teaches the agent how to use it.
