# KOSIS OpenAPI Complete Reference

Reference documentation for KOSIS (Korean Statistical Information Service) OpenAPI.

- Source: https://kosis.kr/openapi/
- Base URL: `https://kosis.kr/openapi/`
- Auth: `apiKey` parameter required on all requests
- Method: GET
- Format: JSON (default), SDMX, XLS
- Encoding: UTF-8

> **Note**: KOSIS may enforce IP-based restrictions (error code 13). Register server IPs on the KOSIS portal.

## 1. Statistics List API

Browse the statistics tree or search by keyword to find `orgId` and `tblId`.

### Request

```
GET https://kosis.kr/openapi/statisticsList.do?method=getList
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| apiKey | String | Yes | API key |
| vwCd | String | Yes | View code (see table below) |
| parentListId | String | Yes | Starting list ID (root: empty string or `A`) |
| format | String | Yes | Response format (`json`) |
| searchNm | String | No | Search keyword |
| orgId | String | No | Agency code filter |

**vwCd codes:**

| Code | Description |
|------|-------------|
| MT_ZTITLE | Domestic statistics by subject (most common) |
| MT_OTITLE | Domestic statistics by agency |
| MT_GTITLE01 | e-Local indicators (by subject) |
| MT_GTITLE02 | e-Local indicators (by region) |
| MT_RTITLE | International statistics |
| MT_BUKHAN | North Korea statistics |

### Response Fields

| Field | Description |
|-------|-------------|
| VW_CD | View ID |
| LIST_ID | List ID (for folders) |
| LIST_NM | List name (for folders) |
| ORG_ID | Agency code (for table leaf nodes) |
| TBL_ID | Table ID (for table leaf nodes) — use for data queries |
| TBL_NM | Table name |
| SEND_DE | Last update date |

### Python Example — Keyword Search

```python
import requests

API_KEY = 'YOUR_KOSIS_API_KEY'
BASE = 'https://kosis.kr/openapi/statisticsList.do'

resp = requests.get(BASE, params={
    'method': 'getList',
    'apiKey': API_KEY,
    'format': 'json',
    'vwCd': 'MT_ZTITLE',
    'parentListId': '',
    'searchNm': '소비자물가',
    'orgId': '101',
})

for item in resp.json()[:5]:
    print(item.get('TBL_ID'), item.get('TBL_NM'))
```

## 2. Statistics Data API — Parameter Method (Recommended)

Query data directly using `orgId` + `tblId`. This is the recommended method for programmatic access.

> **Important**: Use `Param/statisticsParameterData.do`, NOT `statisticsData.do`.

### Request

```
GET https://kosis.kr/openapi/Param/statisticsParameterData.do?method=getList
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| apiKey | String | Yes | API key |
| orgId | String | Yes | Agency ID (e.g., 101=Statistics Korea, 301=Bank of Korea) |
| tblId | String | Yes | Table ID (e.g., DT_1J20005) |
| objL1 | String | Yes | Classification 1 code (e.g., `0` = all, `ALL` = all) |
| objL2~objL8 | String | No | Classification 2-8 codes |
| itmId | String | Yes | Item code (e.g., `T20`, `ALL`) |
| prdSe | String | Yes | Period type (M=monthly, Q=quarterly, Y=annual, etc.) |
| startPrdDe | String | No | Start period (format depends on prdSe) |
| endPrdDe | String | No | End period |
| newEstPrdCnt | String | No | Latest N periods (use when start/end not specified) |
| prdInterval | String | No | Period interval (e.g., 2 = biennial) |
| format | String | Yes | Response format (`json`) |
| outputFields | String | No | Select output fields |

### Period Format by prdSe

| Period | prdSe | Format | Example |
|--------|-------|--------|---------|
| Daily | D | YYYYMMDD | 20240101 |
| Monthly | M | YYYYMM | 202410 |
| Bimonthly | M | YYYYMM (odd months) | 202401, 202403 |
| Quarterly | Q | YYYYQQ (QQ: 01-04) | 202401 (Q1), 202404 (Q4) |
| Semi-annual | S | YYYYHH (HH: 01, 02) | 202401 (H1) |
| Annual | Y | YYYY | 2024 |
| Biennial | F | YYYY | 2024, 2026... |
| Irregular | IR | YYYY or YYYYMM | 2024 |

