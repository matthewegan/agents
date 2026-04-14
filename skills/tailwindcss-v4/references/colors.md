# Tailwind CSS v4 — Colors

## Default color palette

Tailwind v4 includes the same expert-crafted color palette as v3, with shades from 50 (lightest) to 950 (darkest):

**Available color families:** red, orange, amber, yellow, lime, green, emerald, teal, cyan, sky, blue, indigo, violet, purple, fuchsia, pink, rose, slate, gray, zinc, neutral, stone

Plus: `black`, `white`, `transparent`, `current` (currentColor).

Each family has shades: 50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950.

## Using colors

Color utilities follow the pattern `{property}-{color}-{shade}`:

```html
<div class="bg-blue-500 text-white border-gray-200">
<p class="text-slate-700 decoration-rose-500">
```

Shorthand without shade uses the color directly (only for custom colors without shades):

```html
<div class="bg-brand text-on-brand">  <!-- uses --color-brand, --color-on-brand -->
```

## Opacity modifier

Append `/{opacity}` to any color utility:

```html
<div class="bg-blue-500/75">     <!-- 75% opacity -->
<div class="text-black/50">      <!-- 50% opacity -->
<div class="border-white/10">    <!-- 10% opacity -->
```

Works with percentages. Also works with arbitrary values: `bg-blue-500/[.06]`.

## Dark mode

Use the `dark:` variant:

```html
<div class="bg-white dark:bg-gray-900 text-gray-900 dark:text-white">
```

Dark mode is triggered by the `prefers-color-scheme: dark` media query by default. To use class-based dark mode, add a custom variant:

```css
@custom-variant dark (&:where(.dark *));
```

## Referencing colors in CSS

Colors are CSS custom properties, so use `var()`:

```css
.custom {
  background: var(--color-blue-500);
  border-color: var(--color-gray-200);
}
```

To apply opacity to a color variable in CSS, use `--alpha()`:

```css
.overlay {
  background: --alpha(var(--color-blue-500), 50%);
}
```

## Customizing colors

### Add custom colors

```css
@theme {
  --color-brand: #e11d48;
  --color-brand-light: #fb7185;
  --color-brand-dark: #9f1239;
}
```

Generates: `bg-brand`, `bg-brand-light`, `bg-brand-dark`, `text-brand`, etc.

### Replace all default colors

```css
@theme {
  --color-*: initial;
  --color-primary: #3b82f6;
  --color-secondary: #10b981;
  --color-danger: #ef4444;
  --color-surface: #ffffff;
  --color-on-surface: #1e293b;
}
```

### Override specific colors

```css
@theme {
  --color-gray-50: #f8fafc;
  --color-gray-100: #f1f5f9;
}
```

### Using modern color spaces

Tailwind v4 works with any CSS color format:

```css
@theme {
  --color-brand: oklch(0.6 0.25 260);
  --color-accent: hsl(340 82% 52%);
  --color-surface: color(display-p3 0.98 0.98 0.98);
}
```
