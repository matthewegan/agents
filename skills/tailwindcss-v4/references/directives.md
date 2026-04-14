# Tailwind CSS v4 — Directives and Functions

## @import

The single entry point for Tailwind v4:

```css
@import "tailwindcss";
```

This replaces the v3 `@tailwind base/components/utilities` directives.

### Subpath imports

For granular control, import specific layers:

```css
@import "tailwindcss/preflight" layer(base);
@import "tailwindcss/theme" layer(theme);
@import "tailwindcss/utilities" layer(utilities);
```

This is useful when you need to interleave your own CSS layers or disable specific parts.

## @theme

Defines design tokens as CSS custom properties. Variables declared in `@theme` generate corresponding utility classes.

```css
@theme {
  --font-display: "Satoshi", "sans-serif";
  --color-primary: #3b82f6;
  --breakpoint-3xl: 1920px;
  --ease-fluid: cubic-bezier(0.3, 0, 0, 1);
}
```

### Clearing defaults

Use `initial` to remove all default values for a namespace before defining your own:

```css
@theme {
  --color-*: initial;
  --color-brand: #e11d48;
  --color-surface: #f8fafc;
}
```

### @theme inline

Prevents Tailwind from emitting variables in a `:root` block. The variables still work in utilities but aren't exposed as CSS custom properties on the page:

```css
@theme inline {
  --color-primary: oklch(0.6 0.25 260);
}
```

## @source

Tells Tailwind where to scan for class names. Tailwind v4 auto-detects source files in your project, but you can add additional paths:

```css
@source "../node_modules/@my-company/ui/src/**/*.js";
```

Exclude paths with `not`:

```css
@source not "../legacy";
```

Use `source(none)` on an import to include the CSS without scanning it for classes:

```css
@import "tailwindcss/preflight" source(none);
```

## @utility

Define custom utility classes. Simple (static) utilities:

```css
@utility content-auto {
  content-visibility: auto;
}
```

Functional utilities that accept values:

```css
@utility tab-* {
  tab-size: --value(--tab-*, integer);
}
```

The `--value()` function resolves the value from theme variables or arbitrary bracket notation. Type hints (`integer`, `length`, `color`, etc.) constrain what values are accepted.

## @variant

Apply an existing variant to a block of CSS:

```css
@variant dark {
  .my-component {
    background: black;
    color: white;
  }
}
```

## @custom-variant

Define entirely new variants:

```css
@custom-variant theme-dark (&:where([data-theme="dark"] *));
```

Or with the block syntax for complex selectors:

```css
@custom-variant theme-dark {
  &:where([data-theme="dark"] *) {
    @slot;
  }
}
```

The `@slot` marker indicates where the matched utility's styles should be placed.

## @apply

Inlines utility classes in custom CSS:

```css
.btn {
  @apply rounded-lg bg-blue-500 px-4 py-2 text-white font-semibold;
}
```

Works in `@layer` blocks and regular CSS. Use sparingly — utility classes in markup are preferred.

## @reference

Imports a stylesheet for reference only (type checking, IDE completions) without including its output in the build:

```css
@reference "../../app.css";
```

Useful in component CSS files that need to know about theme variables without duplicating them.

## @plugin

Load JavaScript plugins:

```css
@plugin "@tailwindcss/typography";
@plugin "./my-custom-plugin.js";
```

Replaces the `plugins: [...]` array from `tailwind.config.js`.

## Functions

### --alpha()

Sets the opacity of a color variable:

```css
.overlay {
  background: --alpha(var(--color-blue-500), 50%);
}
```

### --spacing()

Resolves a value from the spacing scale:

```css
.custom {
  margin: --spacing(4);  /* resolves to 1rem */
}
```

The spacing scale in v4 is derived dynamically — `--spacing(n)` = `n * 0.25rem` by default for any value, not just predefined steps.

### --theme()

References a theme variable. Mainly needed in contexts where `var()` doesn't work, like `@media` queries:

```css
@media (width >= --theme(--breakpoint-lg)) {
  /* ... */
}
```

In normal property contexts, prefer `var(--color-blue-500)` over `--theme(--color-blue-500)`.

## Compatibility

The `@utility` and `@custom-variant` directives are v4-only. Plugins written for v3's JavaScript API (`plugin()` function with `addUtilities`, `addVariant`, etc.) still work via `@plugin` but are considered legacy.

The `theme()` function (without the `--` prefix) from v3 is still supported for backwards compatibility but `--theme()` is preferred. The old `screen()` function is replaced by `--theme(--breakpoint-*)`.
