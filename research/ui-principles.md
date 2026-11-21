# Usability review

Reviewed 2026-11-21 using primary design guidance. Firecrawl had zero available credits; sources were read using the web tool.

- [USWDS data visualizations](https://designsystem.digital.gov/components/data-visualizations/): provide a tabular representation, avoid requiring hover to understand data, explain the metric in context, and limit color to a clear purpose. Applied: keyboard-operable search/ranking table, CSV exports, sequential map bands, persistent selected-district values, explicit obligation definition.
- [USWDS tables](https://designsystem.digital.gov/components/table/): tables help readers find and compare structured data. Applied: semantic headers/caption, stable column layout, right-aligned numerical columns, pagination, mobile scrolling with a keyboard-focusable region.
- [W3C WAI region labels](https://www.w3.org/WAI/tutorials/page-structure/labels/): use short descriptive labels and avoid redundant labels for unique landmarks. Applied: main/nav/aside landmarks, skip link, visible field labels, concise navigation, accessible control names.

User preference: common fonts and minimal text. The entire interface uses Arial/Helvetica/system sans-serif; there are no web font requests. Removed the display serif, repeated date metric, marketing-style headline, footer slogan, repeated geography descriptions, and long inline explanations. Kept the distinction between commitments and payments and GAO state precision because those affect interpretation. Detailed caveats and citations live in one dialog.

Review outcomes: desktop and 390px layouts checked with Playwright; no horizontal page overflow. Numeric table can scroll independently. Native select controls, visible focus, Escape-dismissable dialog, list alternative to small map targets, functional search empty states, and separate scales for insets. Small archipelagos use locator outlines and full-inset click targets to remain findable without altering geographic area.

Limit: automated interaction checks and visual review do not establish complete WCAG conformance or replace user research.
