# Tailwind CSS v4 — Theme Variables

Theme variables are CSS custom properties defined in `@theme` blocks. They serve as the design tokens that power Tailwind's utility classes.

## How theme variables work

When you write:
```css
@theme {
  --color-brand: #e11d48;
}
```

Tailwind:
1. Emits `--color-brand: #e11d48;` in a `:root` rule (unless `@theme inline`)
2. Generates utilities: `bg-brand`, `text-brand`, `border-brand`, `ring-brand`, etc.

## Namespace reference

| Namespace | Utilities generated | Example |
|---|---|---|
| `--color-*` | `bg-*`, `text-*`, `border-*`, `ring-*`, `outline-*`, `shadow-*`, `accent-*`, `caret-*`, `fill-*`, `stroke-*`, `divide-*`, `decoration-*`, `placeholder-*` | `--color-brand: #e11d48;` → `bg-brand` |
| `--font-*` | `font-*` | `--font-display: "Inter";` → `font-display` |
| `--text-*` | `text-*` (font-size) | `--text-tiny: 0.625rem;` → `text-tiny` |
| `--font-weight-*` | `font-*` (weight) | `--font-weight-thick: 900;` → `font-thick` |
| `--tracking-*` | `tracking-*` | `--tracking-loose: 0.05em;` → `tracking-loose` |
| `--leading-*` | `leading-*` | `--leading-relaxed: 1.75;` → `leading-relaxed` |
| `--spacing-*` | `m-*`, `p-*`, `gap-*`, `w-*`, `h-*`, `size-*`, `inset-*`, `top/right/bottom/left-*`, `basis-*`, `translate-*`, `scroll-m/p-*`, `space-*` | `--spacing-18: 4.5rem;` → `p-18` |
| `--breakpoint-*` | Responsive variants (`sm:`, `md:`, etc.) | `--breakpoint-3xl: 1920px;` → `3xl:*` |
| `--radius-*` | `rounded-*` | `--radius-pill: 9999px;` → `rounded-pill` |
| `--shadow-*` | `shadow-*` | `--shadow-soft: 0 2px 8px ...;` → `shadow-soft` |
| `--inset-shadow-*` | `inset-shadow-*` | `--inset-shadow-sm: ...;` → `inset-shadow-sm` |
| `--drop-shadow-*` | `drop-shadow-*` | `--drop-shadow-glow: ...;` → `drop-shadow-glow` |
| `--animate-*` | `animate-*` | `--animate-fade: fade 0.3s ease;` → `animate-fade` |
| `--ease-*` | `ease-*` | `--ease-spring: cubic-bezier(...);` → `ease-spring` |
| `--blur-*` | `blur-*` | `--blur-xs: 2px;` → `blur-xs` |
| `--perspective-*` | `perspective-*` | `--perspective-near: 200px;` → `perspective-near` |
| `--aspect-*` | `aspect-*` | `--aspect-landscape: 4/3;` → `aspect-landscape` |
| `--container-*` | `@container` queries | `--container-3xl: 1920px;` |

## Default spacing scale

The default spacing scale in v4 is dynamic — `--spacing(n)` computes to `n * 0.25rem` for any numeric value, not just predefined steps. You can override this base:

```css
@theme {
  --spacing: 0.3rem;  /* changes the base multiplier */
}
```

Individual named values can also be added:
```css
@theme {
  --spacing-18: 4.5rem;
  --spacing-128: 32rem;
}
```

## Default breakpoints

| Variable | Value |
|---|---|
| `--breakpoint-sm` | `640px` |
| `--breakpoint-md` | `768px` |
| `--breakpoint-lg` | `1024px` |
| `--breakpoint-xl` | `1280px` |
| `--breakpoint-2xl` | `1536px` |

## Customization patterns

### Add new tokens alongside defaults

```css
@theme {
  --color-brand: #e11d48;
  --font-display: "Satoshi", sans-serif;
}
```

### Replace an entire namespace

```css
@theme {
  --color-*: initial;  /* remove all default colors */
  --color-primary: #3b82f6;
  --color-secondary: #10b981;
  --color-surface: #f8fafc;
  --color-on-surface: #0f172a;
}
```

### Override specific defaults

```css
@theme {
  --color-gray-50: #f8fafc;  /* override just gray-50 */
}
```

### Using inline theme

`@theme inline` prevents the variables from being emitted as `:root` CSS custom properties. The utilities still work, but downstream CSS won't see the variables:

```css
@theme inline {
  --color-primary: oklch(0.6 0.25 260);
}
```

## Referencing theme values in CSS

Since theme variables are CSS custom properties, reference them with `var()`:

```css
.banner {
  background: var(--color-blue-500);
  padding: var(--spacing-4, 1rem);
  font-family: var(--font-sans);
}
```

For media queries where `var()` isn't allowed, use `--theme()`:

```css
@media (width >= --theme(--breakpoint-lg)) {
  /* ... */
}
```

## Opacity modifiers on theme colors

Colors defined as theme variables support the `/` opacity modifier syntax automatically:

```html
<div class="bg-brand/50">  <!-- 50% opacity of --color-brand -->
```

This works because Tailwind internally handles color manipulation. You can use any percentage or fraction: `bg-brand/75`, `text-primary/30`, etc.
