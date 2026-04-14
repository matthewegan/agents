---
name: aws-redshift-data-api
description: AWS Redshift Data API reference for querying Redshift clusters via HTTP using the AWS SDK. Use this skill whenever the user is working with @aws-sdk/client-redshift-data, querying Redshift via the Data API, writing code that executes SQL against Redshift without a direct connection, setting up IAM permissions for Redshift Data API access, or troubleshooting Data API issues. Also trigger when you see imports from @aws-sdk/client-redshift-data, RedshiftDataClient, ExecuteStatementCommand, or GetStatementResultCommand in the codebase.
---

# AWS Redshift Data API

Reference for querying Amazon Redshift via the HTTP-based Data API using `@aws-sdk/client-redshift-data`.

**Data API in one sentence:** Submit SQL over HTTP, poll for completion, fetch results — no database drivers, persistent connections, or VPC peering required.

## Installation

```bash
npm install @aws-sdk/client-redshift-data
```

## Core Concepts

### Async Query Model

Every query follows a three-step pattern: **execute → poll → fetch**.

```typescript
import {
  RedshiftDataClient,
  ExecuteStatementCommand,
  DescribeStatementCommand,
  GetStatementResultCommand,
} from "@aws-sdk/client-redshift-data";

const client = new RedshiftDataClient({ region: "us-east-1" });

// 1. Submit query
const { Id } = await client.send(new ExecuteStatementCommand({
  ClusterIdentifier: "my-cluster",
  Database: "dev",
  DbUser: "myuser",
  Sql: "SELECT * FROM schema.table LIMIT 100",
}));

// 2. Poll until done
let status: string;
do {
  const desc = await client.send(new DescribeStatementCommand({ Id }));
  status = desc.Status!;
  if (status === "FAILED") throw new Error(desc.Error);
  if (status !== "FINISHED") await new Promise(r => setTimeout(r, 1000));
} while (status !== "FINISHED");

// 3. Fetch results
const result = await client.send(new GetStatementResultCommand({ Id }));
// result.Records — array of rows, each row is array of typed values
// result.ColumnMetadata — column names, types, etc.
// result.TotalNumRows — total row count
```

### Authentication Methods

#### Temporary Credentials (DbUser) — simplest for ECS/Lambda

```typescript
new ExecuteStatementCommand({
  ClusterIdentifier: "my-cluster",
  Database: "dev",
  DbUser: "myuser",  // cluster must have this user
  Sql: "SELECT 1",
});
```

Requires IAM permission: `redshift:GetClusterCredentials`

#### AWS Secrets Manager — recommended for production

```typescript
new ExecuteStatementCommand({
  ClusterIdentifier: "my-cluster",
  Database: "dev",
  SecretArn: "arn:aws:secretsmanager:us-east-1:123456789012:secret:my-secret",
  Sql: "SELECT 1",
});
```

Requires IAM permission: `secretsmanager:GetSecretValue`

#### Serverless Workgroups

```typescript
new ExecuteStatementCommand({
  WorkgroupName: "my-workgroup",
  Database: "dev",
  // No DbUser needed — derived from IAM identity
  Sql: "SELECT 1",
});
```

Requires IAM permission: `redshift-serverless:GetCredentials`

## All Available Commands

### Query Execution

| Command | Purpose |
|---------|---------|
| `ExecuteStatementCommand` | Run a single SQL statement |
| `BatchExecuteStatementCommand` | Run multiple SQL statements |
| `CancelStatementCommand` | Cancel an in-progress query |
| `DescribeStatementCommand` | Check query status (SUBMITTED → STARTED → FINISHED/FAILED) |
| `GetStatementResultCommand` | Fetch results as JSON (typed values) |
| `GetStatementResultV2Command` | Fetch results as CSV (more efficient for large sets) |
| `ListStatementsCommand` | List recent statements |

### Schema Discovery (synchronous — no polling needed)

| Command | Purpose |
|---------|---------|
| `ListSchemasCommand` | List all schemas in a database |
| `ListTablesCommand` | List tables in a schema |
| `DescribeTableCommand` | Get column metadata for a table |

### Schema Discovery Examples

