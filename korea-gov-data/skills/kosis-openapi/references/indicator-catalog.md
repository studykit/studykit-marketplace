# KOSIS Key Economic Indicator Catalog

Curated catalog of major Korean economic indicators available through KOSIS OpenAPI.
Based on 259,087 statistical tables across 30 subject categories.

## Subject Categories Overview (30 categories)

| # | Subject | Tables | Key Content |
|--:|---------|-------:|-------------|
| 1 | Population | 2,286 | Census, demographics, population projections |
| 2 | General Society | 12,048 | Time use surveys, social surveys |
| 3 | Crime/Safety | 3,993 | Crime statistics, traffic accidents |
| 4 | **Labor** | **4,736** | **Employment, unemployment, wages** |
| 5 | **Income/Consumption/Assets** | **860** | **Household trends, spending** |
| 6 | Health | 6,506 | Health surveys, medical statistics |
| 7 | Welfare | 3,097 | Social welfare |
| 8 | Education/Training | 2,946 | Education statistics |
| 9 | Culture/Leisure | 7,505 | Culture, tourism, sports |
| 10 | Housing | 582 | Housing, building permits |
| 11 | Land Use | 1,169 | Land use, cadastral |
| 12 | **Economy/Business Cycle** | **875** | **Economic census, BSI** |
| 13 | Business Management | 8,555 | Business activity, services |
| 14 | Agriculture/Forestry | 11,103 | Agriculture, forestry, livestock |
| 15 | Fisheries | 852 | Fishing, seafood |
| 16 | **Mining/Manufacturing** | **930** | **Industrial production** |
| 17 | **Construction** | **2,224** | **Construction orders, permits** |
| 18 | Transportation/Logistics | 1,304 | Vehicles, logistics |
| 19 | ICT | 8,554 | ICT, e-commerce |
| 20 | Science/Technology | 9,107 | R&D, patents |
| 21 | Wholesale/Retail/Services | 4,962 | Retail sales, services |
| 22 | **Wages** | **113** | **Total wages, work hours** |
| 23 | **Prices** | **51** | **CPI, PPI, import/export prices** |
| 24 | **National Accounts** | **595** | **GDP, GNI, fund flow** |
| 25 | **Government/Finance** | **5,426** | **Fiscal, revenue/expenditure** |
| 26 | **Finance** | **2,435** | **Stock indices, interest rates, exchange rates** |
| 27 | **Trade/BOP** | **317** | **Exports/imports, current account, FDI** |
| 28 | **Environment** | **1,036** | **Air quality, waste, energy** |
| 29 | **Energy** | **1,262** | **Electricity, oil, gas** |
| 30 | Regional Statistics | 153,658 | City/province/district statistics |

> **Bold**: High-value subjects for economic analysis.

---

## 1. Prices (51 tables)

### Consumer Price Index (CPI)

| tblId | Table Name | Period | Data Range | orgId |
|-------|-----------|--------|-----------|-------|
| `DT_1J22003` | Consumer Price Index (2020=100, total) | M/Q/Y | 1965~2025 | 101 |
| `DT_1J22001` | CPI by expenditure purpose (2020=100) | M/Q/Y | 1965~2025 | 101 |
| `DT_1J22002` | CPI by commodity nature (2020=100) | M/Q/Y | 1985~2025 | 101 |
| `DT_1J22042` | Monthly CPI change rate | M | 1965~2026 | 101 |
| `DT_1J22041` | Annual CPI change rate | Y | 1966~2025 | 101 |
| `DT_1J22005` | Living price index (2020=100) | M/Q/Y | 1995~2025 | 101 |
| `DT_1J22004` | Fresh food index (2020=100) | M/Q/Y | 1990~2025 | 101 |
| `DT_1J22009` | Core CPI excl. food & energy (2020=100) | M/Q/Y | 1990~2025 | 101 |
| `DT_1J22010` | Special classification CPI (2020=100) | M/Q/Y | 2015~2025 | 101 |

