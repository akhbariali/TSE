# TSE Market Archive

<!-- impeccable:product-schema 1 -->

## Platform
web

## Stack
Provisional recommendation: Python standard-library HTTP server, SQLite, and plain HTML/CSS/JavaScript. Stack and deployment preferences were asked using the question tool; no reply received yet. No paid service or external runtime dependency is needed.

## Users
The requesting user researches Tehran Securities Exchange market-performance Excel reports and wants to find reports and their analysis in one place.

## Product Purpose
Collect as many market-performance reports as the source exposes across all pages, avoid duplicate downloads, and make the reports and ownership-flow analysis available in a web app with no login.

## Operating Context
Source: https://www.tse.ir/download-center, category 12. Workbooks use Persian symbols and Solar Hijri dates. The existing workspace contains 20 parsed reports and ownership-flow exports. An archive download is now collecting 797 Excel attachments across 41 pages.

## Capabilities and Constraints
Report browsing and original workbook downloads; date filtering; individual/institutional flow rankings; symbol history; rolling flows; trading-value concentration; data-quality and download status; resumable refresh. Retain original symbol suffixes and source provenance. Do not represent mixed-instrument totals as equity-only activity, ownership transfers as new cash, or flows as return predictions. Historical layouts may be unsupported; such files must stay downloadable with explicit analysis status.

## Open Decisions
English interface is provisional while the language question is pending. Persian text and dates remain intact. Hosting is not specified; run locally by default. Visual direction and product name are implementation choices, not user-provided brand commitments.

## Product Principles
- Source files and accounting consistency remain inspectable.
- Dates, scope, units, and data limitations stay close to the metrics.
- Browse and analyze without an account.
- Repeated archive updates preserve existing successful downloads.
