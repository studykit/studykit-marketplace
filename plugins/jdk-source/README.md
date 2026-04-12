# JDK Source Viewer Plugin

A plugin for viewing, searching, and understanding JDK internal source code during Java development and debugging.

## Components

| Type | Name | Purpose |
|------|------|---------|
| Agent | `jdk-explorer` | Isolated execution context for source lookup and analysis |
| Skill | `lookup` | Search JDK source and recommend what to read next |

## Features

- **JDK source exploration**: View Java standard library source code (for example `java.util.HashMap`, `java.lang.String`)
- **Code search**: Search within cached JDK sources for classes, methods, and patterns
- **Implementation explanations**: Explain how JDK classes work internally and point to the relevant code paths
- **Automatic caching**: Extracted sources are saved for reuse at `~/.cache/jdk-sources/`
- **GitHub fallback**: Falls back to OpenJDK on GitHub when a local source archive is unavailable
- **Symbol indexing**: Uses `universal-ctags` and `readtags` for fast symbol lookup

## Usage

### Skill: `lookup`

Use the `lookup` skill directly, or trigger it with questions about JDK internals.

Examples:

```text
How does HashMap work internally?
Show me the String source code from JDK
Why does ConcurrentHashMap not allow null keys?
```

The skill will:
1. Determine the JDK version from project build files first
2. Ensure source is cached at `~/.cache/jdk-sources/` (extract `src.zip` or use GitHub fallback)
3. Build a `ctags` index when needed
4. Search and analyze the relevant source code
5. Recommend which files and methods to read, in order

## Cache Structure

```text
~/.cache/jdk-sources/
├── zip/
│   └── jdk-21/
│       ├── tags
│       └── java.base/java/util/HashMap.java
└── git/
    ├── jdk.git/
    └── jdk-21/
        ├── tags
        └── src/java.base/share/classes/java/util/HashMap.java
```

## Requirements

- JDK installation with `src.zip` (recommended)
- Or internet access for GitHub OpenJDK fallback
- `universal-ctags` for symbol indexing
- `readtags` available from the same ctags installation

Example install on macOS:

```bash
brew install universal-ctags
```

## Related Files

- `plugins/jdk-source/agents/jdk-explorer.md`
- `plugins/jdk-source/skills/lookup/SKILL.md`
- `plugins/jdk-source/.codex-plugin/plugin.json`
