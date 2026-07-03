# SARP UX and Visual Design System

## Design objective

SARP is an internal security operations tool. It should feel reliable, calm and efficient rather than flashy, technical for its own sake, or overly designed.

The user should be able to answer three questions quickly:

1. What is this record?
2. How serious is it?
3. What action can I safely take next?

Use Material UI defaults as the foundation. Customise only enough to create a consistent enterprise appearance.

---

## Design principles

### 1. Functional before decorative

Every visible element should help users navigate, understand status, inspect risk, or take an action.

Avoid:

- Gradients.
- Glassmorphism.
- Hero banners.
- Large illustrations.
- Decorative charts without an API-backed metric.
- Animation beyond small Material UI feedback states.
- “Cyber” visual clichés such as green terminal text, matrix backgrounds, glowing borders or fake SOC maps.

### 2. Calm and compact

Use space to make information readable, not to make the app feel empty.

- Prefer 8px spacing increments.
- Use 24px page padding on desktop.
- Use 16px padding on small screens.
- Keep dense operational tables readable rather than oversized.
- Use one primary action per area.

### 3. Clear status hierarchy

A finding’s severity, an observation’s triage status and an assessment’s lifecycle status are different concepts. Do not style them as if they are the same thing.

```text
Severity      = technical/business seriousness
Triage status = analyst review decision
Lifecycle     = workflow progress
```

### 4. Backend is the security boundary

Role-based navigation is for clarity, not protection. The frontend must never imply it is enforcing access control.

Hide unsupported actions from the UI, but always handle `401`, `403` and `404` safely because the API is authoritative.

---

## Layout system

### Desktop

```text
┌─────────────────────────────────────────────────────────────────────┐
│ Sidebar 240px  │ Top app bar (64px)                                 │
│                ├────────────────────────────────────────────────────┤
│ SARP           │ Breadcrumb / Page title / small contextual actions │
│                ├────────────────────────────────────────────────────┤
│ Assessments    │                                                    │
│                │ Main content (max width 1440px)                    │
│                │                                                    │
│                │ Cards, tabs, tables, dialogs                       │
│                │                                                    │
└────────────────┴────────────────────────────────────────────────────┘
```

- Sidebar: 240px width, fixed on desktop.
- Top app bar: 64px high.
- Main content: fluid width with `maxWidth: 1440px`, centred where sensible.
- Page content: `24px` desktop padding.
- Do not place important actions behind excessive overflow menus.

### Mobile and tablet

- Replace permanent sidebar with a temporary MUI `Drawer`.
- Keep the top app bar visible.
- Use horizontal scroll for wide data tables rather than crushing columns.
- Make observation detail a full-screen drawer or dialog.
- Keep tap targets at least 44px high/wide where practical.

---

## Theme rules

Create exactly one MUI theme in `src/theme/theme.js`.

### Colour roles

Use restrained, accessible semantic colours. Do not use a separate colour for every component.

```text
App background: very light neutral
Surface: white
Primary action: one professional blue
Text primary: near-black navy/grey
Text secondary: medium neutral grey
Borders/dividers: subtle cool grey
Sidebar: dark neutral navy/slate
```

Use status/severity colours only in chips, small indicators and important alerts. Do not colour entire pages or tables by severity.

Suggested semantic mapping:

| Meaning | Visual treatment |
|---|---|
| Critical | Strong red chip + text label |
| High | Orange/red-orange chip + text label |
| Medium | Amber chip + text label |
| Low | Blue/teal chip + text label |
| Informational | Neutral grey chip + text label |
| Confirmed | Blue or positive neutral status chip |
| False positive | Grey outlined chip |
| Duplicate | Purple/neutral outlined chip |
| Promoted | Green success chip |
| Error | MUI error alert |
| Warning | MUI warning alert |
| Success | MUI success alert/snackbar |

Never make a meaning dependent on colour alone. Every chip includes readable text.

### Typography

Use MUI’s default system/Roboto stack. Do not add decorative fonts.

```text
Page title: h5 or h4, semibold
Section heading: h6, semibold
Table text: body2
Metadata: caption or body2, secondary colour
Buttons: default MUI weight
```

Avoid excessive all-caps. Use it only for small labels such as `CVSS` or `CVE` where the term conventionally appears in capitals.

### Shape and elevation

```text
Border radius: 8px
Cards: outlined or very low elevation
Inputs/buttons: MUI defaults with 8px radius
Dividers: subtle, frequent where they clarify groups
```

Avoid heavy shadows. SARP is an information system, not a consumer storefront.

### Theme skeleton

Codex may adapt exact hex values, but preserve the roles and constraints:

```javascript
import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  shape: { borderRadius: 8 },
  palette: {
    mode: 'light',
    primary: { main: '#2563eb' },
    background: { default: '#f8fafc', paper: '#ffffff' },
  },
  typography: {
    fontFamily: 'Roboto, Arial, sans-serif',
  },
  components: {
    MuiCard: {
      defaultProps: { variant: 'outlined' },
    },
    MuiButton: {
      defaultProps: { disableElevation: true },
    },
  },
});
```

Do not add global CSS resets beyond Material UI `CssBaseline` unless a concrete browser issue needs one.

---

## Component patterns

### Page header

Every major screen begins with:

```text
Breadcrumb (when useful)
Page title
One-sentence contextual explanation
Primary action only when action exists and user may perform it
```

Example:

```text
Assessment: Northwind Q3 External Review
Review imported observations before promoting confirmed issues to managed findings.
```

### Cards

Use cards only to group closely related information.

Good:

- Assessment overview.
- Import metadata.
- Finding summary.
- Triage decision form.

Avoid wrapping every individual table row or label inside a card.

### Tables

Tables are a core SARP pattern.

Rules:

