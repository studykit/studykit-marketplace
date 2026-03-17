---
name: kosis-discovery
description: This skill should be used when users want to explore, browse, or discover what Korean national statistics are available in KOSIS (kosis.kr). Common triggers include "what Korean economic data is available", "show me KOSIS statistics about employment", "browse KOSIS data categories", "what statistics does Statistics Korea publish", "what data can I get from KOSIS", "list available trade statistics", "what health data exists in Korea". This skill presents available data listings, not API specifications or code. Covers 260,000+ tables from 100+ agencies across 30 subject categories.
argument-hint: <topic to explore, e.g. employment, healthcare, trade, economy>
context: fork
disable-model-invocation: true
---

# KOSIS Statistics Discovery

Explore and present available Korean national statistics for: **$ARGUMENTS**

## About KOSIS

KOSIS (Korean Statistical Information Service) provides access to 260,000+ statistical tables from 100+ government agencies across 30 subject categories. Data spans demographics, economy, trade, health, education, environment, and more.

- **Portal**: kosis.kr
- **Coverage**: 1953 ~ present (varies by table)
- **Agencies**: Statistics Korea, Bank of Korea, Korea Customs Service, Korea Exchange, and 100+ more

## Discovery Workflow

### Step 1: Search Curated Indicators

Read `references/indicator-catalog.md` and search for `$ARGUMENTS` or related Korean terms. This catalog contains key economic indicators organized by topic (prices, employment, trade, production, etc.) with table IDs, agency codes, period types, and data ranges.

### Step 2: Browse Subject Categories

If Step 1 yields insufficient results, read `references/catalogs.md` to explore the full 30-category taxonomy. Each category includes:
- Subject name (Korean and English)
- Number of available tables
- Search keywords for the KOSIS API

Categories span demographics, economy, labor, trade, health, education, environment, energy, and more. See `references/catalogs.md` for the full 30-category taxonomy with table counts and Korean search keywords.

### Step 3: Supplement via API (if needed)

For topics not covered by the curated catalogs, suggest a keyword search via the KOSIS API:

```
GET https://kosis.kr/openapi/statisticsSearch.do?method=getList
    &apiKey={KEY}&format=json&searchNm={KEYWORD}&resultCount=20
```

Response fields: `TBL_ID`, `ORG_ID`, `TBL_NM`, `STAT_NM`.

### Step 4: Present Results

Use the output template below. Focus on presenting what data exists, not API implementation details.

## Output Template

```markdown
## Available KOSIS Data: $ARGUMENTS

### Matching Indicators

| Indicator | Table ID | Agency | Period | Data Range |
|-----------|----------|--------|--------|------------|
| [name] | [tblId] | [agency] | [M/Q/Y] | [start ~ end] |
| ... | ... | ... | ... | ... |

### Related Categories

| Category | Description | Table Count |
|----------|-------------|-------------|
| [name] | [what it covers] | [count] |
| ... | ... | ... |

### Next Steps

- To get the API specification for a specific table, ask: **"get KOSIS API for [table name or ID]"**
- To browse more tables in a category, ask: **"show me all [category] statistics in KOSIS"**
```

## Reference Files

- **`references/indicator-catalog.md`** — Curated catalog of key economic indicators with tblId, orgId, period, and data range
- **`references/catalogs.md`** — Index of all 30 subject categories and agency-based catalog files (260,000+ tables)
