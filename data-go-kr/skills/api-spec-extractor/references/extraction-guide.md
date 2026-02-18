# data.go.kr Page Structure & Extraction Patterns

## Page URL Patterns

data.go.kr Open API detail pages follow this URL pattern:

```
https://www.data.go.kr/data/{dataId}/openapi.do
```

Where `{dataId}` is a numeric identifier (e.g., `15101609`, `15059113`).

## Page Structure

### Swagger UI Section

The primary source of API specification. Located via:

```
#api-swagger > section > div.swagger-ui
```

> **Note:** These CSS selectors are based on the data.go.kr page structure as of early 2025. If extraction fails, verify the current page structure.

Contains:
- Endpoint definitions with HTTP methods
- Parameter tables (name, type, required, description)
- Response schema tables
- Example values

### Detailed Description Section (상세설명)

Contains:
- API name and provider organization
- Service description
- Data period and update schedule
- Base URL information

### Request Parameters (요청변수)

Table columns typically include:
- 항목명 (Parameter name)
- 타입 (Type): String, Number, Integer
- 항목크기 (Size): Character length limit
- 필수여부 (Required): Y/N
- 항목설명 (Description)
- 샘플데이터 (Example)

### Response Fields (출력결과)

Table columns typically include:
- 항목명 (Field name)
- 타입 (Type)
- 항목크기 (Size)
- 항목설명 (Description)
- 샘플데이터 (Example)

### Preview Section (미리보기)

May contain example request URLs with actual parameter values.

## Common Provider Patterns

### apis.data.go.kr (Government Gateway)

Government APIs proxied through the central gateway.

- **Base URL format**: `https://apis.data.go.kr/{orgCode}/{serviceName}`
- **Example**: `https://apis.data.go.kr/1220000/Itemtrade`
- **Protocol**: HTTPS preferred, HTTP also supported
- **Authentication**: serviceKey as query parameter

### Provider-hosted APIs

APIs hosted directly by the providing organization.

- **Base URL format**: `http://{provider-domain}:{port}/openapi/service/{serviceName}`
- **Example**: `http://www.ygpa.or.kr:9191/openapi/service/statCargoArea`
- **Protocol**: Often HTTP only
- **Authentication**: serviceKey as query parameter

## Common Parameter Patterns

### Date Range Parameters

Most statistical APIs use year-month (yyyymm) format:

| Pattern | Start Parameter | End Parameter | Format | Example |
|---------|----------------|---------------|--------|---------|
| Pattern A | strtYymm | endYymm | yyyymm (number) | 202401 |
| Pattern B | yyyymmfr | yyyymmto | yyyymm (string, size 6) | 202401 |
| Pattern C | startDe | endDe | yyyyMMdd (string, size 8) | 20240101 |

### Classification Code Parameters

| Parameter | Description | Common Values |
|-----------|-------------|---------------|
| hsSgn | HS code (trade classification) | 2/4/6/10 digit codes |
| prt_at_code | Port/area code | 3-digit codes (e.g., 620) |
| g_in_out | Import/Export flag | I (import), O (export) |

### Pagination Parameters

Some APIs support pagination:

| Parameter | Description | Default |
|-----------|-------------|---------|
| pageNo | Page number | 1 |
| numOfRows | Results per page | 10 |

## Common Response Patterns

### Standard Response Wrapper

Most data.go.kr APIs wrap responses in a standard structure:

```xml
<response>
  <header>
    <resultCode>00</resultCode>
    <resultMsg>NORMAL SERVICE.</resultMsg>
  </header>
  <body>
    <items>
      <item>
        <!-- actual data fields -->
      </item>
    </items>
    <numOfRows>10</numOfRows>
    <pageNo>1</pageNo>
    <totalCount>100</totalCount>
  </body>
</response>
```

### Result Codes

| Code | Message | Meaning |
|------|---------|---------|
| 00 | NORMAL SERVICE | Success |
| 01 | APPLICATION ERROR | Application error |
| 10 | INVALID REQUEST PARAMETER ERROR | Bad parameter |
| 12 | NO OPENAPI SERVICE ERROR | Service not found |
| 20 | SERVICE ACCESS DENIED ERROR | Access denied |
| 22 | LIMITED NUMBER OF SERVICE REQUESTS EXCEEDS ERROR | Rate limit exceeded |
| 30 | SERVICE KEY IS NOT REGISTERED ERROR | Invalid key |
| 31 | DEADLINE HAS EXPIRED ERROR | Key expired |

## Rate Limit Tiers

### Development (개발용)

- Auto-approved on API subscription
- Typically 1,000 requests/day
- Sufficient for testing and prototyping

### Production (운영용)

- Requires usage registration (활용사례 등록)
- Higher limits (varies by API, often 10,000+/day)
- Auto-approved after registration in most cases

## Real-World Extraction Examples

### Example 1: Trade Statistics API (관세청 품목별 수출입실적)

Source: `https://www.data.go.kr/data/15101609/openapi.do`

Extracted spec:

- **Base URL**: `https://apis.data.go.kr/1220000/Itemtrade`
- **Endpoint**: `/getItemtradeList`
- **Format**: XML
- **Required params**: serviceKey, strtYymm (number), endYymm (number)
- **Optional params**: hsSgn (number, HS code 2/4/6/10 digits)
- **Response fields**: year, hsCode, statKor, expDlr, expWgt, impDlr, impWgt, balPayments

### Example 2: Cargo Transport Statistics (여수광양항만공사 지역별 화물수송 통계)

Source: `https://www.data.go.kr/data/15059113/openapi.do`

Extracted spec:

- **Base URL**: `http://www.ygpa.or.kr:9191/openapi/service/statCargoArea`
- **Endpoint**: `/getStatCargoArea`
- **Format**: JSON, XML
- **Required params**: serviceKey, prt_at_code (String, 3), yyyymmfr (String, 6), yyyymmto (String, 6)
- **Optional params**: g_in_out (String, 1: I=import, O=export)
- **Response fields**: title, totTon, korTon, forTon
