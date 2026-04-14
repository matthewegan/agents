---
name: contentstack-js-management-sdk
description: "Guide for writing correct code with the Contentstack JavaScript Content Management SDK (@contentstack/management). Use this skill whenever the user is creating, updating, deleting, or publishing content programmatically in Contentstack — importing from @contentstack/management, managing entries/assets/content types via code, writing migration scripts, building admin tools, or automating content workflows. Also trigger when you see contentstack.client(), management_token, authtoken in a Contentstack context, or any CRUD operations against Contentstack (as opposed to read-only delivery queries). This is the management/write SDK — for read-only content fetching, use the delivery SDK skill instead."
---

# Contentstack JavaScript Content Management SDK

This skill helps you write correct code using `@contentstack/management` — the SDK for creating, updating, deleting, and publishing content in Contentstack. Unlike the delivery SDK (read-only), this SDK provides full CRUD operations across all stack resources.

## Key Concepts

- **Client**: The root object. Created with an `authtoken`, or unauthenticated then paired with a management token on the stack.
- **Stack**: Access point for all resources. Obtained via `client.stack({ api_key, management_token?, branch_uid? })`.
- **Resource pattern**: `stack.resourceType()` returns a collection (query/create), `stack.resourceType(uid)` returns a single resource (fetch/update/delete).
- **CRUD interface**: Most resources support `.create()`, `.fetch()`, `.update()`, `.delete()`. Entries and assets additionally support `.publish()` and `.unpublish()`.
- **Promise-based**: All operations return promises — use `await` or `.then()`.

## Installation

```bash
npm i @contentstack/management
```

Requires Node.js 22+.

## Client Initialization & Authentication

There are three auth approaches. Pick one based on your use case.

### Authtoken (user-specific, read-write)

```javascript
import contentstack from '@contentstack/management'

const client = contentstack.client({ authtoken: 'YOUR_AUTHTOKEN' })
const stack = client.stack({ api_key: 'STACK_API_KEY' })
```

### Management Token (stack-scoped, no user attached)

```javascript
const client = contentstack.client()
const stack = client.stack({
  api_key: 'STACK_API_KEY',
  management_token: 'MGMT_TOKEN',
  branch_uid: 'main' // optional
})
```

### Login (email/password, with optional MFA)

```javascript
const client = contentstack.client()

// Without MFA
await client.login({ email: 'user@example.com', password: 'password' })

// With MFA (pass tfa_token or mfaSecret to auto-generate OTP)
await client.login({ email: 'user@example.com', password: 'password', tfa_token: '123456' })
```

### Region configuration

Set the `host` for non-NA regions. This takes priority over region selection:

| Region | Host |
|--------|------|
| NA (default) | `api.contentstack.io` |
| EU | `eu-api.contentstack.com` |
| AU | `au-api.contentstack.com` |
| Azure NA | `azure-na-api.contentstack.com` |
| Azure EU | `azure-eu-api.contentstack.com` |
| GCP NA | `gcp-na-api.contentstack.com` |

```javascript
const client = contentstack.client({ host: 'eu-api.contentstack.com' })
```

## Entries (CRUD + Publish)

The most commonly used resource. Chain from stack → contentType → entry.

### Create

```javascript
const entry = await stack
  .contentType('blog_post')
  .entry()
  .create({
    entry: {
      title: 'My Post',
      url: '/my-post',
      body: 'Content here...'
    }
  })
```

### Fetch single entry

```javascript
const entry = await stack
  .contentType('blog_post')
  .entry('entry_uid')
  .fetch()
```

### Query entries

```javascript
const entries = await stack
  .contentType('blog_post')
  .entry()
  .query({ include_count: true })
  .find()
```

### Update

Fetch first, modify, then update:

```javascript
const entry = await stack.contentType('blog_post').entry('entry_uid').fetch()
entry.title = 'Updated Title'
await entry.update()
```

### Delete

```javascript
await stack.contentType('blog_post').entry('entry_uid').delete()
```

### Publish / Unpublish

