---
name: datago-openapi
description: Extract and organize Open API specifications from Korea's Public Data Portal (data.go.kr) into structured documentation. Fetches a data.go.kr openapi.do page, parses the Swagger UI and parameter tables, and outputs a complete API spec with endpoints, request parameters, response schema, rate limits, and example requests.
context: fork
disable-model-invocation: true
---

# data.go.kr API Specification Extractor

Extract, organize, and document Open API specifications from Korea's Public Data Portal (data.go.kr).

## When to Use

- A user provides a `data.go.kr` URL and asks to extract or summarize the API spec
- A user wants structured documentation of a Korean public data API
- A user needs to understand request parameters, response schema, or usage of a data.go.kr API

## Core Workflow

### 1. Fetch the Page

Use `WebFetch` with the provided URL. Apply this extraction prompt:

> "Extract all API specification details from this page. Include: API name, base URL, all endpoints, request parameters (name, type, required/optional, size, description, example), response fields (name, type, size, description), authentication method, data format (JSON/XML), rate limits, data period, and any example request URLs. Pay special attention to the Swagger UI section and parameter/response tables."

### 2. Identify Key Information

From the fetched content, locate and extract:

| Category | What to Find |
|----------|-------------|
| API Identity | Name, description, provider |
| Connection | Base URL, endpoint paths, protocol (HTTP/HTTPS), method (GET/POST) |
| Data Format | Response format (JSON, XML, or both) |
| Authentication | `serviceKey` parameter (always required for data.go.kr APIs) |
| Parameters | All request parameters with type, required/optional, size, description, example |
| Response | All response fields with type, size, description |
| Limits | Rate limits per tier (development / production) |
| Metadata | Data update frequency, data period |

### 3. Structure the Output

Present extracted information using the output template below.

## Output Template

```markdown
## [API Name]

### Basic Information

| Item | Value |
|------|-------|
| API Name | [Full Korean name] |
| Base URL | [URL] |
| Endpoint | [Path] |
| Protocol | [HTTP/HTTPS] |
| Data Format | [JSON/XML] |
| Method | [GET/POST] |
| Data Period | [e.g., 2020.01 ~ 2024.12, or "Not specified"] |

### Request Parameters

#### Required

| Parameter | Type | Size | Description | Example |
|-----------|------|------|-------------|---------|
| serviceKey | String | - | Public Data Portal API key | - |

#### Optional

| Parameter | Type | Size | Description | Example |
|-----------|------|------|-------------|---------|

### Response Schema

#### Header

| Field | Type | Description |
|-------|------|-------------|
| resultCode | string | Result code |
| resultMsg | string | Result message |

#### Body (items)

| Field | Type | Size | Description | Example |
|-------|------|------|-------------|---------|

### Example Request

\`\`\`
GET [base_url][endpoint]?serviceKey={API_KEY}&[param1]=[value1]&[param2]=[value2]
\`\`\`

### Rate Limits

| Tier | Traffic | Approval |
|------|---------|----------|
| Development | [limit] | [method] |
| Production | [limit] | [method] |

### Notes
- [Data update schedule, special considerations, etc.]
```

## Key Conventions for data.go.kr APIs

- **serviceKey** is always required — it is the authentication key from the Public Data Portal
- Parameter sizes (e.g., "6" for yyyymm format) indicate maximum character length
- Rate limits typically show two tiers: development (개발용, auto-approved) and production (운영용, requires usage registration)
- Many APIs support both JSON and XML; note which formats are available
- Base URLs vary by provider — some use `apis.data.go.kr`, others use provider-specific domains

## Handling Multiple Endpoints

When an API has multiple endpoints, document each one as a separate section with its own parameters and response schema. Use `### Endpoint 1: [name]`, `### Endpoint 2: [name]` etc.

## Edge Cases

- **Page load failure**: Report the error and suggest verifying the URL
- **No spec found**: Check if the URL is an openapi.do page; if not, inform the user
- **Incomplete data**: Extract what is available, mark missing fields as "Not specified on page"
- **Multiple response formats**: Document each format if schemas differ

## Additional Resources

### Reference Files

For detailed extraction patterns and data.go.kr page structure:
- **`references/extraction-guide.md`** - Page structure details, common field patterns, and provider-specific notes
