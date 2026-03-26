# Obsidian CLI Command Reference

Complete reference for all Obsidian CLI commands. Requires Obsidian 1.12.4+ with CLI registered.

## Conventions

- **Parameters**: `key=value` (quote values with spaces)
- **Flags**: Boolean switches, included without values
- **(required)**: Parameter must be provided
- `file=<name>` resolves by filename (wikilink-style); `path=<path>` uses exact vault-root path
- `vault=<name>` must be the first parameter when targeting a specific vault

---

## General

| Command | Parameters | Description |
|---------|------------|-------------|
| `help [command]` | — | List all commands or show help for a specific command |
| `version` | — | Display Obsidian version |
| `reload` | — | Reload the app window |
| `restart` | — | Restart the application |

## Daily Notes

| Command | Parameters | Description |
|---------|------------|-------------|
| `daily` | `paneType=tab\|split\|window` | Open today's daily note |
| `daily:path` | — | Print the daily note file path |
| `daily:read` | — | Print the daily note content |
| `daily:append` | `content=<text>` **(required)**; `paneType`; `inline`; `open` | Append content to the daily note |
| `daily:prepend` | `content=<text>` **(required)**; `paneType`; `inline`; `open` | Prepend content to the daily note |

- `inline` flag inserts content without a leading newline separator.
- `open` flag opens the note after writing.

## Files and Folders

| Command | Parameters | Description |
|---------|------------|-------------|
| `file` | `file=<name>` \| `path=<path>` | Show file info |
| `files` | `folder=<path>`; `ext=<extension>`; `total` | List files in vault or folder |
| `folder` | `path=<path>` **(required)**; `info=files\|folders\|size` | Show folder info |
| `folders` | `folder=<path>`; `total` | List folders |
| `open` | `file=<name>` \| `path=<path>`; `newtab` | Open a note in Obsidian |
| `create` | `name=<name>`; `path=<path>`; `content=<text>`; `template=<name>`; `overwrite`; `open`; `newtab` | Create a new note |
| `read` | `file=<name>` \| `path=<path>` | Print note content to stdout |
| `append` | `file=<name>` \| `path=<path>`; `content=<text>` **(required)**; `inline` | Append content to a note |
| `prepend` | `file=<name>` \| `path=<path>`; `content=<text>` **(required)**; `inline` | Prepend content to a note |
| `move` | `file=<name>` \| `path=<path>`; `to=<path>` **(required)** | Move a note to a new location |
| `rename` | `file=<name>` \| `path=<path>`; `name=<name>` **(required)** | Rename a note |
| `delete` | `file=<name>` \| `path=<path>`; `permanent` | Delete a note (trash by default) |

- `create` with `template=` applies the named template. Add `overwrite` to replace existing files.
- `inline` flag on `append`/`prepend` skips the leading newline separator.

## Search

| Command | Parameters | Description |
|---------|------------|-------------|
| `search` | `query=<text>` **(required)**; `path=<folder>`; `limit=<n>`; `format=text\|json`; `total`; `case` | Search vault content |
| `search:context` | `query=<text>` **(required)**; `path=<folder>`; `limit=<n>`; `format=text\|json`; `case` | Search with surrounding context |
| `search:open` | `query=<text>` | Open Obsidian search UI with query |

- `case` flag enables case-sensitive matching.
- `path=` restricts search to a specific folder.

## Tasks

| Command | Parameters | Description |
|---------|------------|-------------|
| `tasks` | `file=<name>` \| `path=<path>`; `status="<char>"`; `total`; `done`; `todo`; `verbose`; `format=json\|tsv\|csv`; `active`; `daily` | List tasks |
| `task` | `ref=<path:line>` \| (`file=<name>` \| `path=<path>` + `line=<n>`); `status="<char>"`; `toggle`; `daily`; `done`; `todo` | Get or modify a single task |

- `done` / `todo` filters by completion status.
- `active` filters to the currently active file.
- `daily` targets the daily note.
- `toggle` flips the task's completion state.
- `status="<char>"` sets a custom status character (e.g., `status="/"` for in-progress).

## Tags

| Command | Parameters | Description |
|---------|------------|-------------|
| `tags` | `file=<name>` \| `path=<path>`; `sort=count`; `total`; `counts`; `format=json\|tsv\|csv`; `active` | List all tags |
| `tag` | `name=<tag>` **(required)**; `total`; `verbose` | Show notes with a specific tag |

- `counts` includes usage count per tag.
- `sort=count` orders by frequency.

## Links

| Command | Parameters | Description |
|---------|------------|-------------|
| `backlinks` | `file=<name>` \| `path=<path>`; `counts`; `total`; `format=json\|tsv\|csv` | List pages linking to this note |
| `links` | `file=<name>` \| `path=<path>`; `total` | List outgoing links from a note |
| `unresolved` | `total`; `counts`; `verbose`; `format=json\|tsv\|csv` | List unresolved (broken) links |
| `orphans` | `total` | List notes with no incoming or outgoing links |
| `deadends` | `total` | List notes with no outgoing links |