```javascript
await stack.contentType('blog_post').entry('entry_uid').publish({
  publishDetails: {
    locales: ['en-us'],
    environments: ['production']
  },
  locale: 'en-us',
  version: 1,          // optional: specific version
  scheduledAt: '2024-12-01T12:00:00Z' // optional: schedule
})

await stack.contentType('blog_post').entry('entry_uid').unpublish({
  publishDetails: {
    locales: ['en-us'],
    environments: ['production']
  }
})
```

### Set workflow stage

```javascript
await stack.contentType('blog_post').entry('entry_uid').setWorkflowStage({
  workflow_stage: {
    uid: 'stage_uid',
    comment: 'Moving to review'
  }
})
```

### Get entry locales and references

```javascript
const locales = await stack.contentType('blog_post').entry('entry_uid').locales()
const refs = await stack.contentType('blog_post').entry('entry_uid').references({})
```

### Import entries

```javascript
await stack.contentType('blog_post').entry().import({
  entry: '/path/to/entry.json',
  locale: 'en-us',
  overwrite: true
})
```

## Content Types

### Create

```javascript
const contentType = await stack.contentType().create({
  content_type: {
    title: 'Blog Post',
    uid: 'blog_post',
    schema: [
      { display_name: 'Title', uid: 'title', data_type: 'text', mandatory: true, unique: true },
      { display_name: 'URL', uid: 'url', data_type: 'text' },
      { display_name: 'Body', uid: 'body', data_type: 'text' }
    ],
    options: {
      is_page: true,
      singleton: false,
      title: 'title',
      sub_title: [],
      url_pattern: '/:title'
    }
  }
})
```

### Fetch / Query / Update / Delete

```javascript
const ct = await stack.contentType('blog_post').fetch()
const allTypes = await stack.contentType().query().find()

ct.title = 'Updated Blog Post'
await ct.update()

await stack.contentType('blog_post').delete()
```

### Import content types

```javascript
await stack.contentType().import({ content_type: '/path/to/content_type.json' })
```

### Generate UID from name

```javascript
const uid = stack.contentType().generateUid('Blog Post') // "blog_post"
```

## Assets

### Upload

```javascript
const asset = await stack.asset().create({
  upload: '/path/to/image.png',
  title: 'Hero Image',
  description: 'Homepage hero',
  tags: ['hero', 'homepage'],
  parent_uid: 'folder_uid' // optional: upload into folder
})
```

### Fetch / Query

```javascript
const asset = await stack.asset('asset_uid').fetch()
const assets = await stack.asset().query().find()
```

### Replace file

```javascript
const asset = await stack.asset('asset_uid').fetch()
await asset.replace({ upload: '/path/to/new-image.png' })
```

### Download

```javascript
await stack.asset('asset_uid').download({ responseType: 'stream' })
```

### Publish / Unpublish

Same pattern as entries:

```javascript
await stack.asset('asset_uid').publish({
  publishDetails: { locales: ['en-us'], environments: ['production'] }
})
```

### Asset folders

```javascript
// Create folder
await stack.asset().folder().create({ asset: { name: 'Images' } })

// Fetch folder
const folder = await stack.asset().folder('folder_uid').fetch()
```

## Stack Operations

```javascript
// Fetch stack details
const stackDetails = await stack.fetch()

// Update stack
stackDetails.name = 'New Stack Name'
await stackDetails.update()

// List users
const users = await stack.users()

// Share stack
await stack.share(['user@example.com'], { role_uid: 'role_uid' })

// Transfer ownership
await stack.transferOwnership('newowner@example.com')

// Stack settings
const settings = await stack.settings()
await stack.addSettings({ discrete_variables: { key: 'value' } })
await stack.resetSettings()
```

## Other Resources (Quick Reference)

All resources follow the same collection/singleton pattern: `stack.resource()` for collections, `stack.resource(uid)` for a single item. Collections support `.query().find()` and `.create()`. Singletons support `.fetch()`, `.update()`, `.delete()`.

