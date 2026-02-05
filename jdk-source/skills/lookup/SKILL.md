---
name: lookup
description: This skill should be used when the user asks to "view JDK source", "show JDK internal code", "see OpenJDK implementation", "look at Java standard library source", "how does HashMap work internally", "show me String source code", "what's inside ArrayList", "show JDK internals", or needs to examine Java standard library internals for debugging or learning.
disable-model-invocation: true
version: 0.1.0
---

# JDK Source Lookup

Reference information for locating JDK standard library source code. This skill is preloaded by the `jdk-explorer` agent.

## Overview

When analyzing Java code, developers often need to examine JDK internal implementations to understand behavior, debug issues, or learn patterns. This skill provides reference information for source locations and caching.

## Source Locations

### Local JDK Installation (Preferred)

Most JDK installations include source code in `lib/src.zip`:

```
$JAVA_HOME/lib/src.zip
```

**Common JAVA_HOME locations:**
- macOS (Homebrew): `/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home`
- macOS (Oracle): `/Library/Java/JavaVirtualMachines/jdk-21.jdk/Contents/Home`
- Linux: `/usr/lib/jvm/java-21-openjdk`
- Windows: `C:\Program Files\Java\jdk-21`

**To find JAVA_HOME:**
```bash
# Check environment variable
echo $JAVA_HOME

# Or use java command
java -XshowSettings:properties -version 2>&1 | grep 'java.home'

# macOS specific
/usr/libexec/java_home
```

### GitHub OpenJDK (Fallback)

When local source is unavailable, clone from GitHub using bare clone + worktree.

**Setup bare clone (one-time):**
```bash
git clone --bare https://github.com/openjdk/jdk.git ~/.cache/jdk-sources/git/jdk.git
```

**Create worktree for specific version:**
```bash
git -C ~/.cache/jdk-sources/git/jdk.git worktree add ~/.cache/jdk-sources/git/jdk-21 jdk-21
```

**File path in git worktree:**
```
~/.cache/jdk-sources/git/jdk-21/src/java.base/share/classes/java/util/HashMap.java
```

**Module mapping for common packages:**
| Package | Module |
|---------|--------|
| `java.lang.*`, `java.util.*`, `java.io.*` | `java.base` |
| `java.sql.*` | `java.sql` |
| `java.net.http.*` | `java.net.http` |
| `javax.swing.*` | `java.desktop` |

### Native Code (Git only)

Git source includes C/C++ native implementations:

| Location | Description |
|----------|-------------|
| `src/hotspot/share/` | HotSpot VM shared code |
| `src/hotspot/cpu/{arch}/` | CPU-specific VM code |
| `src/hotspot/os/{os}/` | OS-specific VM code |
| `src/{module}/share/native/` | Native library code |
| `src/{module}/{os}/native/` | OS-specific native code |

**Examples:**
- `src/hotspot/share/gc/` - Garbage collector implementations
- `src/java.base/share/native/libjava/String.c` - Native String methods
- `src/java.base/unix/native/libjava/` - Unix-specific Java native code

## Converting Class Name to Path

Transform fully-qualified class name to file path:

```
java.util.HashMap → java/util/HashMap.java
java.util.concurrent.ConcurrentHashMap → java/util/concurrent/ConcurrentHashMap.java
java.lang.String → java/lang/String.java
```

**For inner classes:**
```
java.util.HashMap.Node → java/util/HashMap.java (inner class in same file)
```

## Extracting from src.zip

**IMPORTANT: Always extract the ENTIRE src.zip. Do NOT extract individual files.**

```bash
# ALWAYS extract ALL sources at once
mkdir -p ~/.cache/jdk-sources/zip/jdk-$VERSION
unzip -o "$JAVA_HOME/lib/src.zip" -d ~/.cache/jdk-sources/zip/jdk-$VERSION
```

**src.zip structure:**
```
java.base/
  java/
    lang/
      String.java
      Object.java
    util/
      HashMap.java
      ArrayList.java
```

## Detecting JDK Version