> **Warning**: Quarterly format uses `01`-`04`, NOT `1`-`4`. Using `20241` instead of `202401` causes errors.

### Response Fields

| Field | Description |
|-------|-------------|
| ORG_ID | Agency code |
| TBL_ID | Table ID |
| TBL_NM | Table name |
| C1 ~ C8 | Classification value ID (by level) |
| C1_NM ~ C8_NM | Classification value name |
| C1_OBJ_NM ~ C8_OBJ_NM | Classification axis name |
| ITM_ID | Item ID |
| ITM_NM | Item name |
| UNIT_NM | Unit name |
| PRD_SE | Period type |
| PRD_DE | Period value |
| DT | **Numeric data value** |
| LST_CHN_DE | Last modified date |

### Python Example — CPI Query

```python
import requests

API_KEY = 'YOUR_KOSIS_API_KEY'
BASE = 'https://kosis.kr/openapi/Param/statisticsParameterData.do'

resp = requests.get(BASE, params={
    'method': 'getList',
    'apiKey': API_KEY,
    'format': 'json',
    'orgId': '101',
    'tblId': 'DT_1J22003',
    'objL1': 'ALL',
    'itmId': 'ALL',
    'prdSe': 'M',
    'startPrdDe': '202401',
    'endPrdDe': '202412',
})

for row in resp.json()[:5]:
    print(f"{row['PRD_DE']}  {row['C1_NM']}  {row['ITM_NM']}  {row['DT']} {row['UNIT_NM']}")
```

## 3. Statistics Data API — Registration Method

Query using a pre-registered `userStatsId` from the KOSIS portal.

> **Note**: This method uses fixed URLs and cannot dynamically query different tables. The parameter method (Section 2) is recommended for most use cases.

### Request

```
GET https://kosis.kr/openapi/statisticsData.do?method=getList
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| apiKey | String | Yes | API key |
| userStatsId | String | Yes | Registered table ID |
| prdSe | String | Yes | Period type |
| newEstPrdCnt | String | No | Latest N periods |
| startPrdDe | String | No | Start period |
| endPrdDe | String | No | End period |
| format | String | Yes | Response format (`json`) |

## 4. Integrated Search API

Search for statistics tables by keyword. Returns `TBL_ID` and `ORG_ID` for use with the data query API.

### Request

```
GET https://kosis.kr/openapi/statisticsSearch.do?method=getList
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| apiKey | String | Yes | API key |
| searchNm | String | Yes | Search keyword |
| format | String | Yes | Response format (`json`) |
| orgId | String | No | Agency code filter |
| sort | String | No | Sort: `RANK` (relevance, default) / `DATE` (newest) |
| startCount | String | No | Page number (default: 1) |
| resultCount | String | No | Results per page (default: 10) |

### Response Fields

| Field | Description |
|-------|-------------|
| ORG_ID | Agency code |
| ORG_NM | Agency name |
| TBL_ID | Table ID — use this for data queries |
| TBL_NM | Table name |
| MT_ATITLE | KOSIS category path |
| STRT_PRD_DE | Data period start |
| END_PRD_DE | Data period end |
| CONTENTS | Table contents summary |
| STAT_DB_CNT | Total search result count |

### Python Example

```python
resp = requests.get(
    'https://kosis.kr/openapi/statisticsSearch.do',
    params={
        'method': 'getList',
        'apiKey': API_KEY,
        'format': 'json',
        'searchNm': '소비자물가',
        'orgId': '101',
        'sort': 'DATE',
        'resultCount': '10',
    }
)

for item in resp.json():
    print(item['TBL_ID'], item['TBL_NM'], item['STRT_PRD_DE'], '~', item['END_PRD_DE'])
```

## 5. Meta Info API (getMeta)

Retrieve classification codes, item codes, units, and annotations for a specific table.

### Request

