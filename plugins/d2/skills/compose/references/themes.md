# D2 Themes

D2 themes are applied via the CLI `--theme` flag or the `D2_THEME` environment variable.

## Available Themes

### Light Themes

| ID | Name | Description |
|----|------|-------------|
| 0 | Neutral Default | Clean, neutral colors (default) |
| 1 | Neutral Grey | Grey-toned neutral palette |
| 3 | Flagship Terrastruct | Terrastruct brand colors |
| 4 | Cool Classics | Classic cool-toned palette |
| 5 | Mixed Berry Blue | Blue-purple mix |
| 6 | Grape Soda | Deep purple theme |
| 7 | Aubergine | Dark purple/eggplant |
| 8 | Colorblind Clear | Optimized for color vision deficiency |
| 100 | Vanilla Nitro Cola | Brown/tan warm tones |
| 101 | Orange Creamsicle | Orange warm tones |
| 102 | Shirley Temple | Pink/red tones |
| 103 | Earth Tones | Natural earthy colors |
| 104 | Everglade Green | Green forest palette |
| 105 | Buttered Toast | Warm yellow/brown |
| 300 | Terminal | Monospaced font, caps lock labels, no border radius, dot fill patterns |
| 301 | Terminal Grayscale | Terminal style in grayscale |
| 302 | Origami | Paper-folded aesthetic |
| 303 | C4 | C4 model style colors |

### Dark Themes

| ID | Name | Description |
|----|------|-------------|
| 200 | Dark Mauve | Dark purple/mauve background |
| 201 | Dark Flagship Terrastruct | Dark Terrastruct brand |

## Applying Themes

### Via CLI Flag

```bash
d2 --theme 6 input.d2 output.svg
```

### Via Environment Variable

```bash
D2_THEME=6 d2 input.d2 output.svg
```

### Dark Theme (Adaptive)

Set a dark theme that activates when the viewer's browser is in dark mode:

```bash
d2 --theme 0 --dark-theme 200 input.d2 output.svg
```

## Sketch Mode

For a hand-drawn look, use the `--sketch` flag:

```bash
d2 --sketch input.d2 output.svg
```

Sketch mode can be combined with any theme.

## Theme Overrides

Customize specific colors within a theme using D2 configuration variables:

- `theme-overrides`: Override colors for the light theme
- `dark-theme-overrides`: Override colors for the dark theme

Color codes used in themes: `N1`-`N7` (neutrals), `B1`-`B6` (blues), `AA2`/`AA4`/`AA5`, `AB4`/`AB5`

## User Request Mapping

| User says | Theme ID | Theme Name |
|-----------|----------|------------|
| "default", "neutral", "기본" | 0 | Neutral Default |
| "grey", "gray", "회색" | 1 | Neutral Grey |
| "purple", "grape", "보라색" | 6 | Grape Soda |
| "colorblind", "accessible", "접근성" | 8 | Colorblind Clear |
| "warm", "earth", "따뜻한" | 103 | Earth Tones |
| "green", "forest", "녹색" | 104 | Everglade Green |
| "terminal", "mono", "터미널" | 300 | Terminal |
| "C4" | 303 | C4 |
| "dark", "dark mode", "다크" | 200 | Dark Mauve |
| "sketch", "hand-drawn", "손그림" | Use `--sketch` flag with any theme |
| Custom colors | Use inline `style` properties |
