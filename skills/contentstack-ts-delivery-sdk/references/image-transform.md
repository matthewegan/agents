# Image Transformation API

The `ImageTransform` class provides chainable image manipulation methods. Apply transforms to an image URL using `.transform()`.

```typescript
import { ImageTransform, Format } from '@contentstack/delivery-sdk';

const transform = new ImageTransform()
  .resize({ width: 300, height: 200 })
  .quality(80)
  .format(Format.WEBP);

const transformedUrl = imageUrl.transform(transform);
```

## Methods

### resize(options)
Resize the image. Options: `width`, `height`, `disable` (e.g., `"upscale"`).

```typescript
new ImageTransform().resize({ width: 200, height: 200, disable: 'upscale' });
```

### crop(options)
Crop the image. Basic crop uses `width` and `height`. Advanced modes use `cropBy`:

```typescript
// Basic crop
new ImageTransform().crop({ width: 100, height: 200 });

// Aspect ratio
new ImageTransform().crop({ width: 2, height: 3, cropBy: CropBy.ASPECTRATIO });

// Region crop (from specific coordinates)
new ImageTransform().crop({ width: 200, height: 300, cropBy: CropBy.REGION, xval: 100, yval: 150 });

// Offset crop
new ImageTransform().crop({ width: 200, height: 300, cropBy: CropBy.OFFSET, xval: 100, yval: 150 });
```

### canvas(options)
Set canvas size. Optional `canvasBy` for offset mode:

```typescript
new ImageTransform().canvas({ width: 100, height: 200 });
new ImageTransform().canvas({ width: 200, height: 300, canvasBy: CanvasBy.OFFSET, xval: 100, yval: 150 });
```

### fit(fitBy)
Used with `resize()`. Values: `FitBy.BOUNDS`, etc.

```typescript
new ImageTransform().resize({ width: 200, height: 200 }).fit(FitBy.BOUNDS);
```

### dpr(ratio)
Device pixel ratio. Used with `resize()`:

```typescript
new ImageTransform().resize({ width: 300, height: 500 }).dpr(2);
```

### format(format)
Output format: `Format.PJPG`, `Format.WEBP`, `Format.GIF`, etc.

```typescript
new ImageTransform().format(Format.PJPG);
```

### quality(value)
JPEG/WebP quality (1-100):

```typescript
new ImageTransform().quality(80);
```

### auto()
Auto-optimize format and quality:

```typescript
new ImageTransform().auto();
```

### orient(orientation)
Rotate/flip: `Orientation.FLIP_HORIZONTAL`, `Orientation.FLIP_VERTICAL`, etc.

```typescript
new ImageTransform().orient(Orientation.FLIP_HORIZONTAL);
```

### overlay(options)
Add image overlay. Options: `relativeURL` (required), `align`, `repeat`, `width`.

```typescript
// Basic overlay
new ImageTransform().overlay({ relativeURL: overlayUrl });

// Positioned overlay
new ImageTransform().overlay({ relativeURL: overlayUrl, align: OverlayAlign.BOTTOM });

// Repeating overlay
new ImageTransform().overlay({
  relativeURL: overlayUrl,
  align: OverlayAlign.BOTTOM,
  repeat: OverlayRepeat.Y,
  width: '50p',
});
```

### blur(amount)
Gaussian blur (1-1000):

```typescript
new ImageTransform().blur(10);
```

### brightness(value)
Adjust brightness:

```typescript
new ImageTransform().brightness(80.5);
```

### contrast(value)
Adjust contrast:

```typescript
new ImageTransform().contrast(-80.99);
```

### saturation(value)
Adjust saturation:

```typescript
new ImageTransform().saturation(-80.99);
```

### sharpen(amount, radius, threshold)
Sharpen image:

```typescript
new ImageTransform().sharpen(5, 1000, 2);
```

### frame()
Extract first frame from animated GIFs:

```typescript
new ImageTransform().frame();
```

### bgColor(color)
Background color (hex without #):

```typescript
new ImageTransform().bgColor('cccccc');
```

### padding(values)
Padding as uniform value or [top, right, bottom, left]:

```typescript
new ImageTransform().padding(50);
new ImageTransform().padding([25, 50, 75, 90]);
```

### trim(values)
Trim as uniform value or array:

```typescript
new ImageTransform().trim(50);
new ImageTransform().trim([25, 50, 75, 90]);
```

### resizeFilter(filter)
Filter for resize: `ResizeFilter.NEAREST`, etc. Used with `resize()`:

```typescript
new ImageTransform().resize({ width: 500, height: 550 }).resizeFilter(ResizeFilter.NEAREST);
```

## Enums

All enums are importable from `@contentstack/delivery-sdk`:

- `CropBy`: `DEFAULT`, `ASPECTRATIO`, `REGION`, `OFFSET`
- `CanvasBy`: `DEFAULT`, `ASPECTRATIO`, `REGION`, `OFFSET`
- `FitBy`: `BOUNDS`, `CROP`
- `Format`: `GIF`, `PNG`, `JPG`, `PJPG`, `WEBP`, `WEBPLL`, `WEBPLY`
- `Orientation`: `DEFAULT` (1), `FLIP_HORIZONTAL` (2), `FLIP_HORIZONTAL_VERTICAL` (3), `FLIP_VERTICAL` (4), `FLIP_HORIZONTAL_LEFT` (5), `RIGHT` (6), `FLIP_HORIZONTAL_RIGHT` (7), `LEFT` (8)
- `OverlayAlign`: `TOP`, `BOTTOM`, `LEFT`, `RIGHT`, `MIDDLE`, `CENTER`
- `OverlayRepeat`: `X`, `Y`, `BOTH`
- `ResizeFilter`: `NEAREST`, `BILINEAR`, `BICUBIC`, `LANCZOS2`, `LANCZOS3`
