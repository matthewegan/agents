---
name: contentstack-ts-delivery-sdk
description: "Guide for writing correct code with the Contentstack TypeScript Delivery SDK (@contentstack/delivery-sdk). Use this skill whenever the user is working with Contentstack content delivery, importing from @contentstack/delivery-sdk, querying entries or assets from a Contentstack stack, or mentions Contentstack in the context of fetching/displaying content. Also trigger when you see contentstack.stack(), ContentType, BaseEntry, or other Contentstack SDK patterns in the codebase."
---

# Contentstack TypeScript Delivery SDK

This skill helps you write correct, idiomatic code using `@contentstack/delivery-sdk`. The SDK uses a fluent, chainable API where you build queries step by step and terminate them with `.fetch()` (single item) or `.find()` (collections).

## Key Concepts

- **Stack**: The root client. Created once with `apiKey`, `deliveryToken`, and `environment`.
- **ContentType → Entry**: Chain from stack to content type to entry. Use `.fetch()` for a single entry by UID, `.find()` for querying multiple.
- **Query**: Created via `.query()` on an entry collection. Provides filtering, sorting, and logical operators.
- **Asset**: Similar pattern to entries — `.asset(uid).fetch()` for one, `.asset().find()` for many.
- **Global Field**: `stack.globalField(uid).fetch()` for one, `stack.globalField().find()` for many.
- **Generics**: All `.fetch()` and `.find()` calls accept a type parameter (e.g., `fetch<BlogEntry>()`) for typed responses. Extend `BaseEntry` or `BaseAsset` for your types.

## Installation

```bash
npm i @contentstack/delivery-sdk
```

Requires Node.js 22+.

## Stack Initialization

```typescript
import contentstack, { Region, Policy } from '@contentstack/delivery-sdk';

const stack = contentstack.stack({
  apiKey: "apiKey",
  deliveryToken: "deliveryToken",
  environment: "environment_name",
  // Optional:
  region: Region.EU,           // Default is Region.US
  branch: "develop",           // For branch-specific content
  locale: "en-us",             // Default locale
  early_access: ["feature_1"], // Early access features
  logHandler: (level, data) => console.log(level, data),
});
```

Supported regions: `US` (default), `EU`, `AU`, `AZURE_NA`, `AZURE_EU`, `GCP_NA`, `GCP_EU`.

### Live Preview

```typescript
const stack = contentstack.stack({
  apiKey: "apiKey",
  deliveryToken: "deliveryToken",
  environment: "environment_name",
  live_preview: {
    enable: true,
    preview_token: "preview_token",
    host: "rest-preview.contentstack.com",
  },
});
```

### Plugins

Intercept requests and responses with the plugin system:

```typescript
import { ContentstackPlugin } from '@contentstack/delivery-sdk';

class LoggingPlugin implements ContentstackPlugin {
  onRequest(config: any) {
    console.log('Request:', config.url);
    return config;
  }
  onResponse(request: any, response: any, data: any) {
    console.log('Response:', response.status);
    return response;
  }
}

const stack = contentstack.stack({
  apiKey: "apiKey",
  deliveryToken: "deliveryToken",
  environment: "environment_name",
  plugins: [new LoggingPlugin()],
});
```

## Fetching Entries

### Single entry by UID

```typescript
import { BaseEntry } from '@contentstack/delivery-sdk';

interface BlogPost extends BaseEntry {
  title: string;
  body: string;
  author: string;
}

const entry = await stack
  .contentType("blog_post")
  .entry("entry_uid")
  .fetch<BlogPost>();
```

### Multiple entries

```typescript
const entries = await stack
  .contentType("blog_post")
  .entry()
  .find<BlogPost>();
```

### Entry modifiers (chainable before `.fetch()` or `.find()`)

| Method | Purpose |
|--------|---------|
| `.locale("en-us")` | Fetch in specific locale |
| `.includeBranch()` | Include branch info in response |
| `.includeFallback()` | Include fallback locale content |
| `.includeEmbeddedItems()` | Include embedded entries/assets |
| `.includeContentType()` | Include content type schema |
| `.includeReference("field")` | Resolve reference fields |
| `.includeMetadata()` | Include metadata |
| `.includeCount()` | Include total count in response |
| `.only("field")` | Return only specified fields |
| `.except("field")` | Exclude specified fields |
| `.variants("variant_uid")` | Fetch variant (string or string[]) |
| `.skip(n)` / `.limit(n)` | Pagination |
| `.orderByAscending(key)` / `.orderByDescending(key)` | Sort results |
| `.addParams({ key: "value" })` | Add arbitrary query parameters |
| `.param(key, value)` | Add single query parameter |
| `.removeParam(key)` | Remove a query parameter |

### Variants