```typescript
import {
  ListSchemasCommand,
  ListTablesCommand,
  DescribeTableCommand,
} from "@aws-sdk/client-redshift-data";

// List schemas
const schemas = await client.send(new ListSchemasCommand({
  ClusterIdentifier: "my-cluster",
  Database: "dev",
  DbUser: "myuser",
}));
// schemas.Schemas → ["public", "exerp", "toast", ...]

// List tables in a schema
const tables = await client.send(new ListTablesCommand({
  ClusterIdentifier: "my-cluster",
  Database: "dev",
  DbUser: "myuser",
  SchemaPattern: "exerp",  // schema filter
}));
// tables.Tables → [{ name: "person", schema: "exerp", type: "TABLE" }, ...]

// Describe a table's columns
const columns = await client.send(new DescribeTableCommand({
  ClusterIdentifier: "my-cluster",
  Database: "dev",
  DbUser: "myuser",
  Schema: "exerp",
  Table: "person",
}));
// columns.ColumnList → [{ name: "id", typeName: "int4", nullable: 0 }, ...]
```

## Result Format

### JSON (GetStatementResult)

```json
{
  "Records": [
    [
      { "longValue": 42 },
      { "stringValue": "hello" },
      { "doubleValue": 3.14 },
      { "booleanValue": true },
      { "isNull": true }
    ]
  ],
  "ColumnMetadata": [
    { "name": "id", "typeName": "int4", "nullable": 0 },
    { "name": "name", "typeName": "varchar", "nullable": 1 }
  ],
  "TotalNumRows": 1
}
```

Each cell is an object with exactly one typed key:
- `longValue` — integers
- `stringValue` — strings, dates, timestamps
- `doubleValue` — floats/doubles
- `booleanValue` — booleans
- `isNull: true` — null values
- `blobValue` — binary data

### CSV (GetStatementResultV2) — more efficient for large results

Returns results in 1MB chunks. Use `NextToken` for pagination.

```typescript
const result = await client.send(new GetStatementResultV2Command({ Id }));
// result.Records[0].CSVRecords → "col1,col2\r\n1,hello\r\n2,world\r\n"
// result.ResultFormat → "CSV"
```

## Parameterized Queries

Use `:paramName` syntax to prevent SQL injection. Parameters replace **values only** — not column names, table names, or aggregate functions.

```typescript
await client.send(new ExecuteStatementCommand({
  ClusterIdentifier: "my-cluster",
  Database: "dev",
  DbUser: "myuser",
  Sql: "SELECT * FROM exerp.person WHERE person_id = :id",
  Parameters: [
    { name: "id", value: "12345" },
  ],
}));
```

**What works:**
- WHERE values: `WHERE col = :val`
- INSERT values: `INSERT INTO t VALUES (:v1, :v2)`
- Type casting: `:val::smallint`
- Same parameter reused multiple times

**What does NOT work:**
- Column names: `SELECT :col` ✗
- Table names: `FROM :table` ✗
- Aggregate functions: `COUNT(:col)` ✗
- NULL values (interpreted as literal string "NULL") ✗
- Zero-length strings ✗

## Session Reuse

Maintain state across multiple queries (e.g., SET statements, temp tables):

```typescript
// First query — create session
const result1 = await client.send(new ExecuteStatementCommand({
  ClusterIdentifier: "my-cluster",
  Database: "dev",
  DbUser: "myuser",
  Sql: "SET timezone TO 'US/Eastern'",
  SessionKeepAliveSeconds: 300,
}));
const sessionId = result1.SessionId;

// Subsequent queries reuse the session
const result2 = await client.send(new ExecuteStatementCommand({
  SessionId: sessionId,
  Sql: "SELECT current_timestamp",
  SessionKeepAliveSeconds: 300,
}));
```

**Constraints:**
- Max session duration: 24 hours
- Only one query at a time per session (no parallel queries)
- Session auto-closes after `SessionKeepAliveSeconds` of inactivity

## Idempotency

Use `ClientToken` to ensure exactly-once execution (useful in retries):

```typescript
await client.send(new ExecuteStatementCommand({
  ClusterIdentifier: "my-cluster",
  Database: "dev",
  DbUser: "myuser",
  Sql: "INSERT INTO t VALUES (1, 'hello')",
  ClientToken: "unique-token-abc-123",
}));
```

