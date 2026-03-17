# JDK Source Viewer Plugin

A Claude Code plugin for viewing, searching, and understanding JDK internal source code during Java development and debugging.

## Features

- **JDK source exploration**: View Java standard library source code (e.g., `java.util.HashMap`, `java.lang.String`)
- **Code search**: Search within JDK sources for patterns, methods, or keywords
- **Implementation explanations**: Get detailed explanations of how JDK classes work internally
- **Automatic caching**: Extracted sources saved for reuse across sessions at `~/.cache/jdk-sources/`
- **GitHub fallback**: Access OpenJDK source when local installation unavailable

## Installation

Add this plugin to your Claude Code configuration.

## Usage

### Skill: `/lookup` (Auto or Manual)

The **lookup** skill searches JDK source and recommends which code to read. It runs in an isolated context using the **jdk-explorer** agent as execution environment (`context: fork` + `agent` pattern).

**Invoke manually:**
```
/lookup How does HashMap work internally?
/lookup Show me the String source code from JDK
/lookup Why does ConcurrentHashMap not allow null keys?
```

**Or let Claude trigger it automatically** when you ask about JDK internals:
```
"I'm getting a ConcurrentModificationException from ArrayList, what's happening?"
"What's the difference between HashMap and LinkedHashMap internally?"
```

The skill will:
1. Determine the JDK version from your project
2. Ensure source is cached at `~/.cache/jdk-sources/` (extract src.zip or clone from GitHub)
3. Build ctags index for fast symbol lookup
4. Search and analyze the relevant source code
5. Recommend which files/methods to read and why

## Cache Structure

```
~/.cache/jdk-sources/
├── zip/                          # From local src.zip
│   └── jdk-21/
│       ├── tags                  # ctags index
│       └── java.base/java/util/HashMap.java
└── git/                          # From GitHub OpenJDK
    ├── jdk.git/                  # Bare repository
    └── jdk-21/
        ├── tags                  # ctags index
        └── src/java.base/share/classes/java/util/HashMap.java
```

## Requirements

- JDK installation with `src.zip` (recommended)
- Or internet access for GitHub OpenJDK fallback
- `universal-ctags` for symbol indexing (`brew install universal-ctags`)
