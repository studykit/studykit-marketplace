---
name: kosis-openapi
description: This skill should be used when users want to look up or extract KOSIS (kosis.kr) OpenAPI specifications for Korean national statistics indicators. Common triggers include "find KOSIS API for CPI", "get KOSIS table for GDP", "Korean employment statistics API", "KOSIS consumer price index", "query Korean trade data". Covers 260,000+ statistical tables from 100+ government agencies.
argument-hint: <statistical indicator or topic, e.g. CPI, GDP, employment>
context: fork
disable-model-invocation: true
---

# KOSIS OpenAPI Specification Extractor

Extract and organize the KOSIS OpenAPI specification for: **$ARGUMENTS**

## Overview

KOSIS OpenAPI provides RESTful access to 260,000+ statistical tables from 100+ Korean government agencies. All endpoints use `GET` method, require an `apiKey` parameter, and return JSON.

- **Base URL**: `https://kosis.kr/openapi/`
- **Authentication**: `apiKey` parameter (issued from KOSIS portal)
- **Response format**: JSON (default), SDMX, XLS
- **Encoding**: UTF-8

## Core Endpoints

| Service | Endpoint | Purpose |
|---------|----------|---------|
| Statistics Data (recommended) | `Param/statisticsParameterData.do` | Query data by orgId + tblId |
| Integrated Search | `statisticsSearch.do` | Find tblId by keyword |
| Statistics List | `statisticsList.do` | Browse statistics tree |
| Meta Info | `statisticsData.do?method=getMeta` | Get classification (OBJ) and item (ITM) codes |
| Statistics Description | `statisticsExplData.do` | Survey metadata |
| Large Data | `statisticsBigData.do` | 40k+ records (SDMX/XLS) |

## Data Query Workflow

### Step 1: Find the Table ID (tblId)

When the target `tblId` is unknown, search for `$ARGUMENTS` using one of these approaches:

**Option A — Search the indicator catalog:**
Read `references/indicator-catalog.md` and grep for `$ARGUMENTS` or related Korean terms to find tblId from curated economic indicator tables.

**Option B — Keyword search via API:**
```
GET https://kosis.kr/openapi/statisticsSearch.do?method=getList
    &apiKey={KEY}&format=json&searchNm=$ARGUMENTS&resultCount=10
```

Response includes `TBL_ID`, `ORG_ID`, `TBL_NM` for each match.

**Option C — Browse the catalog files:**
For comprehensive catalog browsing, read `references/catalogs.md` which contains index files for all 30 subject categories and 100+ agencies.

### Step 2: Get Classification and Item Codes

Before querying data, confirm `objL1` and `itmId` values using getMeta:

```
# Classification codes (for objL1)
GET https://kosis.kr/openapi/statisticsData.do
    ?method=getMeta&type=OBJ&apiKey={KEY}&orgId={ORG}&tblId={TBL}&format=json

# Item codes (for itmId)
GET https://kosis.kr/openapi/statisticsData.do
    ?method=getMeta&type=ITM&apiKey={KEY}&orgId={ORG}&tblId={TBL}&format=json
```

Other `type` values: `TBL` (table name), `PRD` (period info), `NOTE` (annotations), `UNIT` (units), `SOURCE` (source).

### Step 3: Query Data

```
GET https://kosis.kr/openapi/Param/statisticsParameterData.do?method=getList
    &apiKey={KEY}&format=json
    &orgId={ORG}&tblId={TBL}
    &objL1={CODE}&itmId={ITM}
    &prdSe={PERIOD}&startPrdDe={START}&endPrdDe={END}
```

**Required parameters:**

| Parameter | Description | Example |
|-----------|-------------|---------|
| orgId | Agency code | `101` (Statistics Korea) |
| tblId | Table ID | `DT_1J22003` |
| objL1 | Classification 1 code | `ALL` or specific code |
| itmId | Item code | `ALL` or specific code |
| prdSe | Period type | `M` (monthly), `Q` (quarterly), `Y` (annual) |
| format | Response format | `json` |

**Optional parameters:** `objL2`~`objL8`, `startPrdDe`, `endPrdDe`, `newEstPrdCnt`, `prdInterval`, `outputFields`

### Period Format Reference

| Period | prdSe | Format | Example |
|--------|-------|--------|---------|
| Daily | D | YYYYMMDD | `20240101` |
| Monthly | M | YYYYMM | `202410` |
| Quarterly | Q | YYYYQQ (01-04) | `202401` (Q1), `202404` (Q4) |
| Semi-annual | S | YYYYHH (01-02) | `202401` (H1) |
| Annual | Y | YYYY | `2024` |

> **Important**: Quarterly format uses `01`-`04`, not `1`-`4`. `202401` means Q1, `202404` means Q4.

### Key Response Fields

The main data value is in the `DT` field. Classification names are in `C1_NM`~`C8_NM`, item name in `ITM_NM`, and unit in `UNIT_NM`. For complete field reference, read `references/api-guide.md`.

For agency codes (orgId), error codes, and additional endpoint details, consult `references/api-guide.md`.

## Output Template

When extracting a KOSIS API spec for `$ARGUMENTS`, present using this format:

```markdown
## $ARGUMENTS

### Basic Information

| Item | Value |
|------|-------|
| Table Name | [Korean name] |
| orgId | [agency code] |
| tblId | [table ID] |
| Period Type | [M/Q/Y] |
| Data Range | [start ~ end] |
| Source | [agency name] |

### API Request

GET https://kosis.kr/openapi/Param/statisticsParameterData.do?method=getList
    &apiKey={API_KEY}&format=json
    &orgId=[orgId]&tblId=[tblId]
    &objL1=[code]&itmId=[code]
    &prdSe=[M/Q/Y]&startPrdDe=[start]&endPrdDe=[end]

### Python Example

[requests-based example code]
```

## Additional Resources

### Reference Files

- **`references/api-guide.md`** — Complete KOSIS API documentation with all endpoints, parameters, and Python examples
- **`references/indicator-catalog.md`** — Curated catalog of key economic indicators with tblId, orgId, period, and data range
- **`references/catalogs.md`** — Index of all 30 subject categories and agency-based catalog files (260,000+ tables)
