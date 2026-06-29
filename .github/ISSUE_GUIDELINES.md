# GitHub Issue Guidelines

Every implementation issue should follow a consistent structure and use the project planning fields.

---

## Issue structure

### Objective

Describe the goal of the work in one or two sentences.

### Scope

List what is included in this issue.

### Acceptance criteria

Define the conditions that must be satisfied before the issue can be closed.

### Out of scope

List work that explicitly does not belong in this issue.

### Notes *(optional)*

Include implementation notes, references, methodology decisions, or dependencies where useful.

---

## GitHub Project fields

### Status

* Backlog
* Ready
* In Progress
* Review
* Done

### Priority

* High
* Medium
* Low

### Size

* XS
* S
* M
* L

---

## Labels

### Type

* `type: feature`
* `type: enhancement`
* `type: bug`
* `type: refactor`
* `type: docs`
* `type: test`

### Area

* `area: architecture`
* `area: data-layer`
* `area: market-data`
* `area: reporting`
* `area: streamlit`
* `area: notebooks`

### Risk module

* `risk: var`
* `risk: stress`
* `risk: liquidity`
* `risk: leverage`
* `risk: attribution`
* `risk: esg`

### Regulation

* `reg: aifmd`
* `reg: ucits`
* `reg: priips`
* `reg: annex-iv`

### Asset class

* `asset: hedge-fund`
* `asset: private-equity`
* `asset: infrastructure`
* `asset: real-estate`
* `asset: private-debt`

### Development

* `dev: dependencies`
* `dev: ci`
* `dev: release`

---

## Milestones

* **v0.1.0 - Foundation**
* **v0.2.0 - Core Risk Analytics**
* **v0.3.0 - Regulatory Reporting**
* **v0.4.0 - Alternative Assets**
* **v0.5.0 - Applications**
* **v1.0.0 - Feature Parity**

---

## General rules

* One issue should represent one deliverable.
* Keep issues implementation-focused.
* Link related issues where appropriate.
* Avoid mixing unrelated features in the same issue.
* Complete the acceptance criteria before closing an issue.
* Use labels to classify the issue and project fields for planning.
* Prefer checklists inside an issue instead of creating many micro-issues.
