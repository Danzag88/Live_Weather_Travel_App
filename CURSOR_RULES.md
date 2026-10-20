Always apply this guidance when working in this repository.

## Overview

This repo connects Cursor to Snowflake account `QNKEIAF-UH49076` (host `QNKEIAF-UH49076.snowflakecomputing.com`) using a programmatic access token (PAT). Session context:

- User: `DANZAG88`
- Role: `ACCOUNTADMIN`
- Warehouse: `COMPUTE_WH` (always set; SQL fails without a warehouse)
- Database: `SNOWFLAKE_LEARNING_DB`
- Schema: `TEST_SNOWFLAKEDB`

Primary paths:

- Snowflake-managed MCP (see `.cursor/mcp.json`) for tools such as `execute_sql`, fetch, search, and email.
- Direct SQL API and Cortex REST API (see README.md and SnowflakeDB) when MCP is not available.

Do not commit PAT secrets, passwords, or `.env` files. Read the token from `SNOWFLAKE_PAT`.

The value lives only in gitignored files:

- `.env` — `SNOWFLAKE_PAT=` is the value Cursor and local code read. Paste the secret after the equals sign.
- `.secrets/snowflake_pat` — the same secret as the only line in the file, for the Snowflake CLI (`PROGRAMMATIC_ACCESS_TOKEN`).

SQL setup scripts: `authentication.sql`, `DB_Setup.sql`, `email_integration.sql`.

## Web resources

- Snowflake-managed MCP: https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-mcp
- SQL API: https://docs.snowflake.com/en/developer-guide/sql-api/index
- SQL API auth: https://docs.snowflake.com/en/developer-guide/sql-api/authenticating
- REST API auth (PAT): https://docs.snowflake.com/en/developer-guide/snowflake-rest-api/authentication
- Programmatic access tokens: https://docs.snowflake.com/en/user-guide/programmatic-access-tokens
- Cortex REST API: https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-rest-api
- Notification / email integrations: https://docs.snowflake.com/en/user-guide/notifications/email-notifications
- SYSTEM$SEND_EMAIL: https://docs.snowflake.com/en/sql-reference/stored-procedures/system_send_email
- Network rules: https://docs.snowflake.com/en/sql-reference/sql/create-network-rule
- Network policies: https://docs.snowflake.com/en/user-guide/network-policies
- Authentication policies: https://docs.snowflake.com/en/sql-reference/sql/create-authentication-policy

Account URLs:

- Snowsight / API host: https://QNKEIAF-UH49076.snowflakecomputing.com
- SQL statements: https://QNKEIAF-UH49076.snowflakecomputing.com/api/v2/statements
- Cortex chat: https://QNKEIAF-UH49076.snowflakecomputing.com/api/v2/cortex/v1/chat/completions
- Managed MCP (after `CREATE MCP SERVER`): https://QNKEIAF-UH49076.snowflakecomputing.com/api/v2/databases/<DATABASE>/schemas/<SCHEMA>/mcp-servers/<SERVER_NAME>

## MCP connections

Cursor MCP config is `.cursor/mcp.json`:

- Server name: `snowflake`
- Local command: `snowflake/mcp_stdio_proxy.py` (stdio). It reads `SNOWFLAKE_PAT` from `.env` or `.secrets/snowflake_pat` and forwards to the managed server.
- Managed server: `SNOWFLAKE_LEARNING_DB.TEST_SNOWFLAKEDB.TEST_MCP_SERVER`
- URL: `https://QNKEIAF-UH49076.snowflakecomputing.com/api/v2/databases/SNOWFLAKE_LEARNING_DB/schemas/TEST_SNOWFLAKEDB/mcp-servers/TEST_MCP_SERVER`
- Headers sent by the proxy: `Authorization: Bearer <SNOWFLAKE_PAT>`, `X-Snowflake-Authorization-Token-Type: PROGRAMMATIC_ACCESS_TOKEN`

Do not put the token in `mcp.json`.

Prerequisites (run `authentication.sql` and `DB_Setup.sql` in Snowsight):

- Network rule `MCP_EXTERNAL_ACCESS_RULE` (IPV4, `0.0.0.0/0`, INGRESS)
- Network policy `MCP_NETWORK_POLICY` applied to user `DANZAG88`
- Authentication policy `MCP_AUTH_POLICY` with `PROGRAMMATIC_ACCESS_TOKEN`
- PAT `mcp_server_pat` stored only as `SNOWFLAKE_PAT`

If the managed MCP object exists, prefer the full `/api/v2/databases/.../mcp-servers/...` URL. Do not put the token in `mcp.json`.

## How to call the MCP tools

Use the Snowflake MCP server tools when they are connected. Qualifying names must be `DATABASE.SCHEMA.OBJECT`. Always set warehouse `COMPUTE_WH`.

### Fetch (read rows)