| Resource | Collection | Singleton | Notes |
|----------|-----------|-----------|-------|
| `environment()` | query, create | fetch, update, delete | Deploy targets with server URLs |
| `locale()` | query, create | fetch, update, delete | Language/locale with fallback |
| `branch()` | query, create | fetch, update, delete | Also: `.compare(branchUid)`, merge |
| `branchAlias()` | query, create | fetch, update, delete | Alias pointing to a branch |
| `globalField()` | query, create | fetch, update, delete | Reusable field definitions |
| `webhook()` | create, fetchAll | fetch, update, delete | Also: `.executions()`, `.retry()` |
| `workflow()` | create, fetchAll | fetch, update, delete | Also: `.publishRule()` |
| `release()` | query, create | fetch, update, delete | Also: `.item()`, `.deploy()`, `.clone()` |
| `label()` | query, create | fetch, update, delete | Content labels |
| `role()` | query, create | fetch, update, delete | User roles/permissions |
| `deliveryToken()` | query, create | fetch, update, delete | |
| `managementToken()` | query, create | fetch, update, delete | |
| `extension()` | query, create | fetch, update, delete | Custom fields/widgets |
| `taxonomy()` | create, query | fetch, update, delete | Also: `.terms()`, `.export()`, `.import()` |

For detailed patterns on branches, releases, workflows, bulk operations, and taxonomies, see `references/advanced-resources.md`.

## Bulk Operations

For publishing, unpublishing, or deleting many items at once:

```javascript
await stack.bulkOperation().publish({
  details: {
    entries: [
      { uid: 'entry1_uid', _content_type_uid: 'blog_post' },
      { uid: 'entry2_uid', _content_type_uid: 'blog_post' }
    ],
    locales: ['en-us'],
    environments: ['production']
  }
})

await stack.bulkOperation().delete({
  entries: [{ uid: 'entry_uid', content_type: 'blog_post', locale: 'en-us' }]
})
```

## Common Patterns

### Migration script structure

```javascript
import contentstack from '@contentstack/management'

const client = contentstack.client({ authtoken: process.env.CS_AUTHTOKEN })
const stack = client.stack({ api_key: process.env.CS_API_KEY })

// Create content type
const ct = await stack.contentType().create({
  content_type: {
    title: 'Article',
    uid: 'article',
    schema: [
      { display_name: 'Title', uid: 'title', data_type: 'text', mandatory: true, unique: true },
      { display_name: 'Slug', uid: 'slug', data_type: 'text', mandatory: true },
      { display_name: 'Body', uid: 'body', data_type: 'text' }
    ],
    options: { is_page: true, singleton: false, title: 'title', sub_title: [] }
  }
})

// Create entries
for (const item of data) {
  await stack.contentType('article').entry().create({
    entry: { title: item.title, slug: item.slug, body: item.body }
  })
}
```

### Fetch-modify-update pattern

The SDK uses a mutable object pattern for updates. Always fetch first, then modify properties, then call `.update()`:

```javascript
const entry = await stack.contentType('blog_post').entry('uid').fetch()
entry.title = 'New Title'
entry.body = 'Updated body'
const updated = await entry.update()
```

Do not try to pass updated fields to `.update()` directly — modify the fetched object's properties instead.

### Query with pagination

```javascript
const result = await stack
  .contentType('blog_post')
  .entry()
  .query({ include_count: true, skip: 0, limit: 50 })
  .find()
```

## Gotchas

- **Delivery SDK vs Management SDK**: `@contentstack/delivery-sdk` is read-only with fluent query builders. `@contentstack/management` is CRUD with a different API shape. Don't mix patterns between them.
- **Fetch before update**: You must `.fetch()` an item before calling `.update()` — the SDK needs the full object state.
- **Management tokens are stack-scoped**: They can't access organization-level resources. Use authtokens for cross-stack operations.
- **Rate limits**: The CMA has a rate limit of 10 requests/second for read/write. Build in backoff for bulk operations.
- **Branch context**: When using `branch_uid` in the stack config, all operations target that branch. Omit it for the default branch.
- **Publish requires explicit locales and environments**: Unlike the delivery SDK where you set a global locale, publishing always requires you to specify which locales and environments.
- **Import paths**: `.import()` methods expect a file path string, not a parsed object.
- **Webhook/Workflow collections use `fetchAll()`**: Unlike most resources that use `.query().find()`, webhooks and workflows use `.fetchAll()` to list items.