Fetch content variants by UID or alias (alias preferred). You can layer multiple variants (up to 3 by default) — priority is based on the order added:

```typescript
// Single variant
const entry = await stack.contentType("blog_post").entry("uid").variants("variant_alias").fetch<BlogPost>();

// Multiple variants (layered, first takes priority)
const entry = await stack.contentType("blog_post").entry("uid").variants(["v1", "v2"]).fetch<BlogPost>();
```

## Querying with Conditions

For filtered queries, call `.query()` on the entry collection to get a Query object:

```typescript
const query = stack.contentType("blog_post").entry().query();
const results = await query
  .equalTo("status", "published")
  .limit(10)
  .find<BlogPost>();
```

### Query operations

**Comparison:**
- `.equalTo(field, value)` — exact match
- `.greaterThan(field, value)`, `.greaterThanOrEqualTo(field, value)`
- `.lessThan(field, value)`, `.lessThanOrEqualTo(field, value)`

**Inclusion:**
- `.containedIn(field, [values])` — field value is one of the given values
- `.notContainedIn(field, [values])` — field value is NOT one of the given values

**Existence:**
- `.exists(field)` / `.notExists(field)`

**Text:**
- `.regex(field, pattern, flags?)` — e.g., `.regex("title", "^Demo", "i")`
- `.search(keyword)` — full-text search

**References:**
- `.referenceIn(refField, subQuery)` — entries where referenced entries match subQuery
- `.referenceNotIn(refField, subQuery)` — inverse
- `.whereIn(field)` / `.whereNotIn(field)` — reference field inclusion

**Tags:**
- `.tags(["tag1", "tag2"])` — filter by tags

**Raw `where()`:**
```typescript
import { QueryOperation } from '@contentstack/delivery-sdk';
query.where("price", QueryOperation.IS_LESS_THAN, 100);
```

`QueryOperation` enum values: `EQUALS`, `NOT_EQUALS`, `INCLUDES`, `EXCLUDES`, `IS_LESS_THAN`, `IS_LESS_THAN_OR_EQUAL`, `IS_GREATER_THAN`, `IS_GREATER_THAN_OR_EQUAL`, `EXISTS`, `MATCHES`.

### Query utility methods

```typescript
query.addParams({ include_workflow: true, include_publish_details: true });
query.addQuery("key", "value");
query.param("key", "value");
query.removeParam("key");
const raw = query.getQuery(); // retrieve the raw query object
```

### Logical operators (combining queries)

```typescript
const q1 = stack.contentType("product").entry().query()
  .containedIn("category", ["electronics"]);
const q2 = stack.contentType("product").entry().query()
  .where("price", QueryOperation.EQUALS, 99);

// OR
const results = await stack.contentType("product").entry().query()
  .or(q1, q2)
  .find<Product>();

// AND
const results = await stack.contentType("product").entry().query()
  .and(q1, q2)
  .find<Product>();

// queryOperator for explicit control
import { QueryOperator } from '@contentstack/delivery-sdk';
query.queryOperator(QueryOperator.AND, subQuery1, subQuery2);
```

## Pagination

```typescript
const query = stack.contentType("blog_post").entry().query();

// First page (default skip=0, limit=10)
const page1 = await query.paginate().find<BlogPost>();

// Custom pagination
const page = await query.paginate({ skip: 20, limit: 20 }).find<BlogPost>();

// Navigate
const nextPage = await query.next().find<BlogPost>();
const prevPage = await query.previous().find<BlogPost>();
```

## Assets

```typescript
import { BaseAsset } from '@contentstack/delivery-sdk';

interface MyAsset extends BaseAsset {}

// Single asset
const asset = await stack.asset("asset_uid").fetch<MyAsset>();

// All assets
const assets = await stack.asset().find<MyAsset>();

// With modifiers
const asset = await stack
  .asset("asset_uid")
  .includeDimension()
  .includeBranch()
  .includeMetadata()
  .relativeUrls()
  .locale("en-us")
  .version(1)
  .fetch<MyAsset>();

// Asset collection queries (supports same filtering as entries)
const assets = await stack.asset()
  .where("file_size", QueryOperation.IS_GREATER_THAN, "1000")
  .limit(10)
  .skip(5)
  .includeCount()
  .includeMetadata()
  .orderByAscending("created_at")
  .find<MyAsset>();
```

## Global Fields

```typescript
import { BaseGlobalField } from '@contentstack/delivery-sdk';

// Fetch a single global field
const field = await stack.globalField("seo_fields").fetch<BaseGlobalField>();

// List all global fields
const fields = await stack.globalField().find<BaseGlobalField>();

// With branch info
const field = await stack.globalField("seo_fields").includeBranch().fetch<BaseGlobalField>();
```

## Taxonomy Queries