Use `execute_sql` (or the SQL API) with `SELECT`. Example: fetch active email recipients.

```sql
SELECT
  EMAIL_ADDRESS,
  INTEGRATION_SCOPE,
  RECIPIENT_TYPE,
  IS_ACTIVE,
  CREATED_TIMESTAMP,
  UPDATED_AT,
  ENVIRONMENT,
  STATUS_SCOPE,
  SEND_DAYS
FROM SHARED_DB.PUBLIC.EMAIL_RECIPIENTS
WHERE IS_ACTIVE = TRUE
  AND ENVIRONMENT = 'Live'
  AND STATUS_SCOPE = 'All'
ORDER BY EMAIL_ADDRESS;
```

MCP-style tool arguments:

```json
{
  "statement": "SELECT * FROM SHARED_DB.PUBLIC.EMAIL_RECIPIENTS WHERE IS_ACTIVE = TRUE LIMIT 100",
  "warehouse": "COMPUTE_WH",
  "database": "SHARED_DB",
  "schema": "PUBLIC",
  "role": "ACCOUNTADMIN"
}
```

### execute_sql (DDL/DML/queries)

```json
{
  "statement": "SHOW TABLES IN SCHEMA SNOWFLAKE_LEARNING_DB.TEST_SNOWFLAKEDB",
  "warehouse": "COMPUTE_WH",
  "database": "SNOWFLAKE_LEARNING_DB",
  "schema": "TEST_SNOWFLAKEDB",
  "role": "ACCOUNTADMIN"
}
```

Session check:

```sql
SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_SCHEMA();
```

### Send email

Integration: `TEST_EMAIL_INTEGRATION` (`email_integration.sql`). Recipients must be in `ALLOWED_RECIPIENTS` and verified on a Snowflake user. Prefer addresses from `SHARED_DB.PUBLIC.EMAIL_RECIPIENTS`.

```sql
CALL SYSTEM$SEND_EMAIL(
  'TEST_EMAIL_INTEGRATION',
  'replace-with-verified-user@example.com',
  'Snowflake Test Notification',
  'Test body from Cursor MCP / execute_sql.'
);
```

Workflow:

1. `execute_sql` to `SELECT EMAIL_ADDRESS FROM SHARED_DB.PUBLIC.EMAIL_RECIPIENTS WHERE IS_ACTIVE AND RECIPIENT_TYPE = 'TO'`.
2. `execute_sql` to `CALL SYSTEM$SEND_EMAIL(...)` for each allowed address (or a comma-separated list if the integration allows it).
3. Do not email addresses that are not in `ALLOWED_RECIPIENTS`.

### Search the database (MCP + SQL)

Discover objects:

```sql
SHOW DATABASES;
SHOW SCHEMAS IN DATABASE SNOWFLAKE_LEARNING_DB;
SHOW TABLES IN SCHEMA SNOWFLAKE_LEARNING_DB.TEST_SNOWFLAKEDB;
SHOW TABLES IN SCHEMA SHARED_DB.PUBLIC;
```

Catalog search:

```sql
SELECT TABLE_CATALOG, TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE
FROM SNOWFLAKE_LEARNING_DB.INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'TEST_SNOWFLAKEDB'
ORDER BY TABLE_NAME;

SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
FROM SHARED_DB.INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'PUBLIC'
  AND TABLE_NAME = 'EMAIL_RECIPIENTS'
ORDER BY ORDINAL_POSITION;
```

If a Cortex Search service exists, call the MCP `CORTEX_SEARCH_SERVICE_QUERY` tool with that service identifier. If it does not exist, use `SHOW TABLES` / `INFORMATION_SCHEMA` / `SELECT` — do not invent a search service name.

## Known issues

- PAT `401` `390432` Network policy is required. PATs fail until a network policy is set on the user/account. Run `authentication.sql`.
- PAT not usable until `PROGRAMMATIC_ACCESS_TOKEN` is in the authentication policy. Apply `MCP_AUTH_POLICY` before creating or using a PAT.
- Warehouse unset. Snowsight may show no warehouse. Always pass `COMPUTE_WH` in SQL and MCP calls.
- MCP URL vs SQL API URL. Account root URL is not the managed MCP path. Full MCP URL needs `CREATE MCP SERVER` plus database/schema/server name.
- Email recipients must be verified Snowflake users listed on `TEST_EMAIL_INTEGRATION`. `SYSTEM$SEND_EMAIL` rejects others.
- `GRANT USAGE` is not `SELECT`. `DB_Setup.sql` grants `USAGE` only. Grant `SELECT`/`INSERT` separately for table access.
- Snowflake `PRIMARY KEY` is not enforced on standard tables. Treat `EMAIL_RECIPIENTS` PK as documentation unless using a hybrid table.
- `CREATE OR REPLACE TABLE` drops data. Do not rerun replace-table scripts against populated tables without a backup.
- Never paste PATs into source files. If a token leaks into SnowflakeDB or `mcp.json`, remove it and rotate the PAT.
- `SNOWFLAKE_SAMPLE_DATA` is read-only. Do not create MCP servers or tables there. App objects live in `SNOWFLAKE_LEARNING_DB` / `SHARED_DB`.