AWS SDKs auto-generate `ClientToken` on retry. Only set manually in Step Functions or custom retry logic. Token expires after 8 hours.

## IAM Policy

### Minimum policy for Data API with temporary credentials (DbUser)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "redshift-data:ExecuteStatement",
        "redshift-data:BatchExecuteStatement",
        "redshift-data:CancelStatement",
        "redshift-data:DescribeStatement",
        "redshift-data:GetStatementResult",
        "redshift-data:ListStatements",
        "redshift-data:ListSchemas",
        "redshift-data:ListTables",
        "redshift-data:DescribeTable"
      ],
      "Resource": "arn:aws:redshift:us-east-1:ACCOUNT_ID:cluster:CLUSTER_NAME"
    },
    {
      "Effect": "Allow",
      "Action": "redshift:GetClusterCredentials",
      "Resource": "*"
    }
  ]
}
```

### With Secrets Manager instead of DbUser

Replace the `GetClusterCredentials` statement with:

```json
{
  "Effect": "Allow",
  "Action": "secretsmanager:GetSecretValue",
  "Resource": "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:SECRET_NAME"
}
```

### Cross-account access

If the Redshift cluster is in a different AWS account, the calling role needs `sts:AssumeRole` permission, and the target account needs a trust policy on its role.

## Limits

| Limit | Value |
|-------|-------|
| Max query duration | 24 hours |
| Max result size | 500 MB (compressed) |
| Max result row size | 64 KB per row |
| Max SQL statement size | 100 KB |
| Result retention | 24 hours |
| Max active queries per cluster | 500 |
| Max active sessions | 500 |
| ClientToken expiration | 8 hours |

## Troubleshooting

### "Packet for query is too large"
A single row exceeds the 64KB per-row limit. Reduce the number of columns or use `SUBSTRING`/`LEFT` on large text columns.

### "Database response exceeded size limit"
Total result set exceeds 500MB. Add `LIMIT` clauses or paginate with `LIMIT`/`OFFSET`:
```sql
SELECT * FROM big_table LIMIT 1000 OFFSET 0;
SELECT * FROM big_table LIMIT 1000 OFFSET 1000;
```

### Query stuck in SUBMITTED/STARTED
Check `DescribeStatement` for status. Max 500 active queries per cluster — if at capacity, queries queue. Use `CancelStatement` to free slots.

### "ERROR: relation does not exist"
The `DbUser` may not have access to that schema/table. Some system tables (e.g., `stl_query_summary`) are only accessible to superusers.

### Statement FAILED with no results
Always check `DescribeStatement` before `GetStatementResult`. Calling `GetStatementResult` on a non-FINISHED statement throws `ResourceNotFoundException`.

## Helper: Poll Until Done

Reusable utility for the async pattern:

```typescript
async function waitForStatement(
  client: RedshiftDataClient,
  statementId: string,
  timeoutMs = 30_000,
): Promise<void> {
  const start = Date.now();
  while (true) {
    const desc = await client.send(
      new DescribeStatementCommand({ Id: statementId }),
    );
    if (desc.Status === "FINISHED") return;
    if (desc.Status === "FAILED") {
      throw new Error(`Redshift query failed: ${desc.Error}`);
    }
    if (desc.Status === "ABORTED") {
      throw new Error("Redshift query was aborted");
    }
    if (Date.now() - start > timeoutMs) {
      await client.send(new CancelStatementCommand({ Id: statementId }));
      throw new Error(`Redshift query timed out after ${timeoutMs}ms`);
    }
    await new Promise(r => setTimeout(r, 500));
  }
}
```

## Helper: Parse Records to Objects

Convert the typed-value format into plain JS objects:

```typescript
import type { ColumnMetadata, Field } from "@aws-sdk/client-redshift-data";

function parseRecords(
  records: Field[][],
  columns: ColumnMetadata[],
): Record<string, unknown>[] {
  return records.map(row =>
    Object.fromEntries(
      row.map((field, i) => [
        columns[i].name,
        field.longValue ?? field.stringValue ?? field.doubleValue ??
        field.booleanValue ?? (field.isNull ? null : field.blobValue),
      ]),
    ),
  );
}
```