```
GET https://kosis.kr/openapi/statisticsData.do?method=getMeta
    &apiKey={KEY}&orgId={ORG}&tblId={TBL}&type={TYPE}&format=json
```

### type Values

| type | Returns |
|------|---------|
| TBL | Table name |
| ORG | Agency name |
| PRD | Period info (range, frequency) |
| OBJ | Classification list (use to find objL1~objL8 codes) |
| ITM | Item list (use to find itmId codes) |
| NOTE | Annotations |
| UNIT | Units |
| SOURCE | Data source |

### Python Example — Get OBJ and ITM Codes

```python
# Classification (OBJ) codes → use as objL1 value
resp = requests.get(
    'https://kosis.kr/openapi/statisticsData.do',
    params={
        'method': 'getMeta',
        'apiKey': API_KEY,
        'format': 'json',
        'orgId': '101',
        'tblId': 'DT_1J22003',
        'type': 'OBJ',
    }
)
for obj in resp.json():
    print(f"OBJ_ID={obj['OBJ_ID']}  OBJ_NM={obj['OBJ_NM']}")

# Item (ITM) codes → use as itmId value
resp = requests.get(
    'https://kosis.kr/openapi/statisticsData.do',
    params={
        'method': 'getMeta',
        'apiKey': API_KEY,
        'format': 'json',
        'orgId': '101',
        'tblId': 'DT_1J22003',
        'type': 'ITM',
    }
)
for itm in resp.json():
    print(f"ITM_ID={itm['ITM_ID']}  ITM_NM={itm['ITM_NM']}")
```

## 6. Statistics Description API

Retrieve survey metadata (purpose, frequency, legal basis, etc.) for a statistical survey.

### Request

```
GET https://kosis.kr/openapi/statisticsExplData.do?method=getList
    &apiKey={KEY}&orgId={ORG}&tblId={TBL}&metaItm=All&format=json
```

## 7. Large Data API

For datasets exceeding 40,000 records. Returns SDMX or XLS format.

> **Note**: Datasets exceeding 200,000 records cannot use XLS format. Reduce query scope.

```
GET https://kosis.kr/openapi/statisticsBigData.do?method=getList
    &apiKey={KEY}&userStatsId={ID}&format=sdmx&type=DSD
```

## 8. Key Indicators API

Retrieve concept definitions, calculation methods, and sources for individual indicators.

```
GET https://kosis.kr/openapi/pkNumberService.do
    ?method=getList&service=1&serviceDetail=pkNotion
    &apiKey={KEY}&jipyoId={JIPYO_ID}&format=json
```

## 9. Major Agency Codes (orgId)

| orgId | Agency | Key Statistics |
|-------|--------|---------------|
| 101 | Statistics Korea (통계청/국가데이터처) | CPI, PPI, employment, unemployment, population |
| 301 | Bank of Korea (한국은행) | GDP, balance of payments, monetary indicators |
| 134 | Korea Customs Service (관세청) | Trade statistics |
| 154 | Financial Supervisory Service (금융감독원) | Financial statistics |
| 116 | National Tax Service (국세청) | Tax statistics |
| 200 | Ministry of Education (교육부) | Education statistics |
| 343 | Korea Exchange (한국거래소) | Stock market indices |
| 118 | Ministry of Employment and Labor (고용노동부) | Employment trends |

## 10. Error Codes

| Code | Meaning | Resolution |
|------|---------|------------|
| 11 | Auth error (invalid API key) | Reissue key from KOSIS portal |
| 13 | IP access denied | Register server IP on KOSIS portal |
| 20 | No results | Check tblId, objL1, itmId, date format |
| 30 | Registered table not found | Re-register userStatsId |

## 11. Recommended Data Query Procedure

When the tblId is unknown:

1. `statisticsSearch.do` — keyword search → get `TBL_ID`, `ORG_ID`
2. `statisticsData.do?method=getMeta&type=OBJ` — get classification codes (`objL1`)
3. `statisticsData.do?method=getMeta&type=ITM` — get item codes (`itmId`)
4. `Param/statisticsParameterData.do` — query actual data
