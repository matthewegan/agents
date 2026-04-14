---
name: tailwindcss-v4
description: "Tailwind CSS v4 reference for writing correct, idiomatic Tailwind v4 code. Use this skill whenever the user is working with Tailwind CSS — whether they're styling components, configuring themes, writing custom utilities, setting up a Tailwind project, or asking about Tailwind classes, directives, or configuration. Also use it when editing CSS files that contain @import 'tailwindcss', @theme, @utility, @variant, or other Tailwind v4 directives, even if the user doesn't explicitly mention Tailwind."
---

# Tailwind CSS v4

Tailwind CSS v4 is a major release that moves configuration from JavaScript (`tailwind.config.js`) into CSS. Design tokens are now CSS custom properties defined with `@theme`, and new directives like `@utility` and `@variant` replace much of what previously required plugins or config files.

This skill covers the v4-specific syntax and patterns. For the full utility class reference (flex, grid, spacing, typography, etc.), rely on your training data — the class names themselves haven't changed. What *has* changed is how you configure, extend, and customize Tailwind.

## Quick reference: What changed in v4

| v3 | v4 |
|---|---|
| `@tailwind base; @tailwind components; @tailwind utilities;` | `@import "tailwindcss";` |
| `tailwind.config.js` theme/extend | `@theme { }` block in CSS |
| `plugins: [...]` in config | `@plugin "package-name";` in CSS |
| `content: [...]` in config | Automatic detection + `@source` directive |
| Custom utilities via plugin API | `@utility` directive in CSS |
| Custom variants via plugin API | `@custom-variant` directive in CSS |
| `theme()` function | `--theme()` function (or just `var()` since tokens are CSS variables) |
| `screen()` function | `--theme(--breakpoint-*)` |

## Entry point

Every Tailwind v4 project starts with a single CSS import:

```css
@import "tailwindcss";
```

This replaces the three separate `@tailwind` directives from v3. You can also use subpath imports for finer control — see `references/directives.md` for details.

## Theme configuration with `@theme`

The `@theme` directive defines design tokens as CSS custom properties. These tokens power Tailwind's utility classes:

```css
@theme {
  --font-display: "Satoshi", "sans-serif";
  --color-primary: #3b82f6;
  --color-primary-light: #60a5fa;
  --breakpoint-3xl: 1920px;
  --ease-fluid: cubic-bezier(0.3, 0, 0, 1);
  --animate-spin-slow: spin 3s linear infinite;
}
```

Each variable you define here generates corresponding utility classes. `--color-primary: #3b82f6` gives you `bg-primary`, `text-primary`, `border-primary`, etc.

### Namespace conventions

Theme variables follow a namespace pattern that maps to utility classes. The key namespaces:

| Namespace | Example variable | Generated utilities |
|---|---|---|
| `--color-*` | `--color-brand: #e11d48;` | `bg-brand`, `text-brand`, `border-brand` |
| `--font-*` | `--font-heading: "Inter";` | `font-heading` |
| `--text-*` | `--text-tiny: 0.625rem;` | `text-tiny` |
| `--spacing-*` | `--spacing-18: 4.5rem;` | `m-18`, `p-18`, `gap-18`, `w-18`, etc. |
| `--breakpoint-*` | `--breakpoint-3xl: 1920px;` | `3xl:*` responsive variant |
| `--radius-*` | `--radius-pill: 9999px;` | `rounded-pill` |
| `--shadow-*` | `--shadow-soft: 0 2px 8px ...;` | `shadow-soft` |
| `--animate-*` | `--animate-fade: fade 0.3s ease;` | `animate-fade` |
| `--ease-*` | `--ease-spring: cubic-bezier(...);` | `ease-spring` |
| `--inset-shadow-*` | `--inset-shadow-sm: inset 0 1px ...;` | `inset-shadow-sm` |

For the full list of namespaces and default theme values, see `references/theme.md`.

### Overriding vs extending defaults

By default, variables in `@theme` **extend** the built-in defaults. To **replace** an entire namespace (remove all defaults for that group), use `--color-*: initial;` before defining your own:

