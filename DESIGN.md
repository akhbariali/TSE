---
name: TSE Market Archive
description: An inspectable market history with original reports close to the analysis.
colors:
  blue: "#2248a5"
  blue-dark: "#183780"
  blue-soft: "#edf2ff"
  ink: "#202c43"
  muted: "#5d6c82"
  line: "#dce3ee"
  ground: "#f3f6fb"
  paper: "#fff"
  positive: "#137465"
  positive-soft: "#e7f4f0"
  negative: "#ac493d"
  negative-soft: "#faeeea"
  amber: "#815b12"
  amber-soft: "#faf1dc"
typography:
  headline:
    fontFamily: 'Arial, "Noto Sans Arabic", Tahoma, sans-serif'
    fontSize: "27px"
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: "-0.025em"
  title:
    fontFamily: 'Arial, "Noto Sans Arabic", Tahoma, sans-serif'
    fontSize: "17px"
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "-0.015em"
  body:
    fontFamily: 'Arial, "Noto Sans Arabic", Tahoma, sans-serif'
    fontSize: "14px"
    lineHeight: 1.5
  table:
    fontFamily: 'Arial, "Noto Sans Arabic", Tahoma, sans-serif'
    fontSize: "12px"
    lineHeight: 1.5
  label:
    fontFamily: 'Arial, "Noto Sans Arabic", Tahoma, sans-serif'
    fontSize: "11px"
    fontWeight: 600
    lineHeight: 1.5
rounded:
  panel: "12px"
  navigation: "7px"
  button: "6px"
  field: "5px"
  badge: "4px"
spacing:
  compact: "6px"
  control-gap: "8px"
  small: "12px"
  regular: "16px"
  panel: "20px"
  section: "22px"
  wide: "24px"
  desktop-gutter: "34px"
components:
  button-primary:
    backgroundColor: "{colors.blue}"
    textColor: "{colors.paper}"
    rounded: "{rounded.button}"
    padding: "8px 14px"
    typography: "{typography.table}"
  button-primary-hover:
    backgroundColor: "{colors.blue-dark}"
  button-secondary:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.button}"
    padding: "8px 14px"
  button-secondary-hover:
    backgroundColor: "{colors.blue-soft}"
  button-link:
    textColor: "{colors.blue}"
    padding: "8px 0"
  input:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.field}"
    padding: "6px 10px"
  panel:
    backgroundColor: "{colors.paper}"
    rounded: "{rounded.panel}"
  badge-ready:
    backgroundColor: "{colors.positive-soft}"
    textColor: "{colors.positive}"
    rounded: "{rounded.badge}"
    padding: "3px 7px"
  badge-warning:
    backgroundColor: "{colors.amber-soft}"
    textColor: "{colors.amber}"
    rounded: "{rounded.badge}"
    padding: "3px 7px"
---
# Design System: TSE Market Archive

## Overview

**Creative North Star: "Inspectable market history"**

A statistical atlas translated into a working research app: cobalt navigation frames a cool, near-white workspace, while white work areas keep charts, exact-symbol tables, and source actions readable. The atmosphere is calm, compact, and factual.

Hierarchy comes from typography, aligned measurements, thin separators, and restrained tonal changes. Teal and brick carry transfer direction; amber carries analysis warnings. Persian symbol labels and Solar Hijri dates remain intact within the current English interface. The language choice is provisional, not a permanent visual identity commitment.

**Key Characteristics:**

- Compact research typography with tabular measurements.
- Cobalt navigation and cool paper work areas.
- Semantic transfer colors with signed values and explicit labels.
- Flat bordered containers and visible keyboard focus.

## Colors

The palette pairs statistical-atlas cobalt with cool neutrals and explicit data-state colors. Frontmatter records the canonical CSS custom-property values from `web/static/style.css`.

### Primary

- **Atlas cobalt** (`blue`): navigation shell, primary actions, links, active tabs, chart selection, and cumulative series.
- **Deep cobalt** (`blue-dark`): primary-action hover and blue notice text.
- **Pale cobalt** (`blue-soft`): informational notices and secondary-action hover.

### Secondary

- **Transfer teal** (`positive`) and **teal wash** (`positive-soft`): positive transfers, buying bars, and validated-status badges.
- **Transfer brick** (`negative`) and **brick wash** (`negative-soft`): negative transfers, selling bars, and errors.
- **Archive amber** (`amber`) and **amber wash** (`amber-soft`): reconciliation warnings and unavailable analysis.

### Neutral

- **Deep ink** (`ink`): main text and transient message backgrounds.
- **Slate** (`muted`): context, labels, units, chart axes, and secondary text.
- **Cool rule** (`line`): panel outlines, dividers, and tracks.
- **Workspace mist** (`ground`): page background and quiet inset controls.
- **White paper** (`paper`): work areas, inputs, and selected navigation.

**The Transfer Color Rule.** Teal and brick describe the direction of ownership transfers; signed values and labels accompany them.

## Typography

The system uses Arial with Noto Sans Arabic, Tahoma, and generic sans-serif fallbacks. No web fonts are bundled or fetched. Chart labels use the narrower Arial/Tahoma/sans-serif stack. There is no separate display face or monospace family.