## Timestamp handling

- Store business timestamps as `TIMESTAMP_NTZ(9)` unless a timezone is required.
- `EMAIL_RECIPIENTS.CREATED_TIMESTAMP` defaults to `CURRENT_TIMESTAMP()` (session TZ converted to NTZ).
- Set `UPDATED_AT` explicitly on updates; it is nullable and has no default.
- Compare dates with `TO_TIMESTAMP_NTZ` / `DATE_TRUNC` so TZ and NTZ are not mixed incorrectly.
- When returning timestamps to the user, state that values are NTZ (no offset). Do not assume UTC unless confirmed with `SHOW PARAMETERS LIKE 'TIMEZONE'`.
- SQL API / MCP may return timestamps as strings. Parse them; do not invent offsets.
- Prefer `CURRENT_TIMESTAMP()` for NTZ columns; use `SYSDATE()` / `CONVERT_TIMEZONE` only when timezone conversion is intentional.

Example update:

```sql
UPDATE SHARED_DB.PUBLIC.EMAIL_RECIPIENTS
SET NOTES = 'Updated from Cursor',
    UPDATED_AT = CURRENT_TIMESTAMP()
WHERE EMAIL_ADDRESS = 'replace-with-verified-user@example.com'
  AND INTEGRATION_SCOPE = 'ALL'
  AND ENVIRONMENT = 'Live'
  AND STATUS_SCOPE = 'All';
```

## Workflow

1. Confirm `SNOWFLAKE_PAT` is set and MCP `snowflake` is connected (or use `python3 SnowflakeDB` / SQL API).
2. `execute_sql`: `SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_SCHEMA()`.
3. Search: `SHOW TABLES` / `INFORMATION_SCHEMA` in `SNOWFLAKE_LEARNING_DB.TEST_SNOWFLAKEDB` and `SHARED_DB.PUBLIC`.
4. Fetch: `SELECT` from the key tables below with explicit filters (`IS_ACTIVE`, `ENVIRONMENT`, `STATUS_SCOPE`).
5. Mutate only with fully qualified names and a `WHERE` clause that matches the composite key when updating `EMAIL_RECIPIENTS`.
6. Email: load recipients from `EMAIL_RECIPIENTS`, then `SYSTEM$SEND_EMAIL` via `TEST_EMAIL_INTEGRATION`.
7. Report row counts, filters used, and timestamp columns as NTZ. Do not invent rows.

## Key tables

| Table | Purpose |
| --- | --- |
| `SHARED_DB.PUBLIC.EMAIL_RECIPIENTS` | Notification list. PK: `(EMAIL_ADDRESS, INTEGRATION_SCOPE, ENVIRONMENT, STATUS_SCOPE)`. Defaults: `INTEGRATION_SCOPE='ALL'`, `RECIPIENT_TYPE='TO'`, `IS_ACTIVE=TRUE`, `ENVIRONMENT='Live'`, `STATUS_SCOPE='All'`, `SEND_DAYS='All'`. |
| `SNOWFLAKE_LEARNING_DB.TEST_SNOWFLAKEDB.*` | Primary app/schema for this test project. List with `SHOW TABLES` before querying. |
| `SNOWFLAKE_LEARNING_DB.INFORMATION_SCHEMA.*` | Catalog for learning DB. |
| `SHARED_DB.INFORMATION_SCHEMA.*` | Catalog for shared DB. |

Other objects: integration `TEST_EMAIL_INTEGRATION`; network rule `MCP_EXTERNAL_ACCESS_RULE`; policies `MCP_NETWORK_POLICY`, `MCP_AUTH_POLICY`.

## Accuracy rules

- Query Snowflake; do not guess table contents, row counts, or column values.
- Use fully qualified names. Do not rely on an implicit database/schema.
- Always specify `COMPUTE_WH` (or verify `CURRENT_WAREHOUSE()` is set).
- Filter `EMAIL_RECIPIENTS` on the composite key columns when updating or deleting.
- Honor `IS_ACTIVE`, `ENVIRONMENT`, `STATUS_SCOPE`, and `SEND_DAYS` before sending email.
- Quote string literals exactly (`'Live'`, `'All'`, `'ALL'`, `'TO'`) as stored; they are case-sensitive unless a collation says otherwise.
- If a tool or query errors, report the Snowflake code/message (for example `390432`) and stop. Do not retry blindly with different credentials.
- Never write secrets into git, README, `mcp.json`, or chat logs.
- Prefer `SELECT` / `SHOW` before `CREATE OR REPLACE`.
- When summarizing results, distinguish empty result sets from failed queries.
