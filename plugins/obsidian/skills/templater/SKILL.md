---
name: templater
description: >-
  This skill should be used when the user asks to "create a Templater template",
  "modify a Templater template", "fix my Templater template", "add a prompt to my template",
  "debug Templater syntax", "write a daily note template", "make a meeting note template",
  or mentions Obsidian Templater command syntax, tp.* API, or template patterns.
argument-hint: <what to create or modify, e.g. "create a daily note template with mood tracking", "add a date picker to my daily note template", "fix the frontmatter update logic">
---

# Templater Skill

Create, understand, and modify Templater templates in Obsidian vaults. Templater uses a command syntax (`<% %>`) with a `tp.*` API to dynamically generate note content.

## Command Syntax Quick Reference

| Syntax | Name | Purpose | Output? |
|--------|------|---------|---------|
| `<% expr %>` | Interpolation | Evaluate expression and insert result | Yes |
| `<%* code %>` | Execution | Run JavaScript silently | No (use `tR +=` to output) |
| `<%+ expr %>` | Dynamic | Re-evaluate on each preview open | Yes (deprecated — prefer Dataview) |

### Whitespace Control

| Modifier | Effect |
|----------|--------|
| `<%-` | Trim one newline before |
| `-%>` | Trim one newline after |
| `<%_` | Trim all whitespace before |
| `_%>` | Trim all whitespace after |

### Key Variables

- **`tR`** — The accumulated template result string. Use `tR += "text"` in execution commands to append output. `tR = ""` resets all prior output.

## Template Creation Workflow

Follow these steps when creating a new template from scratch.

### Step 1: Gather Requirements

Clarify the template's purpose and needs:

| Question | Purpose |
|----------|---------|
| What type of note is this for? | Determines structure (daily, meeting, project, etc.) |
| What information should be captured? | Defines frontmatter fields and sections |
| Should anything be prompted at creation time? | Decides `tp.system.prompt()` / `tp.system.suggester()` usage |
| Where should the template file live? | Vault path for writing the file |
| Any naming convention for generated notes? | Determines if `tp.file.rename()` or `tp.file.move()` is needed |

Skip questions already clear from the request.

### Step 2: Select Patterns

Select building blocks from `references/patterns.md` based on requirements:

| Need | Pattern |
|------|---------|
| Select from options | `tp.system.suggester()` |
| Free text input | `tp.system.prompt()` |
| Date-based navigation | Date offset links `[[<% tp.date.now("YYYY-MM-DD", ±N) %>]]` |
| Auto-set frontmatter | `tp.hooks.on_all_templates_executed()` + `processFrontMatter()` |
| Create related files | `tp.file.create_new()` loop |
| Conditional sections | `<%* if -%>` execution blocks |
| Dynamic lists | `tR +=` in loops |

### Step 3: Build and Write

1. Compose the template combining selected patterns
2. Validate against `references/modules.md` for correct API signatures
3. Write the template file directly to the vault using the Write tool

### Step 4: Test the Template

Test using the Obsidian CLI:

```bash
# 1. Create a test note using the template
obsidian create name="test-templater-output" template="TemplateName"

# 2. Read the result to verify output
obsidian read file="test-templater-output"

# 3. Clean up the test note
obsidian delete file="test-templater-output"
```

**CLI testing limitations:**
- `tp.system.prompt()` and `tp.system.suggester()` require the Obsidian UI — they do not work via CLI. For templates with interactive prompts, instruct the user to test manually: create a new note in Obsidian and run **Templater: Insert Template** from the command palette.
- `tp.file.cursor()` positions are only meaningful in the editor — skip cursor verification in CLI tests.

**Testing checklist:**
- [ ] Frontmatter fields correctly populated
- [ ] Date values render with expected format
- [ ] Conditional sections appear/hide as intended
- [ ] File naming/moving works correctly
- [ ] No syntax errors or blank lines from untrimmed whitespace

If CLI test reveals issues, fix the template and re-test. For interactive templates, present the expected output as a code block so the user knows what to verify in Obsidian.

---

## Template Modification Workflow

Follow these steps when modifying an existing template.

### Step 1: Analyze the Existing Template

Read the template file and identify:
- Which `tp.*` modules are used (date, file, system, frontmatter, etc.)
- Control flow patterns (conditionals, loops)
- User interaction points (prompts, suggesters)
- Frontmatter manipulation hooks
- Cursor placement positions

### Step 2: Classify the Modification Intent

| Intent | Approach |
|--------|----------|
| Add new dynamic field | Insert `<% %>` interpolation with appropriate `tp.*` call |
| Add user input | Use `tp.system.prompt()` or `tp.system.suggester()` with `await` |
| Add conditional logic | Use `<%* if/else %>` execution blocks with `-%>` whitespace trimming |
| Modify frontmatter | Use `tp.hooks.on_all_templates_executed()` + `processFrontMatter()` |
| Fix broken template | Check syntax, missing `await`, unmatched brackets, wrong API signatures |
| Add file operations | Use `tp.file.create_new()`, `tp.file.move()`, `tp.file.rename()` |

### Step 3: Build the Modification

Consult `references/modules.md` for exact function signatures and parameters. Apply these rules:

1. **Always `await` async functions** — `tp.system.prompt()`, `tp.system.suggester()`, `tp.web.request()`, `tp.file.create_new()` all require `await`.
2. **Use execution blocks for setup** — Capture variables with `<%* let x = await ... %>`, then reference with `<% x %>`.
3. **Trim whitespace around control flow** — Use `-%>` after opening `<%* if -%>` and `<%* } -%>` to avoid blank lines.
4. **Frontmatter updates run in hooks** — Direct `tp.frontmatter` is read-only. To write, use `tp.hooks.on_all_templates_executed()`.
5. **Cursor placement is ordered** — `tp.file.cursor(1)` jumps first, `tp.file.cursor(2)` second. Same number = multi-cursor.

### Step 4: Validate and Present

Before presenting the modified template:
- Verify all `tp.*` function signatures match `references/modules.md`
- Check that `await` is used where needed
- Ensure whitespace trimming produces clean output
- Confirm variable scoping (variables declared in `<%* %>` are available in subsequent commands)

## Output Format

When presenting a created or modified template:

````markdown
```markdown
(full template content)
```

**Changes made:**
- (bullet list of what was created/changed and why)

**Notes:**
- (any caveats, e.g. required settings, plugin dependencies)
````

## Additional Resources

### Reference Files

- **`references/modules.md`** — Complete `tp.*` API reference covering all internal modules (tp.date, tp.file, tp.system, tp.frontmatter, tp.hooks, tp.obsidian, tp.web, tp.config) and user functions (tp.user) with signatures, parameters, and examples
- **`references/patterns.md`** — Practical template examples organized by use case (daily notes, meeting notes, project templates, book notes, weekly reviews, etc.) with explanations of techniques used
