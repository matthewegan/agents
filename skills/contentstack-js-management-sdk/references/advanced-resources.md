# Advanced Resources Reference

Detailed patterns for resources that go beyond basic CRUD.

## Table of Contents

- [Branches & Merging](#branches--merging)
- [Releases](#releases)
- [Workflows & Publish Rules](#workflows--publish-rules)
- [Taxonomies & Terms](#taxonomies--terms)
- [Bulk Operations](#bulk-operations)
- [Environments](#environments)
- [Locales](#locales)
- [Webhooks](#webhooks)
- [Variants & Variant Groups](#variants--variant-groups)

---

## Branches & Merging

### Create a branch

```javascript
const branch = await stack.branch().create({
  branch: {
    uid: 'feature-branch',
    source: 'main'
  }
})
```

### Compare branches

```javascript
const comparison = await stack.branch('feature-branch').compare('main')
```

### Merge branches

```javascript
await stack.branch().merge(
  {
    item_merge_strategies: [
      { uid: 'content_type_uid', type: 'content_type', merge_strategy: 'merge_prefer_compare' }
    ]
  },
  {
    base_branch: 'main',
    compare_branch: 'feature-branch',
    default_merge_strategy: 'merge_prefer_base',
    merge_comment: 'Merging feature into main',
    no_revert: false
  }
)
```

**Merge strategies**: `merge_prefer_base`, `merge_prefer_compare`, `overwrite_with_compare`, `merge_new_only`, `merge_modified_only_prefer_base`, `merge_modified_only_prefer_compare`, `ignore`.

### Merge queue

```javascript
const queue = await stack.branch().mergeQueue().fetchAll()
const job = await stack.branch().mergeQueue('merge_job_uid').fetch()
```

### Branch aliases

```javascript
await stack.branchAlias().create({ branch_alias: { uid: 'release', target_branch: 'main' } })
const alias = await stack.branchAlias('release').fetch()
```

---

## Releases

### Create and manage releases

```javascript
const release = await stack.release().create({
  release: {
    name: 'Q1 Launch',
    description: 'Q1 content release',
    locked: false,
    archived: false
  }
})

// Add items to release
await stack.release('release_uid').item().create({
  items: [
    { uid: 'entry_uid', version: 1, locale: 'en-us', content_type_uid: 'blog_post', action: 'publish' },
    { uid: 'asset_uid', version: 1, locale: 'en-us', content_type_uid: 'built_io_upload', action: 'publish' }
  ]
})

// List release items
const items = await stack.release('release_uid').item().findAll()

// Delete items from release
await stack.release('release_uid').item().delete({
  items: [{ uid: 'entry_uid', locale: 'en-us', version: 1, content_type_uid: 'blog_post', action: 'publish' }]
})

// Move items between releases
await stack.release('release_uid').item().move({
  param: {
    release_uid: 'target_release_uid',
    items: [{ uid: 'entry_uid', locale: 'en-us', version: 1, content_type_uid: 'blog_post', action: 'publish' }]
  }
})
```

### Deploy a release

```javascript
await stack.release('release_uid').deploy({
  environments: ['production'],
  locales: ['en-us'],
  scheduledAt: '2024-12-01T00:00:00Z',
  action: 'publish' // or 'unpublish'
})
```

### Clone a release

```javascript
const cloned = await stack.release('release_uid').clone({
  name: 'Q1 Launch Copy',
  description: 'Cloned release'
})
```

---

## Workflows & Publish Rules

### Create a workflow

```javascript
const workflow = await stack.workflow().create({
  workflow: {
    name: 'Editorial Workflow',
    enabled: true,
    content_types: ['blog_post', 'article'],
    workflow_stages: [
      {
        name: 'Draft',
        allStages: false, allUsers: true,
        specificStages: false, specificUsers: false,
        entry_lock: '$none',
        color: '#2196f3'
      },
      {
        name: 'Review',
        allStages: false, allUsers: false,
        specificStages: true, specificUsers: true,
        entry_lock: '$none',
        color: '#ff9800',
        next_available_stages: ['stage_uid_publish']
      }
    ]
  }
})
```

### Publish rules

```javascript
// List publish rules
const rules = await stack.workflow().publishRule().fetchAll()

// Get specific publish rule
const rule = await stack.workflow().publishRule('rule_uid').fetch()
```

### Move entry through workflow

```javascript
await stack.contentType('blog_post').entry('entry_uid').setWorkflowStage({
  workflow_stage: {
    uid: 'review_stage_uid',
    comment: 'Ready for review',
    due_date: '2024-12-01',
    notify: true,
    assign_to: [{ uid: 'user_uid', name: 'Reviewer', email: 'reviewer@example.com' }]
  }
})
```

---

## Taxonomies & Terms

### Create taxonomy

```javascript
const taxonomy = await stack.taxonomy().create({
  taxonomy: {
    name: 'Categories',
    uid: 'categories',
    description: 'Content categories'
  }
})
```

### Manage terms

```javascript
// Create term
await stack.taxonomy('categories').terms().create({
  term: { name: 'Technology', uid: 'technology' }
})

// Fetch term
const term = await stack.taxonomy('categories').terms('technology').fetch()

// Query terms
const terms = await stack.taxonomy('categories').terms().query().find()

// Update term
term.name = 'Tech'
await term.update()

// Delete term
await stack.taxonomy('categories').terms('technology').delete()
```

### Import / Export taxonomies

```javascript
// Export
const exported = await stack.taxonomy('categories').export()

// Import
await stack.taxonomy().import({ taxonomy: '/path/to/taxonomy.json' })
```

### Publish taxonomies

```javascript
await stack.taxonomy().publish({
  locales: ['en-us'],
  environments: ['production'],
  items: [{ uid: 'categories', term_uid: 'technology' }]
})
```

---

## Bulk Operations

### Bulk publish

```javascript
await stack.bulkOperation().publish({
  details: {
    entries: [
      { uid: 'entry1', _content_type_uid: 'blog_post' },
      { uid: 'entry2', _content_type_uid: 'blog_post' }
    ],
    locales: ['en-us'],
    environments: ['production']
  },
  skip_workflow_stage: false,
  approvals: true
})
```

### Bulk unpublish

```javascript
await stack.bulkOperation().unpublish({
  details: {
    entries: [{ uid: 'entry1', _content_type_uid: 'blog_post' }],
    locales: ['en-us'],
    environments: ['production']
  }
})
```

### Bulk delete

```javascript
await stack.bulkOperation().delete({
  entries: [{ uid: 'entry1', content_type: 'blog_post', locale: 'en-us' }],
  assets: [{ uid: 'asset1' }]
})
```

### Add/update items in bulk

```javascript
await stack.bulkOperation().addItems({ data: { /* bulk item data */ } })
await stack.bulkOperation().updateItems({ data: { /* bulk update data */ } })
```

### Check job status

```javascript
const status = await stack.bulkOperation().jobStatus({ job_id: 'job_uid' })
const items = await stack.bulkOperation().getJobItems('job_uid', {
  include_count: true,
  skip: 0,
  limit: 50
})
```

---

## Environments

```javascript
// Create
await stack.environment().create({
  environment: {
    name: 'staging',
    servers: [{ name: 'staging-server' }],
    urls: [{ locale: 'en-us', url: 'https://staging.example.com' }],
    deploy_content: true
  }
})

// Fetch / Query
const env = await stack.environment('staging').fetch()
const envs = await stack.environment().query().find()
```

---

## Locales

```javascript
// Create
await stack.locale().create({
  locale: {
    code: 'fr-fr',
    name: 'French (France)',
    fallback_locale: 'en-us'
  }
})

// Fetch / Query
const locale = await stack.locale('fr-fr').fetch()
const locales = await stack.locale().query().find()
```

---

## Webhooks

Webhooks use `fetchAll()` instead of `query().find()`.

```javascript
// Create
await stack.webhook().create({
  webhook: {
    name: 'Notify on publish',
    destinations: [{
      target_url: 'https://hooks.example.com/publish',
      custom_header: [{ header_name: 'X-Secret', value: 'abc123' }]
    }],
    channels: ['assets.create', 'content_types.entries.create'],
    retry_policy: 'manual',
    disabled: false
  }
})

// List all
const webhooks = await stack.webhook().fetchAll()

// View executions
const executions = await stack.webhook('webhook_uid').executions({})

// Retry failed execution
await stack.webhook('webhook_uid').retry('execution_uid')
```

---

## Variants & Variant Groups

### Variant groups

```javascript
const group = await stack.variantGroup().create({ /* variant group data */ })
const groups = await stack.variantGroup().query().find()
const group = await stack.variantGroup('group_uid').fetch()
```

### Variants within groups

```javascript
const variant = await stack.variantGroup('group_uid').variant().create({ /* variant data */ })
const variants = await stack.variantGroup('group_uid').variant().query().find()
```

### Entry variants

```javascript
const variants = await stack.contentType('ct_uid').entry('entry_uid').variants()
const variant = await stack.contentType('ct_uid').entry('entry_uid').variants('variant_uid')
```

### Stack-level variants

```javascript
const variants = await stack.variants()
const variant = await stack.variants('variant_uid')
```
