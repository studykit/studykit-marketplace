# JDK Source Viewer Plugin

A Claude Code plugin for viewing, searching, and understanding JDK internal source code during Java development and debugging.

## Features

- **JDK source exploration**: View Java standard library source code (e.g., `java.util.HashMap`, `java.lang.String`)
- **Code search**: Search within JDK sources for patterns, methods, or keywords
- **Implementation explanations**: Get detailed explanations of how JDK classes work internally
- **Automatic caching**: Extracted sources saved for reuse across sessions
- **LSP integration**: Enhanced navigation with jdtls when available
- **GitHub fallback**: Access OpenJDK source when local installation unavailable

## Installation

Add this plugin to your Claude Code configuration.

## Usage

### Agent (Auto-triggered)

The **jdk-explorer** agent automatically activates when you ask about JDK internals:

```
"How does HashMap work internally?"
"Show me the String source code from JDK"
"Find where synchronized is used in ConcurrentHashMap"
"What's the difference between HashMap and LinkedHashMap internally?"
"I'm getting a ConcurrentModificationException from ArrayList, what's happening?"
```

The agent will:
1. Locate or cache the JDK source
2. Read the relevant source files
3. Search for specific patterns if requested
4. Explain the implementation details

### Skill (Reference)

The plugin also provides the **jdk-source-lookup** skill with reference information about source locations and caching strategies.

## Configuration

Create `~/.claude/jdk-source.local.md` to customize settings:

```yaml
---
jdk_source_path: /path/to/jdk/lib/src.zip
jdk_cache_path: ~/my-jdk-sources   # Custom cache location (default: ~/.cache/jdk-sources)
use_github_fallback: true
use_jdtls: true
---
```

### Settings

| Field | Description | Default |
|-------|-------------|---------|
| `jdk_source_path` | Path to JDK src.zip file | Auto-detect from JAVA_HOME |
| `jdk_cache_path` | Directory to cache extracted sources | `~/.cache/jdk-sources` |
| `use_github_fallback` | Use GitHub OpenJDK when local unavailable | `true` |
| `use_jdtls` | Enable LSP features when jdtls is available | `true` |

### Cache Structure

Extracted sources are cached for reuse. Location is configured by `jdk_cache_path` (default: `~/.cache/jdk-sources`):

```
$jdk_cache_path/
├── zip/                          # From local src.zip
│   └── jdk-21/
│       ├── java.base/
│       │   └── java/util/HashMap.java
│       ├── java.sql/
│       └── java.desktop/
└── git/                          # From GitHub OpenJDK
    ├── jdk.git/                  # Bare repository
    └── jdk-21/                   # Worktree
        └── src/
            ├── java.base/share/classes/
            └── hotspot/          # VM source (C/C++)
```

## Requirements

- JDK installation with `src.zip` (recommended)
- Or internet access for GitHub OpenJDK fallback

## LSP Integration (Optional)

When Eclipse JDT Language Server (jdtls) is installed, the agent can leverage enhanced Java navigation:

- **Go to definition**: Navigate directly to JDK source code
- **Find references**: Find all usages of a method or class
- **Hover information**: View method signatures and Javadoc

### Installing jdtls

```bash
# macOS (Homebrew)
brew install jdtls

# Linux (Arch-based)
yay -S jdtls
```

### Prerequisites for LSP

- **Java 17+** (JDK, not just JRE)
- **jdtls** binary in PATH
- **JDK with src.zip** for source attachment