**Priority:**
1. Check project build files → use directly
2. If not found → estimate from JAVA_HOME (`java -version`) → **confirm with user**

**Maven (pom.xml):**
```xml
<properties>
  <maven.compiler.source>21</maven.compiler.source>
  <maven.compiler.target>21</maven.compiler.target>
</properties>
```

**Gradle (build.gradle):**
```groovy
java {
  sourceCompatibility = JavaVersion.VERSION_21
}
```

**Gradle Kotlin DSL (build.gradle.kts):**
```kotlin
java {
  sourceCompatibility = JavaVersion.VERSION_21
}
```

## Cache Location

All JDK sources are cached at: `~/.cache/jdk-sources/`

### Cache Directory Structure

```
~/.cache/jdk-sources/
├── zip/                          # From local src.zip
│   ├── jdk-21/
│   │   ├── tags                  # ctags index
│   │   ├── java.base/
│   │   │   └── java/util/HashMap.java
│   │   ├── java.sql/
│   │   └── java.desktop/
│   └── jdk-17/
│       ├── tags
│       └── ...
└── git/                          # From GitHub OpenJDK
    ├── jdk.git/                  # Bare repository (shared)
    ├── jdk-21/                   # Worktree for JDK 21
    │   ├── tags                  # ctags index
    │   └── src/
    │       ├── java.base/
    │       │   ├── share/classes/java/util/HashMap.java
    │       │   └── share/native/libjava/
    │       ├── hotspot/          # VM source (C/C++)
    │       └── ...
    └── jdk-17/                   # Worktree for JDK 17
        ├── tags
        └── ...
```

**Benefits:**
- **zip/**: Java source only, fast extraction from local JDK
- **git/**: Full source including native C/C++ code, efficient with bare clone + worktrees
- Clear separation between sources
- Multiple JDK versions supported simultaneously

## ctags Indexing

After extracting or cloning JDK source, generate a ctags index for fast symbol lookup. The `tags` file is created once per JDK version directory.

**Prerequisite:** `universal-ctags` must be installed (`brew install universal-ctags`).

### Generating tags

```bash
# For zip source (Java only)
ctags -R --languages=Java -f ~/.cache/jdk-sources/zip/jdk-$VERSION/tags ~/.cache/jdk-sources/zip/jdk-$VERSION/

# For git source (Java + C/C++)
ctags -R --languages=Java,C,C++ -f ~/.cache/jdk-sources/git/jdk-$VERSION/tags ~/.cache/jdk-sources/git/jdk-$VERSION/src/
```

### Searching with readtags

```bash
# Find a class or method definition
readtags -t ~/.cache/jdk-sources/zip/jdk-$VERSION/tags HashMap

# Filter by kind (class, method, field, etc.)
readtags -t ~/.cache/jdk-sources/zip/jdk-$VERSION/tags -Q '(eq? $kind "method")' -l

# Prefix search
readtags -t ~/.cache/jdk-sources/zip/jdk-$VERSION/tags -p put
```

**Tag kinds for Java:**
| Kind | Description |
|------|-------------|
| `c`  | class       |
| `i`  | interface   |
| `m`  | method      |
| `f`  | field       |
| `e`  | enum constant |
| `g`  | enum type   |

### When to regenerate tags

- After extracting a new JDK version
- After cloning/updating a git worktree
- If the `tags` file is missing or corrupted

## Common Classes

Frequently requested JDK classes:

| Class | Path |
|-------|------|
| `java.util.HashMap` | `java/util/HashMap.java` |
| `java.util.ArrayList` | `java/util/ArrayList.java` |
| `java.lang.String` | `java/lang/String.java` |
| `java.util.concurrent.ConcurrentHashMap` | `java/util/concurrent/ConcurrentHashMap.java` |
| `java.lang.Thread` | `java/lang/Thread.java` |
| `java.util.stream.Stream` | `java/util/stream/Stream.java` |

## Tips

- JDK source includes extensive Javadoc comments explaining implementation details
- For debugging, focus on the specific method mentioned in stack traces
