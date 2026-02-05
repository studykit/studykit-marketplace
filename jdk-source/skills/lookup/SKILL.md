---
description: Search JDK source code and recommend which code to read
context: fork
agent: jdk-explorer
allowed-tools: Bash(readtags *), Bash(ctags *), Read, Grep
---

## Task

$ARGUMENTS

## Steps

1. **Determine JDK version** → check project build files first; fall back to JAVA_HOME only with user confirmation
2. **Ensure cache exists** → extract src.zip or clone from GitHub if cache directory is missing
3. **Ensure ctags index exists** → check if `tags` file exists in cache directory; if not, generate it. **Mandatory** before using `readtags`.
4. **Locate source** → use `readtags` for symbol lookup (preferred), fall back to Grep for pattern searches
5. **Analyze** → read source, identify the relevant code paths for the user's question
6. **Recommend** → explain which files/methods to read and why, with a suggested reading order

## JDK Source Reference

### Source Locations

**Local JDK (Preferred):** `$JAVA_HOME/lib/src.zip`

Common JAVA_HOME locations:
- macOS (Homebrew): `/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home`
- macOS (Oracle): `/Library/Java/JavaVirtualMachines/jdk-21.jdk/Contents/Home`
- Linux: `/usr/lib/jvm/java-21-openjdk`

```bash
echo $JAVA_HOME
java -XshowSettings:properties -version 2>&1 | grep 'java.home'
/usr/libexec/java_home  # macOS
```

**GitHub OpenJDK (Fallback):**
```bash
git clone --bare https://github.com/openjdk/jdk.git ~/.cache/jdk-sources/git/jdk.git
git -C ~/.cache/jdk-sources/git/jdk.git worktree add ~/.cache/jdk-sources/git/jdk-21 jdk-21
```

### Module Mapping

| Package | Module |
|---------|--------|
| `java.lang.*`, `java.util.*`, `java.io.*` | `java.base` |
| `java.sql.*` | `java.sql` |
| `java.net.http.*` | `java.net.http` |
| `javax.swing.*` | `java.desktop` |

### Class Name to Path

```
java.util.HashMap → java/util/HashMap.java
java.util.HashMap.Node → java/util/HashMap.java (inner class)
```

### Extracting from src.zip

**IMPORTANT: Always extract the ENTIRE src.zip.**

```bash
mkdir -p ~/.cache/jdk-sources/zip/jdk-$VERSION
unzip -o "$JAVA_HOME/lib/src.zip" -d ~/.cache/jdk-sources/zip/jdk-$VERSION
```

### Detecting JDK Version

1. Check project build files (pom.xml `maven.compiler.source`, build.gradle `sourceCompatibility`) → use directly
2. If not found → `java -version` → **confirm with user**

### Cache Structure

```
~/.cache/jdk-sources/
├── zip/jdk-21/
│   ├── tags
│   └── java.base/java/util/HashMap.java
└── git/
    ├── jdk.git/
    └── jdk-21/tags, src/java.base/share/classes/...
```

### ctags Indexing

Prerequisite: `universal-ctags` (`brew install universal-ctags`)

```bash
# zip source
ctags -R --languages=Java -f ~/.cache/jdk-sources/zip/jdk-$VERSION/tags ~/.cache/jdk-sources/zip/jdk-$VERSION/

# git source
ctags -R --languages=Java,C,C++ -f ~/.cache/jdk-sources/git/jdk-$VERSION/tags ~/.cache/jdk-sources/git/jdk-$VERSION/src/
```

### Searching with readtags

```bash
readtags -t ~/.cache/jdk-sources/zip/jdk-$VERSION/tags HashMap
readtags -t ~/.cache/jdk-sources/zip/jdk-$VERSION/tags -Q '(eq? $kind "method")' -l
readtags -t ~/.cache/jdk-sources/zip/jdk-$VERSION/tags -p put
```

Tag kinds: `c` (class), `i` (interface), `m` (method), `f` (field), `e` (enum constant), `g` (enum type)

### Native Code (Git only)

| Location | Description |
|----------|-------------|
| `src/hotspot/share/` | HotSpot VM shared code |
| `src/hotspot/share/gc/` | Garbage collector implementations |
| `src/java.base/share/native/libjava/` | Native library code |
