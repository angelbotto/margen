# Theme families, modes and typography

Appearance has independent family, light/dark/system mode and typography choices. Changing family preserves the selected mode; device changes affect only system mode. The compact browser offers search, category filtering, favorites and a scrollable list of previews. Sound controls stay in their own tab.

There are 16 families and 32 palettes. Preview swatches follow the effective mode. Linear is one family, not separate light/dark entries.

| Family ID | Modes |
| --- | --- |
| `editorial` | Light, dark, system |
| `sea` | Light, dark, system |
| `olive` | Light, dark, system |
| `clay` | Light, dark, system |
| `plum` | Light, dark, system |
| `liftit` | Light, dark, system |
| `tikin` | Light, dark, system |
| `catabum` | Light, dark, system |
| `kaira` | Light, dark, system |
| `blueprint` | Light, dark, system |
| `hacker` | Light, dark, system |
| `linear` | Light, dark, system |
| `modern` | Light, dark, system |
| `github` | Light, dark, system |
| `catppuccin` | Light, dark, system |
| `solarized` | Light, dark, system |

Six typography presets separate headings from body: Editorial (Instrument Serif/Geist), Sobrio (Geist/Geist), Técnico (Geist Mono/Geist), Libro (Literata/Literata), Revista (Instrument Serif/Literata), Bitácora (Geist Mono/Literata). Reenie Beanie is reserved for handwritten notes. Fonts are embedded with their licenses; code and controls retain their intended families.

Family sources live in `packages/core/themes/families/`; `scripts/themes.py` generates tokens, aliases and runtime metadata. Define complete light/dark tokens, preserve graph/chart states and run theme validation when adding a family. Do not put custom source CSS after the generated-theme marker. The catalog and counts are generated, not manually copied into the reader.

## Kaira

`kaira` adapts Kaira's modular-report palette, using only its initial design tokens: deep plum (`#180611`, `#290c24`, `#3b1233`), warm paper (`#fbf4e9`), ivory (`#fffaf2`) and gold (`#b78a38`, `#d9bd77`, `#f0dfaa`). No report content, logos, private assets or external resources are included. It is a color family in the brand category, not a new brand identity; Margen's layout, typography presets, controls, print behavior and component contracts remain unchanged.

Light mode uses paper, ivory panels and a warm inset surface (`#f3e7d6`). Its functional gold is darkened to `#805b1f`: the original `#b78a38` is retained only as the non-text `marca-acento` reference, not as a body/link/focus color. Dark mode uses the three plum surfaces, ivory primary text, pale-gold secondary text and `#d9bd77` for the functional accent. Adapted green, red and blue semantic colors keep states distinct without using gold for every series.

All seven text/semantic colors meet WCAG AA for normal text (4.5:1) on each of the three surfaces in each mode. The minimum ratios are **4.5311:1** in light mode (muted text on the inset surface) and **7.6051:1** in dark mode (red on the inset surface). Functional gold is at least **5.0122:1** light and **8.7070:1** dark. The generator supplies the existing chart, heatmap, selection, table, focus, annotation and appearance tokens; `node scripts/test_themes.cjs` checks registration, generated CSS, all 42 text/surface pairs, heatmap labels, table selections and runtime mode persistence. These checks measure colors and runtime behavior, not screen-reader or human visual certification.

Choose `theme='kaira', mode='light'` (or `dark` / `system`) through the Python artifact API; CLI equivalents are `--tema kaira --modo light`. The TypeScript token API uses `getThemeTokens('kaira', 'light')` after generating core data with `python3 scripts/build_core.py`.

Preferences are scoped by origin or artifact defaults as documented by the reader. Without storage, controls still work for the session. System mode follows the device; embedded prototypes are independent documents. Paper grain is optional and removed for print. Editor and Linear themes are adaptations, not official integrations.

See [brand identity](brands.md), [contributing components](contributing-components.md) and [the runnable theme guide](../examples/generated/themes.html).
