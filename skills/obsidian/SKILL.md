---
name: obsidian
description: "Interact with an Obsidian vault via the official Obsidian CLI. Use this skill whenever the user mentions Obsidian, their vault, notes, daily notes, or asks to create plans, drafts, documents, or artifacts that belong in their vault. Also use when the user asks to search their notes, find connections between ideas, read a note, manage tasks, or work with tags/properties. If the user says \"put this in my vault\", \"search my notes\", \"add to my daily note\", or similar — this skill applies. Check the user's CLAUDE.md for vault name and path configuration."
---

# Obsidian CLI

The official Obsidian CLI lets you read, write, search, and manage an Obsidian vault from the terminal. It operates as a remote control for the running Obsidian desktop app — if Obsidian isn't running, the first command launches it.

## Resolving the target vault

The CLI needs to know which vault to target. Resolution order:

1. **Current working directory** — if the terminal is inside a vault folder, it's used automatically.
2. **Explicit `vault=` parameter** — use `vault=<name>` as the first parameter: `obsidian vault=MyVault daily`
3. **Active vault** — if neither of the above applies, the currently active vault in Obsidian is used.

Check the user's CLAUDE.md or project instructions for which vault to target. If not specified and not obvious from cwd, ask. To list available vaults: `obsidian vaults verbose`.

## Prerequisites

Requires Obsidian 1.12+ with CLI enabled (Settings > General > Command line interface). On macOS the binary lives at `/usr/local/bin/obsidian`. Verify with:

```sh
obsidian version
```

If the CLI can't connect, the user needs to open Obsidian first.

## Command syntax

```sh
obsidian [vault=<name>] <command> [params...] [flags...]
```

- **Parameters** take values: `name=Note content="Hello world"`
- **Flags** are boolean switches: `open overwrite`
- **Multiline content**: use `\n` for newlines, `\t` for tabs
- **File targeting**: `file=<name>` (wikilink-style resolution) or `path=<exact/path.md>` from vault root
- **Output formats**: many commands accept `format=json|tsv|csv|md`
- **Clipboard**: add `--copy` to any command to copy output to clipboard

## Creating notes

```sh
obsidian create name=Note content="Hello world"
obsidian create path="projects/my-plan.md" content="# Plan\n\nDetails here"
obsidian create name=Note template=MyTemplate open    # from template, then open it
obsidian create path="drafts/doc.md" content="..." overwrite  # overwrite if exists
```

For substantial documents (multiple sections, long prose), write directly to the vault's filesystem path instead of using `content=`. Obsidian picks up new files automatically. Use `obsidian vault info=path` to get the vault's filesystem path if needed. This avoids shell escaping issues with long content strings.

## Reading notes

```sh
obsidian read                           # active file
obsidian read file=Recipe               # by name (wikilink resolution)
obsidian read path="folder/note.md"     # by exact path
```

## Searching

```sh
obsidian search query="meeting notes"                    # matching file paths
obsidian search:context query="API endpoint" format=json # grep-style with line context
obsidian search query="deadline" path=projects           # within a folder
obsidian search query="TODO" total                       # count matches
```

## Connections and links

```sh
obsidian backlinks file=SomeNote        # what links to this note
obsidian links file=SomeNote            # outgoing links from this note
obsidian orphans                        # notes with no incoming links
obsidian deadends                       # notes with no outgoing links
obsidian unresolved                     # broken/unresolved wikilinks
```

When asked to "find connections" or "what relates to X", combine search with backlinks/links to map how notes relate.

## Daily notes

```sh
obsidian daily                                        # open today's daily note
obsidian daily:read                                   # read its contents
obsidian daily:path                                   # get path (even if not yet created)
obsidian daily:append content="- [ ] Buy groceries"   # append content
obsidian daily:prepend content="## Morning standup"    # prepend after frontmatter
```

## Tasks

```sh
obsidian tasks                        # all tasks in vault
obsidian tasks todo                   # incomplete only
obsidian tasks done                   # completed only
obsidian tasks daily                  # from today's daily note
obsidian tasks file=SomeNote verbose  # grouped by file with line numbers
obsidian task ref="Note.md:8" toggle  # toggle a specific task
obsidian task daily line=3 done       # mark daily note task complete
```

## Tags and properties

```sh
obsidian tags counts                                    # all tags with counts
obsidian tags file=SomeNote                             # tags for a specific note
obsidian tag name=project verbose                       # files with a tag
obsidian properties file=SomeNote                       # note properties (yaml frontmatter)
obsidian property:set file=Note name=status value=active
obsidian property:read file=Note name=status
obsidian property:remove file=Note name=status
```

## File management

```sh
obsidian files                          # list all files
obsidian files folder=projects          # files in a folder
obsidian folders                        # list all folders
obsidian file file=Note                 # file info (path, size, dates)
obsidian open file=Note newtab          # open in Obsidian
obsidian move file=OldName to="new/location.md"   # move (updates wikilinks)
obsidian rename file=OldName name=NewName          # rename (updates wikilinks)
obsidian delete file=Scratch                       # move to trash
obsidian delete file=Scratch permanent             # permanent delete
```

## Outline

```sh
obsidian outline file=SomeNote               # heading tree
obsidian outline file=SomeNote format=json   # structured headings
```

## Templates

```sh
obsidian templates                        # list available templates
obsidian template:read name=MyTemplate    # read template content
obsidian template:read name=MyTemplate resolve title="My Note"  # with variables resolved
obsidian template:insert name=MyTemplate  # insert into active file
```

## Bookmarks

```sh
obsidian bookmarks                        # list bookmarks
obsidian bookmark file=Note               # bookmark a file
obsidian bookmark search="TODO"           # bookmark a search
```

## Version history and diff

```sh
obsidian diff file=Note                   # list versions
obsidian diff file=Note from=1            # compare latest version to current
obsidian diff file=Note from=2 to=1       # compare two versions
obsidian history:restore file=Note version=2  # restore a version
```

## Commands and hotkeys

```sh
obsidian commands                         # list all command IDs
obsidian command id="editor:toggle-bold"  # execute any Obsidian command
obsidian hotkeys                          # list hotkey bindings
```

## Vault info

```sh
obsidian vault                            # vault name, path, file/folder counts, size
obsidian vault info=path                  # just the filesystem path
obsidian vaults verbose                   # list all known vaults with paths
```

## Developer commands

```sh
obsidian eval code="app.vault.getFiles().length"   # run JS in Obsidian
obsidian devtools                                   # toggle dev tools
obsidian dev:screenshot path=screenshot.png         # take screenshot
obsidian dev:console                                # show console messages
obsidian plugin:reload id=my-plugin                 # reload a plugin
```

## CLI vs. direct file writes

**Use the CLI** for: reading, searching, tasks, tags, properties, backlinks/links, and file operations that should update wikilinks (move/rename).

**Write directly to the filesystem** for: creating notes with substantial content. Get the vault path with `obsidian vault info=path`, then write markdown files there. Obsidian picks them up automatically.