```typescript
import { TaxonomyQueryOperation } from '@contentstack/delivery-sdk';

// Using where() with TaxonomyQueryOperation
const entries = await stack
  .taxonomy()
  .where("taxonomies.category", TaxonomyQueryOperation.EQ_BELOW, "electronics", { levels: 2 })
  .find<Product>();
```

Convenience methods (same as `where()` with the corresponding operation):
- `.equalAndBelow(key, value, levels?)` — term and its descendants
- `.below(key, value, levels?)` — descendants only
- `.equalAndAbove(key, value, levels?)` — term and its ancestors
- `.above(key, value, levels?)` — ancestors only

Operations: `EQ_BELOW`, `BELOW`, `EQ_ABOVE`, `ABOVE`. The `levels` option controls depth.

## Content Type Schema

```typescript
// Fetch a single content type's schema
const schema = await stack.contentType("blog_post").fetch<BaseContentType>();

// List all content types
const types = await stack.contentType().find<BaseContentType>();

// Include global field schemas
const types = await stack.contentType()
  .includeGlobalFieldSchema()
  .find<BaseContentType>();
```

## Sync

For keeping local content in sync with Contentstack:

```typescript
// Initial sync
const response = await stack.sync();

// Recursive sync (fetches all pages automatically)
const response = await stack.sync({}, true);

// Filtered sync
await stack.sync({ locale: "en-us" });
await stack.sync({ contentTypeUid: "blog_post" });
await stack.sync({ startDate: "2024-01-01" });
await stack.sync({ type: "entry_published" });

// Subsequent syncs using tokens
await stack.sync({ paginationToken: "<token>" });
await stack.sync({ syncToken: "<token>" });
```

Sync type values: `entry_published`, `entry_unpublished`, `entry_deleted`, `asset_published`, `asset_unpublished`, `asset_deleted`, `content_type_deleted`.

## Image Transformations

For the full image transformation API (resize, crop, overlay, format conversion, etc.), see `references/image-transform.md`.

## Cache Policies

```typescript
import contentstack, { Policy } from '@contentstack/delivery-sdk';

const stack = contentstack.stack({
  apiKey: "apiKey",
  deliveryToken: "deliveryToken",
  environment: "environment",
  cacheOptions: {
    policy: Policy.CACHE_ELSE_NETWORK,
    persistenceStore: myStore,  // implements PersistenceStore interface
    maxAge: 86400000,           // TTL in milliseconds (default 24hrs)
  }
});
```

The `PersistenceStore` interface requires `setItem(key, value, contentTypeUid?, maxAge?)` and `getItem(key, contentTypeUid?)`. Use `@contentstack/persistence-plugin` or provide a custom implementation.

| Policy | Behavior |
|--------|----------|
| `Policy.IGNORE_CACHE` | Always fetch from network (default) |
| `Policy.CACHE_ELSE_NETWORK` | Try cache first, fall back to network |
| `Policy.NETWORK_ELSE_CACHE` | Try network first, fall back to cache |
| `Policy.CACHE_THEN_NETWORK` | Return cache immediately, then update from network |

## Common Patterns

### Fetch entries with resolved references

```typescript
const posts = await stack
  .contentType("blog_post")
  .entry()
  .includeReference("author")
  .includeReference("categories")
  .find<BlogPost>();
```

### Type-safe entry interfaces

Always extend `BaseEntry` for entries and `BaseAsset` for assets:

```typescript
import { BaseEntry, BaseAsset } from '@contentstack/delivery-sdk';

interface Author extends BaseEntry {
  name: string;
  bio: string;
  avatar: BaseAsset;
}

interface BlogPost extends BaseEntry {
  title: string;
  slug: string;
  body: string;
  author: Author[];  // reference fields are arrays
  featured_image: BaseAsset;
  tags: string[];
}
```

### Set locale globally vs per-query

```typescript
// Global — applies to all subsequent queries
stack.setLocale("en-us");

// Per-query — overrides global
const entry = await stack
  .contentType("blog_post")
  .entry("uid")
  .locale("fr-fr")
  .fetch<BlogPost>();
```

## Gotchas

- **URL size limit**: Query URLs must stay under 8KB or you'll get a 400 error. If you have many filter values, consider breaking into multiple queries.
- **Single content type per query**: You cannot query across multiple content types in one call.
- **`.fetch()` vs `.find()`**: `.fetch()` is for a single item by UID and returns the item directly. `.find()` is for collections and returns an array.
- **`.query()` placement**: Call `.query()` on the entry collection (not on a single entry) to get filtering capabilities.
- **Cache requires a persistence store**: Setting any policy other than `IGNORE_CACHE` requires providing a `persistenceStore` implementation — there is no built-in in-memory store.
- **Sync field names are camelCase**: Use `contentTypeUid`, `startDate`, `paginationToken`, `syncToken` (not snake_case).
