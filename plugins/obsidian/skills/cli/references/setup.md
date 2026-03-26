# Obsidian CLI Setup and TUI Reference

## Requirements

- Obsidian 1.12.4+ (installer version)
- Obsidian application must be running for CLI commands to execute
- CLI registration: Settings > General > "Command line interface"

## Platform-Specific Installation

### macOS

CLI registration modifies `~/.zprofile` to add the Obsidian CLI to PATH. For alternate shells, add the path manually:

- **Bash**: Add to `~/.bash_profile` or `~/.bashrc`
- **Fish**: Add to `~/.config/fish/config.fish`

### Windows

Requires the Obsidian 1.12.4+ installer (not portable). A terminal redirector `Obsidian.com` is added automatically to the system PATH.

### Linux

Creates a symlink at `/usr/local/bin/obsidian`.

**AppImage users**: May need to create the symlink manually:
```bash
ln -s /path/to/Obsidian.AppImage /usr/local/bin/obsidian
```

**Snap users**: May need to set `XDG_CONFIG_HOME` if the default config path is not accessible.

**Flatpak users**: Create a symlink to `.local/bin/obsidian`:
```bash
ln -s /path/to/flatpak/obsidian ~/.local/bin/obsidian
```

## TUI Keyboard Shortcuts

The Obsidian CLI includes a Terminal User Interface (TUI) with interactive features.

### Navigation

| Shortcut | Action |
|----------|--------|
| `←` / `Ctrl+B` | Move cursor left |
| `→` / `Ctrl+F` | Move cursor right (accepts suggestion at line end) |
| `Ctrl+A` | Jump to start of line |
| `Ctrl+E` | Jump to end of line |
| `Alt+B` | Move back one word |
| `Alt+F` | Move forward one word |

### Editing

| Shortcut | Action |
|----------|--------|
| `Ctrl+U` | Delete to start of line |
| `Ctrl+K` | Delete to end of line |
| `Ctrl+W` / `Alt+Backspace` | Delete previous word |

### Autocomplete

| Shortcut | Action |
|----------|--------|
| `Tab` | Enter suggestion mode or accept selected |
| `Shift+Tab` | Exit suggestion mode |
| `↓` | Enter suggestion mode (from fresh input) |
| `→` | Accept first/selected suggestion (at line end) |

### History

| Shortcut | Action |
|----------|--------|
| `↑` / `Ctrl+P` | Previous history entry |
| `↓` / `Ctrl+N` | Next history entry |
| `Ctrl+R` | Reverse history search |

### General

| Shortcut | Action |
|----------|--------|
| `Enter` | Execute command or accept suggestion |
| `Escape` | Undo autocomplete / exit suggestion / clear input |
| `Ctrl+L` | Clear screen |
| `Ctrl+C` / `Ctrl+D` | Exit TUI |