### Producer Price Index (PPI)

| tblId | Table Name | Period | Data Range | orgId |
|-------|-----------|--------|-----------|-------|
| `DT_404Y014` | PPI basic classification (2020=100) | M/Q/Y | 1965~2025 | 301 |
| `DT_404Y015` | PPI special classification (2020=100) | M/Q/Y | 1965~2025 | 301 |
| `DT_405Y006` | Domestic supply price index | M/Q/Y | 1980~2025 | 301 |

### Import/Export Prices

| tblId | Table Name | Period | Data Range | orgId |
|-------|-----------|--------|-----------|-------|
| `DT_401Y015` | Import price index basic (2020=100) | M/Q/Y | 1971~2025 | 301 |
| `DT_401Y018` | Import price index by use (2020=100) | M/Q/Y | 1971~2025 | 301 |
| `DT_401Y016` | Import price index special (2020=100) | M/Q/Y | 1971~2025 | 301 |

### Other Prices

| tblId | Table Name | Period | Data Range | orgId |
|-------|-----------|--------|-----------|-------|
| `DT_39701_A003` | Construction cost index (2020=100) | M | 2000~2025 | 101 |
| `TX_31802_A000` | Gas station average retail price | M | 2000~2025 | 301 |
| `DT_1J60` | Farm gate price index (2020=100) | Q | 2005~2025 | 101 |

---

## 2. National Accounts / GDP (595 tables)

| tblId | Table Name | Period | Data Range | orgId |
|-------|-----------|--------|-----------|-------|
| `DT_200Y101` | Key indicators (annual) | Y | 1953~2025 | 301 |
| `DT_200Y102` | Key indicators (quarterly) | Q | 1960~2025 | 301 |
| `DT_200Y103` | GDP/GNI by economic activity (SA, nominal, quarterly) | Q | 1960~2025 | 301 |
| `DT_200Y104` | GDP/GNI by economic activity (SA, real, quarterly) | Q | 1960~2025 | 301 |
| `DT_200Y113` | GDP and expenditure (nominal, annual) | Y | 1970~2024 | 301 |
| `DT_2KAA905` | Economic growth rate (constant prices, annual) | Y | 1961~2024 | 101 |
| `DT_1C91` | GRDP by region and economic activity | Y | 1985~2024 | 301 |

---

## 3. Trade / Balance of Payments (317 tables)

### Trade Summary

| tblId | Table Name | Period | Data Range | orgId |
|-------|-----------|--------|-----------|-------|
| `DT_134001_001` | Exports/Imports summary | M/Y | 2000~2025 | 134 |
| `DT_134001_002` | Exports/Imports by country | M | 2000~2025 | 134 |
| `DT_134001_003` | Exports/Imports by continent | M | 2000~2025 | 134 |
| `DT_134004_001` | Trade business diffusion index | M | 2013~2025 | 134 |

### SITC Trade Statistics

| tblId | Table Name | Period | Data Range | orgId |
|-------|-----------|--------|-----------|-------|
| `DT_1R11006_FRM101` | Exports/Imports by country | M/Q/Y | 1965~2025 | 101 |
| `DT_1R11001_FRM101` | Exports/Imports by commodity | M/Q/Y | 2020~2025 | 101 |

### Balance of Payments

| tblId | Table Name | Period | Data Range | orgId |
|-------|-----------|--------|-----------|-------|
| `DT_301Y013` | Balance of payments | M/Q/Y | 1980~2025 | 301 |
| `DT_301Y017` | Current account (seasonally adjusted) | M | 1980~2025 | 301 |
| `DT_301Y014` | Service trade detailed | M/Q/Y | 2006~2025 | 301 |
| `DT_301Y015` | Current account by region | Y | 1998~2024 | 301 |

### FTA / Business-Specific Trade