- **Headline:** page titles use the frontmatter headline role; small screens reduce them to (24px).
- **Title:** section headings use the title role; smaller subheadings use (14px, weight 600).
- **Body:** the global body role establishes the base. Descriptions and methodology text use (13px), with methodology line height (1.8) and a maximum width of (80ch). Mobile methodology copy uses (12px).
- **Table:** compact data uses the table role; button text uses the same size with weight (600).
- **Label:** field labels and table headings use the label role. Secondary notes use (11px), usually regular weight.
- **Measurements:** summary metrics use (25px, weight 600, line height 1.4); narrow layouts use (23px). Dates and numeric data use tabular numerals. Numeric table columns align right.

## Layout

The desktop navigation rail is fixed at (212px), reducing to (190px) at widths of (1200px) or less. Main content is centered within a maximum width of (1600px), with desktop gutters (34px) and a top bar (70px) high. Desktop filters wrap as needed; summary metrics form four columns with vertical separators.

Chart and inspector share a bordered work area. The inspector occupies (260px), reducing to (225px) at the first compact breakpoint and becoming (240px) at tablet sizes. Methodology uses a wider reading column beside archive health; its column gap is (24px).

At (900px) or less, the rail becomes an ordinary horizontal header with horizontally scrollable navigation, and methodology stacks. At (650px) or less, page gutters become (16px), metrics become two columns, date fields share a row, and the inspector moves below the chart. Tables retain aligned columns inside horizontal overflow containers. The symbol-history table limits vertical height to (340px) and keeps its header sticky.

Charts fill their container and redraw on resize. Their ordinary chart height is (248px), increasing to (290px) above (1650px) and reducing to (225px) at the mobile breakpoint. Symbol history has a specific chart height of (235px), superseded by the mobile chart rule.

## Elevation & Depth

Ordinary work areas are flat: white surfaces, fine borders, a pale inspector background, and subtle table-row hover establish depth. Shadows are reserved for transient overlays: chart tooltips use `0 5px 16px #202c4322`; toast messages use `0 8px 28px #202c4329`.

**The Flat Work Area Rule.** Panels and filters use outlines and tonal contrast instead of ambient shadows.

## Shapes

Containers have gently curved corners; controls use smaller radii from the frontmatter. Borders are generally (1px). The rail's selected navigation item is a solid white rounded rectangle. Badges are compact rounded rectangles rather than pills; status dots are circles. Chart bars and small ratio tracks use slight corner rounding. The identity mark is a simple three-stroke bar motif implemented as inline SVG; no raster assets ship.

## Components

### Buttons

Compact, clearly actionable controls. Primary actions use cobalt and white; secondary actions use paper, ink, and a cool-rule border. Their default minimum height is (38px), with a small variant (33px). Link actions omit the border and underline on hover. Primary hover deepens cobalt; secondary hover adds pale cobalt and a stronger border. Disabled buttons use opacity (0.5) and a default cursor.

All keyboard-focusable controls share a (3px) blue outline (`#7198f1`) with an offset of (3px). There is no distinct general pressed-state treatment.

### Inputs / Fields

Labels sit above white bordered inputs, with a vertical gap of (6px). Fields have a minimum height of (36px), padding (6px 10px), and stroke `#cbd5e5`. Disabled date inputs use the workspace background and muted text. Focus uses the shared outline. Selects retain native dropdown behavior; range controls use cobalt as their accent.

### Navigation

Icon-and-label links sit on the cobalt rail. Inactive text is pale blue; hover adds a lighter cobalt surface. The current page is white with cobalt text and weight (600), indicated using `aria-current`. Mobile links stay in a single scrollable horizontal row; their icons disappear below the mobile breakpoint.

### Chips

Analysis-status badges pair concise text with semantic wash colors. Validated badges use teal; warning and unsupported badges use amber. Alternate revisions use a neutral wash. These badges describe file state and have no click or selection behavior.

### Cards / Containers

Panels and filters use white backgrounds, cool-rule borders, and the container radius. Section headings use padding (20px 22px 16px), becoming (18px 16px 14px) on mobile. Methodology and archive-health areas use more reading space. Tables meet panel edges; avoid adding independent rounded cells.

### Research Tables

Headers have a quiet tinted background; body rows use fine horizontal dividers and a subtle hover tint. Symbol buttons use cobalt and weight (600), and company labels preserve right-to-left direction. Numbers remain tabular. Search and sorting controls wrap above the table, while pagination sits below a separating rule.

### Transfer Chart and Inspector

The chart pairs a zero baseline, sparse grid, semantic bars or a cobalt series, a dotted selected-date marker, and a native range scrubber. The selected report inspector presents the date, measurements, breadth track, and original workbook action together. Hover tooltips use ink surfaces with white text. Preserve the meaning of this pairing when adding chart modes.

Motion is restrained and conditional on `prefers-reduced-motion: no-preference`: navigation backgrounds transition (140ms ease-out), breadth segments (280ms cubic-bezier(.16,1,.3,1)), and notices reveal via clipping (250ms with the same curve). Symbol-history scrolling also respects reduced motion. No decorative continuous animation is present.

## Do's and Don'ts

### Do:

- **Do** keep date range, instrument scope, and units close to measurements.
- **Do** use tabular numerals and right alignment for numeric table columns.
- **Do** preserve Persian labels and exact symbol suffixes with appropriate text direction.
- **Do** keep source downloads and analysis-status labels visible.
- **Do** let tables scroll horizontally while the surrounding workspace fits the viewport.

### Don't:

- **Don't** reuse teal and brick as arbitrary decorative accents.
- **Don't** replace aligned table values with decorative cards.
- **Don't** rely on color alone to communicate transfer direction or analysis status.
- **Don't** introduce ambient shadows on ordinary panels.