## Properties (Frontmatter)

| Command | Parameters | Description |
|---------|------------|-------------|
| `aliases` | `file=<name>` \| `path=<path>`; `total`; `verbose`; `active` | List note aliases |
| `properties` | `file=<name>` \| `path=<path>`; `name=<name>`; `sort=count`; `format=yaml\|json\|tsv`; `total`; `counts`; `active` | List properties across vault or for a note |
| `property:set` | `name=<name>` **(required)**; `value=<value>` **(required)**; `type=text\|list\|number\|checkbox\|date\|datetime`; `file=<name>` \| `path=<path>` | Set a frontmatter property |
| `property:remove` | `name=<name>` **(required)**; `file=<name>` \| `path=<path>` | Remove a frontmatter property |
| `property:read` | `name=<name>` **(required)**; `file=<name>` \| `path=<path>` | Read a property value |

- `type=` on `property:set` specifies the YAML type. Defaults to `text`.
- Without `file=`/`path=`, `properties` lists all properties across the vault.

## Outline

| Command | Parameters | Description |
|---------|------------|-------------|
| `outline` | `file=<name>` \| `path=<path>`; `format=tree\|md\|json`; `total` | Show heading outline of a note |

## File History and Sync

### Local History

| Command | Parameters | Description |
|---------|------------|-------------|
| `diff` | `file=<name>` \| `path=<path>`; `from=<n>`; `to=<n>`; `filter=local\|sync` | Show diff between versions |
| `history` | `file=<name>` \| `path=<path>` | Show file history summary |
| `history:list` | — | List files with local history |
| `history:read` | `file=<name>` \| `path=<path>`; `version=<n>` | Read a specific version |
| `history:restore` | `file=<name>` \| `path=<path>`; `version=<n>` **(required)** | Restore a specific version |
| `history:open` | `file=<name>` \| `path=<path>` | Open history view in Obsidian |

### Obsidian Sync

| Command | Parameters | Description |
|---------|------------|-------------|
| `sync` | `on` \| `off` | Enable or disable sync |
| `sync:status` | — | Show sync status |
| `sync:history` | `file=<name>` \| `path=<path>`; `total` | Show sync history for a file |
| `sync:read` | `file=<name>` \| `path=<path>`; `version=<n>` **(required)** | Read a synced version |
| `sync:restore` | `file=<name>` \| `path=<path>`; `version=<n>` **(required)** | Restore a synced version |
| `sync:open` | `file=<name>` \| `path=<path>` | Open sync history in Obsidian |
| `sync:deleted` | `total` | List files deleted via sync |

## Plugins

| Command | Parameters | Description |
|---------|------------|-------------|
| `plugins` | `filter=core\|community`; `versions`; `format=json\|tsv\|csv` | List all plugins |
| `plugins:enabled` | `filter=core\|community`; `versions`; `format=json\|tsv\|csv` | List enabled plugins |
| `plugins:restrict` | `on` \| `off` | Toggle restricted mode |
| `plugin` | `id=<plugin-id>` **(required)** | Show plugin info |
| `plugin:enable` | `id=<id>` **(required)**; `filter=core\|community` | Enable a plugin |
| `plugin:disable` | `id=<id>` **(required)**; `filter=core\|community` | Disable a plugin |
| `plugin:install` | `id=<id>` **(required)**; `enable` | Install a community plugin |
| `plugin:uninstall` | `id=<id>` **(required)** | Uninstall a plugin |
| `plugin:reload` | `id=<id>` **(required)** | Reload a plugin (dev use) |

## Themes and Snippets

| Command | Parameters | Description |
|---------|------------|-------------|
| `themes` | `versions` | List installed themes |
| `theme` | `name=<name>` | Show theme info |
| `theme:set` | `name=<name>` **(required)** | Set active theme |
| `theme:install` | `name=<name>` **(required)**; `enable` | Install a theme |
| `theme:uninstall` | `name=<name>` **(required)** | Uninstall a theme |
| `snippets` | — | List CSS snippets |
| `snippets:enabled` | — | List enabled snippets |
| `snippet:enable` | `name=<name>` **(required)** | Enable a CSS snippet |
| `snippet:disable` | `name=<name>` **(required)** | Disable a CSS snippet |

## Templates

| Command | Parameters | Description |
|---------|------------|-------------|
| `templates` | `total` | List available templates |
| `template:read` | `name=<template>` **(required)**; `title=<title>`; `resolve` | Read a template's content |
| `template:insert` | `name=<template>` **(required)** | Insert template into active note |