- Header row remains visually distinct.
- Text columns left aligned.
- Numbers/dates right aligned or consistently formatted.
- Use no more than 6–8 visible columns.
- Use truncation with a tooltip for long evidence/title fields.
- Keep the primary identifier readable.
- Use a visible `Open` action or make the row keyboard-accessible and clearly clickable.
- Add an empty state inside the table area, not a blank white panel.
- Do not use dense tiny text below a legible size.

Example observation row:

```text
[High] Missing anti-clickjacking header | ZAP | https://app.example.test/account | New | Medium confidence | Open
```

### Chips

Create reusable chips only:

```text
SeverityChip
StatusChip
SourceToolChip
```

Do not recreate ad-hoc colour rules in every page.

### Forms and dialogs

- Use one-column forms by default.
- Use two columns only for short related fields on desktop.
- Show required fields clearly.
- Put help text under unusual fields, especially CVSS and triage notes.
- Put primary submit button on the right; cancel on the left or beside it.
- Disable submit while a request is running.
- Keep dialog titles action-oriented:
  - `Confirm observation`
  - `Mark as false positive`
  - `Promote to finding`

### Action hierarchy

```text
Primary action: contained button
Secondary action: outlined button
Tertiary action: text button
Dangerous action: outlined/error treatment plus confirmation
```

For the current app, “false positive” and “duplicate” are not destructive database deletes. Still require a clear note/confirmation because they change analyst workflow state.

### Feedback states

Every network-bound component must represent:

```text
Loading → Skeleton/spinner in existing layout
Empty   → helpful explanation and next step
Error   → safe Alert plus Retry
Success → Snackbar or small success Alert
```

Good empty state:

```text
No scanner observations match these filters.
Clear filters or import an authorised report through the controlled import process.
```

Bad empty state:

```text
No data.
```

---

## Page-by-page UX guidance

### Login

- Centred card, around 420–460px wide.
- Light background, no large artwork.
- SARP wordmark as text, not a logo project.
- Include a discreet fictional-data note.
- Put login error directly above or below the form.
- Do not say whether email or password was wrong.

### Assessment list

- Start with the title, small description and table.
- Do not show metric cards until a real dashboard API exists.
- Show framework and status as compact chips/text.
- Use client name as secondary information.

### Assessment workspace

- Put assessment identity in the header.
- Tabs should be persistent and predictable.
- Avoid deeply nested tabs.
- Preserve `tab` in the URL query string.
- Use `Overview` for facts, not dashboard-like placeholder cards.

### Imports tab

- Clearly separate import history from observations.
- Show tool icon/text chip, filename, status, counts and timestamp.
- Inform the user that import is CLI-controlled for this version; do not show a disabled “Upload” control without explanation.

### Observations tab

- This is the main operational screen.
- Keep filters at the top with source/tool and triage status.
- Use row click to open a detail drawer.
- Actions should be in the drawer, not crowded into each row.
- Show source identity prominently so analysts understand whether evidence came from Nmap, ZAP, Nessus or Burp.

### Observation detail drawer

Order information like an analyst thinks:

```text
1. Title and current triage status
2. Source tool, confidence and asset/location
3. Scanner severity / CVE/CWE metadata
4. Safe evidence summary
5. Suggested remediation
6. Import and audit metadata
7. Allowed actions
```

Use section dividers. Keep the primary action near the bottom/right but ensure it is visible without excessive scrolling.

### Finding detail

- Use a top summary card for CVSS/severity/status.
- Split body into clear sections: Description, Impact, Remediation, Ownership, Source Evidence.
- Do not display raw scanner evidence.
- Link source observations where backend permissions allow it.

---

## Role-aware UX

| Area | Admin | Consultant | Manager | Client user |
|---|---:|---:|---:|---:|
| Assessment list | View | View assigned | View assigned | View own client only |
| Imports tab | View | View | Optional read-only or hidden | Hidden |
| Scanner observations | View/triage | View/triage | Read-only summary or hidden | Hidden |
| Promote observation | Yes | Yes | No | No |
| Findings | View | View | View | View approved/visible records |
| Membership management | Future admin UI only | No | No | No |

The exact backend response is authoritative. Treat role-aware UI as a way to reduce confusion, not as access control.

---

## Accessibility checklist

- Use visible focus styles; do not remove outlines.
- Every input has a label.
- Icon-only buttons have `aria-label`.
- Dialog focus is trapped by MUI and returns to the trigger after close.
- Errors appear near fields and in a summary alert where appropriate.
- Use readable contrast; do not use pale text for important information.
- Chips contain text, not just icons/colour.
- Avoid hover-only actions; keyboard and touch users must have the same actions.
- Avoid time-limited feedback that disappears before it can be read.
- Respect reduced motion by not introducing decorative animations.

---

## CSS rules for Codex

1. Prefer `sx` for component-local styling.
2. Put shared spacing, palette and component defaults in the central theme.
3. Create a CSS file only if a layout cannot be expressed reasonably with MUI.
4. Never use inline `<style>` tags.
5. Never use `!important` unless fixing a proven third-party conflict.
6. Do not use manual pixel positioning for primary layout.
7. Do not create one-off hex colour values in feature components; use theme palette values.
8. Do not use animation libraries.
9. Do not add dark mode in this sprint.
10. Keep custom CSS minimal enough that a reviewer can understand the visual system in `theme.js`.

---

## Visual quality acceptance criteria

The UI is ready when it looks like a focused internal enterprise tool:

- No page is visually blank while loading.
- No route has unstyled default HTML controls.
- Tables, chips, dialogs and errors look consistent.
- Main workflow needs no guesswork.
- Mobile layout remains usable.
- There are no fake charts, fake metrics, non-working upload buttons or dead navigation items.
- There are no decorative visual effects competing with security data.