```css
@theme {
  --color-*: initial;       /* clear all default colors */
  --color-primary: #3b82f6;
  --color-gray: #6b7280;
}
```

To override just the default values (keeping built-in ones you don't touch), use `@theme inline`:

```css
@theme inline {
  --color-primary: #3b82f6;  /* adds primary without generating extra CSS variables */
}
```

`inline` prevents Tailwind from emitting the variables in a `:root` block — useful when you want to reference them in utilities but don't need them as public API.

## Custom utilities with `@utility`

Define new utility classes directly in CSS:

```css
@utility tab-4 {
  tab-size: 4;
}
```

For utilities that support modifiers (like size values), use a functional form:

```css
@utility tab-* {
  tab-size: --value(--tab-*, integer);
}
```

This creates `tab-4`, `tab-8`, etc. based on `--tab-*` theme values, and also supports arbitrary values like `tab-[16]`.

## Custom variants with `@custom-variant`

```css
@custom-variant theme-dark (&:where([data-theme="dark"] *));

/* Shorthand for simple selectors: */
@custom-variant theme-dark {
  &:where([data-theme="dark"] *) {
    @slot;
  }
}
```

Use in HTML: `<div class="theme-dark:bg-black">`.

## Arbitrary values and properties

Same square-bracket syntax as v3, but now works everywhere:

```html
<!-- Arbitrary values -->
<div class="bg-[#1da1f2] top-[117px] grid-cols-[fit-content(theme(--breakpoint-sm))_auto]">

<!-- Arbitrary properties (for CSS properties without utility classes) -->
<div class="[mask-type:luminance] hover:[mask-type:alpha]">

<!-- Arbitrary variants -->
<div class="[@media(pointer:coarse)]:hidden">
```

## `@apply` directive

Works the same as v3 — inlines utility classes into custom CSS:

```css
.card {
  @apply rounded-lg bg-white p-6 shadow-md;
}
```

Use sparingly. It's best for styling things you don't control (third-party HTML) or for very common component patterns. Prefer utility classes in markup when possible.

## Source detection with `@source`

Tailwind v4 auto-detects your source files. If it misses some, use `@source`:

```css
@source "../node_modules/@my-company/ui/src/**/*.js";
```

To disable automatic detection entirely and go fully explicit:

```css
@source not "../legacy";  /* exclude a path */
```

## Colors

Colors are CSS variables now, which means you can reference them with `var()`:

```css
.custom-element {
  background: var(--color-blue-500);
}
```

Opacity modifier syntax: `bg-blue-500/75` applies 75% opacity. Works with any color utility.

For dark mode, use the `dark:` variant as before: `dark:bg-gray-900`.

## Preflight

Tailwind v4 includes a modern CSS reset (Preflight) that normalizes browser defaults. Key behaviors:
- Margins removed from all elements
- Headings and lists are unstyled
- Images are `display: block` and `max-width: 100%`
- Border defaults to `1px solid` using current color with 0 width

To extend Preflight, add styles in a `@layer base` block. To disable it:

```css
@import "tailwindcss" layer(utilities);  /* only utilities, no preflight */

/* Or exclude specific layers: */
@import "tailwindcss/preflight" source(none);  /* import but don't scan for classes */
```

## Functions

| Function | Purpose | Example |
|---|---|---|
| `--alpha(var, alpha)` | Set opacity on a color variable | `--alpha(var(--color-red-500), 50%)` |
| `--spacing(value)` | Resolve spacing scale value | `--spacing(4)` → `1rem` |
| `--theme(variable)` | Reference theme variable | `--theme(--breakpoint-sm)` → `640px` |

Use `--theme()` when you need theme values outside of property contexts where `var()` works (like inside `@media` queries).

## Further reference

For detailed documentation on specific topics, read the appropriate reference file:

- `references/directives.md` — All directives (`@import`, `@theme`, `@utility`, `@variant`, `@source`, `@apply`, `@reference`, `@plugin`, subpath imports)
- `references/theme.md` — Full namespace list, default theme variables, customization patterns, opacity modifiers
- `references/colors.md` — Default color palette, usage patterns, dark mode, CSS variable references, customizing colors