| tblId | Table Name | Period | Data Range | orgId |
|-------|-----------|--------|-----------|-------|
| `DT_13405_001` | FTA export utilization rate by agreement | Q | 2013~2025 | 134 |
| `DT_1TEC_P116` | Exports/Imports by business size | Q/Y | 2015~2025 | 101 |
| `DT_36005_A001` | Export BSI (EBSI) | Q | 2009~2025 | 101 |

### FDI / Overseas Investment

| tblId | Table Name | Period | Data Range | orgId |
|-------|-----------|--------|-----------|-------|
| `DT_115_2009_H3001_18_1` | FDI inflow by industry | Q | 2000~2025 | 115 |
| `DT_AS10203-N001` | Overseas direct investment | Y | 1980~2024 | 101 |
| `DT_311Y001` | International Investment Position (IIP) | Q/Y | 1994~2024 | 301 |

---

## 4. Labor (4,736 tables)

### Economically Active Population / Employment / Unemployment

| tblId | Table Name | Period | Data Range | orgId |
|-------|-----------|--------|-----------|-------|
| `DT_1DA7001S` | Economically active pop. by gender (incl. employment rate) | M/Q/Y | 2000~2025 | 101 |
| `DT_1DA7002S` | Economically active pop. by age | M/Q/Y | 2000~2025 | 101 |
| `DT_1DA7102S` | Unemployment rate by gender/age | M/Q/Y | 2000~2025 | 101 |
| `DT_1DA7003S` | Economically active pop. by education | M/Q/Y | 2000~2025 | 101 |

### Establishment Employment Trends

| tblId | Table Name | Period | Data Range | orgId |
|-------|-----------|--------|-----------|-------|
| `DT_118N_MON056` | Employment by industry/size | M/Q/Y | 2018~2025 | 118 |
| `DT_118N_MOND56` | Employment by region/industry | M/Q/Y | 2018~2025 | 118 |

### Wage Employment / Productivity

| tblId | Table Name | Period | Data Range | orgId |
|-------|-----------|--------|-----------|-------|
| `DT_1FL_7001` | Wage employment by industry | Q | 2017~2025 | 101 |
| `DT_344N_1D8A_AA` | Labor productivity index (industrial production basis) | Q/Y | 2011~2024 | 344 |

---

## 5. Finance (2,435 tables)

| tblId | Table Name | Period | Data Range | orgId |
|-------|-----------|--------|-----------|-------|
| `DT_343_2010_S0004` | KRX major stock indices | M/Y | 2004~2025 | 343 |
| `DT_343_2010_S0173` | KRX 300 | M/Y | 2011~2025 | 343 |
| `DT_343_2010_S0130` | KTOP 30 | M/Y | 1997~2025 | 343 |
| `DT_281Y001` | Financial transactions (fund flow) | Q/Y | 2009~2024 | 301 |

---

## 6. Income / Consumption / Assets (156 tables)

| tblId | Table Name | Period | Data Range | orgId |
|-------|-----------|--------|-----------|-------|
| `DT_1L9U001` | Monthly avg household income/expenditure (nationwide, 1+ person) | Q/Y | 2019~2024 | 101 |
| `DT_1L9U003` | Household income/expenditure by income quintile | Q/Y | 2019~2024 | 101 |
| `DT_1L9U004` | Household income/expenditure by income decile | Q/Y | 2019~2024 | 101 |

---

## 7. Energy (1,262 tables)

| tblId | Table Name | Period | Data Range | orgId |
|-------|-----------|--------|-----------|-------|
| `TX_31802_A000` | Gas station average retail price | M | 2000~2025 | 301 |

---

## 8. Construction (2,224 tables)

| tblId | Table Name | Period | Data Range | orgId |
|-------|-----------|--------|-----------|-------|
| `DT_39701_A003` | Construction cost index (2020=100) | M | 2000~2025 | 101 |
