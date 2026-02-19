# KOSIS Statistics Table Catalogs

Complete index of all KOSIS statistics tables organized by subject and agency.
Source: KOSIS portal XLS catalog exports (523,204 total tables).

## Catalog Overview

| Catalog | vwCd | Tables | Description |
|---------|------|-------:|-------------|
| Subject-based | MT_ZTITLE | 259,087 | 30 subjects |
| Agency-based | MT_OTITLE | 259,410 | 100+ agencies |
| e-Local Indicators | MT_GTITLE01 | 257 | Regional indicators by subject |
| International | MT_RTITLE | 2,341 | International statistics |
| Statistical Yearbook | — | 1,097 | Korea Statistical Yearbook |
| North Korea | MT_BUKHAN | 1,012 | North Korea statistics |

## Subject-Based Categories (30 subjects, vwCd: MT_ZTITLE)

| # | Subject (Korean) | Subject (English) | Tables |
|--:|-----------------|-------------------|-------:|
| 1 | 인구 | Population | 2,286 |
| 2 | 사회일반 | General Society | 12,048 |
| 3 | 범죄ㆍ안전 | Crime/Safety | 3,993 |
| 4 | 노동 | Labor | 4,736 |
| 5 | 소득ㆍ소비ㆍ자산 | Income/Consumption/Assets | 860 |
| 6 | 보건 | Health | 6,506 |
| 7 | 복지 | Welfare | 3,097 |
| 8 | 교육ㆍ훈련 | Education/Training | 2,946 |
| 9 | 문화ㆍ여가 | Culture/Leisure | 7,505 |
| 10 | 주거 | Housing | 582 |
| 11 | 국토이용 | Land Use | 1,169 |
| 12 | 경제일반ㆍ경기 | Economy/Business Cycle | 875 |
| 13 | 기업경영 | Business Management | 8,555 |
| 14 | 농림 | Agriculture/Forestry | 11,103 |
| 15 | 수산 | Fisheries | 852 |
| 16 | 광업ㆍ제조업 | Mining/Manufacturing | 930 |
| 17 | 건설 | Construction | 2,224 |
| 18 | 교통ㆍ물류 | Transportation/Logistics | 1,304 |
| 19 | 정보통신 | ICT | 8,554 |
| 20 | 과학ㆍ기술 | Science/Technology | 9,107 |
| 21 | 도소매ㆍ서비스 | Wholesale/Retail/Services | 4,962 |
| 22 | 임금 | Wages | 113 |
| 23 | 물가 | Prices | 51 |
| 24 | 국민계정 | National Accounts | 595 |
| 25 | 정부ㆍ재정 | Government/Fiscal | 5,426 |
| 26 | 금융 | Finance | 2,435 |
| 27 | 무역ㆍ국제수지 | Trade/BOP | 317 |
| 28 | 환경 | Environment | 1,036 |
| 29 | 에너지 | Energy | 1,262 |
| 30 | 지역통계 | Regional Statistics | 153,658 |

## Major Agencies (orgId reference)

### Central Government

| orgId | Agency (Korean) | Agency (English) | Tables |
|-------|----------------|-------------------|-------:|
| 101 | 국가데이터처/통계청 | Statistics Korea | 11,139 |
| 301 | 한국은행 | Bank of Korea | — |
| 134 | 관세청 | Korea Customs Service | 60 |
| 116 | 국세청 | National Tax Service | 1,254 |
| 200 | 교육부 | Ministry of Education | 2,330 |
| 118 | 고용노동부 | Ministry of Employment and Labor | 729 |

### Financial / Market

| orgId | Agency (Korean) | Agency (English) | Tables |
|-------|----------------|-------------------|-------:|
| 154 | 금융감독원 | Financial Supervisory Service | — |
| 343 | 한국거래소 | Korea Exchange | — |
| 344 | 한국생산성본부 | Korea Productivity Center | — |

### Regional Governments

| orgId | Agency (Korean) | Agency (English) | Tables |
|-------|----------------|-------------------|-------:|
| — | 서울특별시 | Seoul Metropolitan | 1,993 |
| — | 부산광역시 | Busan Metropolitan | 5,606 |
| — | 경기도 | Gyeonggi Province | — |

## How to Find a Specific Table

### By Subject

To find tables in a specific subject area, search the indicator catalog (`references/indicator-catalog.md`) for curated key indicators, or use the KOSIS `statisticsSearch.do` API with Korean keywords.

**Common search keywords by subject:**

| Subject | Korean Keywords |
|---------|----------------|
| Prices/CPI | 소비자물가, 물가지수, CPI |
| GDP | GDP, 국내총생산, 경제성장률 |
| Employment | 고용률, 실업률, 경제활동인구 |
| Trade | 수출, 수입, 무역, 국제수지 |
| Finance | 주가지수, 금리, 환율 |
| Wages | 임금, 근로시간 |
| Housing | 주택, 건축허가 |
| Population | 인구, 출생, 사망 |

### By Agency

To find all tables from a specific agency, use the `statisticsList.do` API with `vwCd=MT_OTITLE` and `orgId`.

### By Table ID Pattern

KOSIS table IDs follow loose patterns:

| Prefix Pattern | Typical Source |
|---------------|---------------|
| `DT_1J*` | Statistics Korea — prices, CPI |
| `DT_1DA*` | Statistics Korea — labor, employment |
| `DT_200Y*` | Bank of Korea — national accounts |
| `DT_301Y*` | Bank of Korea — balance of payments |
| `DT_401Y*` | Bank of Korea — import/export prices |
| `DT_404Y*` | Bank of Korea — PPI |
| `DT_134*` | Korea Customs Service — trade |
| `DT_343*` | Korea Exchange — stock indices |
| `DT_1L9U*` | Statistics Korea — household income |
| `DT_1FL*` | Statistics Korea — wage employment |