- `resolve` flag processes template variables (e.g., `{{date}}`, `{{title}}`).
- `title=` sets the title variable for template resolution.

## Bookmarks

| Command | Parameters | Description |
|---------|------------|-------------|
| `bookmarks` | `total`; `verbose`; `format=json\|tsv\|csv` | List bookmarks |
| `bookmark` | `file=<path>` \| `subpath=<subpath>` \| `folder=<path>` \| `search=<query>` \| `url=<url>`; `title=<title>` | Create a bookmark |

## Bases

| Command | Parameters | Description |
|---------|------------|-------------|
| `bases` | — | List bases |
| `base:views` | — | List base views |
| `base:create` | `file=<name>` \| `path=<path>`; `view=<name>`; `name=<name>`; `content=<text>`; `open`; `newtab` | Create a base entry |
| `base:query` | `file=<name>` \| `path=<path>`; `view=<name>`; `format=json\|csv\|tsv\|md\|paths` | Query a base |

## Command Palette and Hotkeys

| Command | Parameters | Description |
|---------|------------|-------------|
| `commands` | `filter=<prefix>` | List available commands |
| `command` | `id=<command-id>` **(required)** | Execute a command by ID |
| `hotkeys` | `total`; `verbose`; `format=json\|tsv\|csv` | List hotkey bindings |
| `hotkey` | `id=<command-id>` **(required)**; `verbose` | Show hotkey for a command |

## Publish

Requires an active Obsidian Publish subscription.

| Command | Parameters | Description |
|---------|------------|-------------|
| `publish:site` | — | Show publish site info |
| `publish:list` | `total` | List published files |
| `publish:status` | `total`; `new`; `changed`; `deleted` | Show publish status |
| `publish:add` | `file=<name>` \| `path=<path>`; `changed` | Add file to publish |
| `publish:remove` | `file=<name>` \| `path=<path>` | Remove file from publish |
| `publish:open` | `file=<name>` \| `path=<path>` | Open published page |

## Random and Unique Notes

| Command | Parameters | Description |
|---------|------------|-------------|
| `random` | `folder=<path>`; `newtab` | Open a random note |
| `random:read` | `folder=<path>` | Print a random note's content |
| `unique` | `name=<text>`; `content=<text>`; `paneType=tab\|split\|window`; `open` | Create a unique (Zettelkasten) note |

## Vault Management

| Command | Parameters | Description |
|---------|------------|-------------|
| `vault` | `info=name\|path\|files\|folders\|size` | Show vault info |
| `vaults` | `total`; `verbose` | List registered vaults |

## Workspace

| Command | Parameters | Description |
|---------|------------|-------------|
| `workspace` | `ids` | Show current workspace |
| `workspaces` | `total` | List saved workspaces |
| `workspace:save` | `name=<name>` | Save current workspace |
| `workspace:load` | `name=<name>` **(required)** | Load a workspace |
| `workspace:delete` | `name=<name>` **(required)** | Delete a workspace |
| `tabs` | `ids` | List open tabs |
| `tab:open` | `group=<id>`; `file=<path>`; `view=<type>` | Open a tab |
| `recents` | `total` | List recently opened files |

## Web Viewer

| Command | Parameters | Description |
|---------|------------|-------------|
| `web` | `url=<url>` **(required)**; `newtab` | Open a URL in Obsidian's web viewer |

## Word Count

| Command | Parameters | Description |
|---------|------------|-------------|
| `wordcount` | `file=<name>` \| `path=<path>`; `words`; `characters` | Show word/character count |

## Developer Commands

| Command | Parameters | Description |
|---------|------------|-------------|
| `devtools` | — | Open developer tools |
| `dev:debug` | `on` \| `off` | Toggle debug mode |
| `dev:cdp` | `method=<CDP.method>` **(required)**; `params=<json>` | Execute Chrome DevTools Protocol method |
| `dev:errors` | `clear` | Show or clear error log |
| `dev:screenshot` | `path=<filename>` | Take a screenshot |
| `dev:console` | `limit=<n>`; `level=log\|warn\|error\|info\|debug`; `clear` | Read or clear console output |
| `dev:css` | `selector=<css>` **(required)**; `prop=<name>` | Inspect CSS for an element |
| `dev:dom` | `selector=<css>` **(required)**; `attr=<name>`; `css=<prop>`; `total`; `text`; `inner`; `all` | Inspect DOM elements |
| `dev:mobile` | `on` \| `off` | Toggle mobile emulation |
| `eval` | `code=<javascript>` **(required)** | Execute JavaScript in the Obsidian context |

## Global Flags

These flags work with most commands that produce output:

| Flag | Description |
|------|-------------|
| `--copy` | Copy output to system clipboard |
| `total` | Show only the count of results |
| `verbose` | Show additional detail |
| `format=json\|tsv\|csv` | Output in structured format (command-dependent) |
