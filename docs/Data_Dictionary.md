# Earthdata Community Insights Data Dictionary

**Purpose:** Define the principal domain objects and relationships used by Earthdata Community Insights.  
**Scope:** Conceptual model first; database implementation second.

## 1. Core objects

### Source

**Purpose:** Identifies an artifact or system from which community information was collected.

**Examples:** User Working Group report, workshop summary, spreadsheet, Word document, PDF, survey, meeting notes.

**Authority:** The original artifact and its registered metadata.

**Important attributes:**

- Source identifier and title
- Source type
- Publication or event year
- Author or sponsoring organization
- Original location or retained file reference
- Import status and dates

**Relationships:**

- contains Community Evidence;
- may be associated with Organizations;
- may produce multiple import runs.

**Current implementation:** `sources` and related import metadata.

---

### Community Evidence

**Purpose:** Preserves an original statement or observation that supports one or more community needs.

**Authority:** The source statement. Original wording should not be overwritten.

**Important attributes:**

- Evidence code
- Original statement
- Normalized statement
- Source location or context
- Evidence type
- Event year
- Review and validation fields

**Relationships:**

- belongs to a Source;
- may be attributed to an Organization;
- supports a Canonical Need.

**Lifecycle:** Imported → reviewed → accepted, edited only in normalized fields, or rejected.

**Current implementation:** `evidence`.

---

### Canonical Need

**Purpose:** Represents a concise, curated user outcome shared by one or more evidence records.

**Authority:** Human review informed by supporting evidence.

**Important attributes:**

- Need code
- Canonical wording
- Summary and desired outcome
- Category or theme
- Status and priority
- Review notes
- Signal measures derived from recurrence and source diversity

**Relationships:**

- supported by Community Evidence;
- associated indirectly with Organizations and Sources through evidence;
- requires one or more Capabilities;
- may have candidate or reviewed relationships to Engineering Artifacts.

**Lifecycle:** Proposed → reviewed → approved → revised or archived.

**Quality rule:** Wording should describe an outcome and should not prescribe a particular product unless the product itself is essential to the evidence.

**Current implementation:** `needs`.

---

### Organization

**Purpose:** Identifies an organization that contributed evidence, participated in an engagement, owns a tool, or publishes authoritative information.

**Examples:** NASA DAAC, NOAA, EPA, USGS, university, partner organization.

**Important attributes:**

- Organization code and name
- Organization type
- Parent organization
- Description

**Relationships:**

- contributes Community Evidence;
- may own or steward an Earthdata Tool;
- may publish Capability Evidence.

**Current implementation:** `organizations` and evidence relationship tables.

---

### Capability Category

**Purpose:** Provides a stable, user-oriented grouping for capabilities.

**Initial categories:**

- Discovery and Search
- Data Access and Delivery
- Subsetting and Transformation
- Visualization and Analysis
- Metadata and Interoperability
- Documentation and User Support
- Processing and Workflow
- Reliability and Operations

**Important attributes:**

- Category code and preferred name
- Description
- Display order
- Optional parent category

**Relationships:**

- contains Capabilities.

**Implementation direction:** Categories may be stored as first-class records as the framework expands.

---

### Capability

**Purpose:** Describes a reusable, implementation-independent function that helps satisfy community needs.

**Examples:** Spatial Subsetting, Temporal Search, Interactive Visualization, WMS, API Documentation.

**Authority:** Curated capability framework and human review.

**Important attributes:**

- Stable capability code
- Preferred name
- Definition
- Category
- Keywords and synonyms
- Inclusion and exclusion notes
- Review status

**Relationships:**

- required by Canonical Needs;
- provided by Earthdata Tools;
- demonstrated by Capability Evidence;
- may be related to, enabled by, or dependent on other capabilities.

**Lifecycle:** Proposed → reviewed → active → deprecated or merged.

**Current implementation:** `capabilities`, `need_capabilities`, and `tool_capabilities`.

---

### Earthdata Tool

**Purpose:** Represents an operational Earthdata application, service, library, or interface that provides capabilities.

**Initial examples:** Earthdata Search, Worldview, GIBS, CMR, Harmony.

**Authority:** Curated tool catalog supported by official product information.

**Important attributes:**

- Tool code and name
- Description
- Owning organization
- Product and documentation URLs
- Operational status

**Relationships:**

- provides Capabilities;
- has External Sources such as repositories and documentation sites;
- has Capability Evidence;
- has Engineering Artifacts.

**Current implementation:** `tools` and associated catalog tables.

---

### External Source

**Purpose:** Registers an approved external system or location from which tool-related records may be imported.

**Examples:** GitHub repository, official documentation site, release-note page.

**Important attributes:**

- External-source code and type
- Owner and repository name where applicable
- Base URL
- Tool association
- Synchronization status and timestamps

**Relationships:**

- belongs to an Earthdata Tool;
- produces Engineering Artifacts or Capability Evidence.

**Current implementation:** `external_sources`.

---

### Capability Evidence

**Purpose:** Demonstrates that a tool provides a capability or explains how users can apply it.

**Preferred evidence types:**

- Official product documentation
- API reference
- Tutorial or example
- Release note
- Product page

**Evidence roles:**

- Capability evidence
- Availability evidence
- Usage guidance
- Implementation provenance
- Planned work

**Important attributes:**

- Evidence code and title
- Evidence type and role
- Official URL
- Relevant excerpt or summary
- Publication or effective date
- Review status

**Relationships:**

- published for an Earthdata Tool;
- supports one or more Capabilities;
- may be connected to a Canonical Need through an approved capability relationship.

**Current implementation:** `solution_evidence` and related capability mappings. The user-facing term is Capability Evidence even where existing database names retain earlier terminology.

---

### Engineering Artifact

**Purpose:** Preserves software-development provenance and planned or completed engineering work.

**Examples:** GitHub issue, pull request, release, commit, roadmap item.

**Authority:** The originating repository or project system.

**Important attributes:**

- Artifact type and external number
- Title and body
- State
- Labels and milestone
- Created, updated, closed, or merged dates
- External URL

**Relationships:**

- belongs to an External Source and Earthdata Tool;
- may have a candidate or reviewed relationship to a Canonical Need;
- may provide provenance for a Capability.

**Current implementation:** `implementation_artifacts`.

---

### Need-to-Artifact Relationship

**Purpose:** Records a proposed or reviewed interpretation of how an engineering artifact relates to a canonical need.

**Relationship types may include:**

- Tracks
- Proposes
- Partially addresses
- Fully addresses
- Implements
- Documents
- Unrelated

**Important attributes:**

- Machine score and matched terms
- Explanation
- Relationship type
- Review status
- Reviewer and review date

**Authority:** Machine-generated until reviewed; human reviewer after confirmation.

**Current implementation:** `need_artifact_matches`.

---

### Review

**Purpose:** Records the human decision that establishes whether proposed wording or relationships are accepted.

**Minimum statuses:** Pending, Confirmed, Rejected, Uncertain.

**Important attributes:**

- Reviewed object or relationship
- Decision
- Reviewer
- Date
- Notes or rationale

**Rule:** Automated processing must not overwrite a reviewed decision. Pending machine-generated suggestions may be refreshed when matching logic changes.

**Current implementation:** Review fields are currently distributed across domain and relationship tables; a dedicated history model may be added later.

---

### Dataset Mode

**Purpose:** Separates the complete analytical dataset from a small curated demonstration dataset.

**Values:** Full and Demo.

**Full:** Uses the primary database containing all imported records.

**Demo:** Uses a separate database containing explicitly selected needs and their dependent evidence, organizations, capabilities, tools, capability evidence, and selected implementation relationships.

**Current implementation:** Environment variables plus `refresh-demo.ps1` and `use-dataset.ps1`.

## 2. Relationship summary

| From | Relationship | To | Authority |
|---|---|---|---|
| Source | contains | Community Evidence | Import and review |
| Organization | contributes | Community Evidence | Source and review |
| Community Evidence | supports | Canonical Need | Human review |
| Canonical Need | requires | Capability | Human review |
| Earthdata Tool | provides | Capability | Official evidence and review |
| Capability Evidence | demonstrates | Tool capability | Official source and review |
| External Source | produces | Engineering Artifact | Imported source |
| Engineering Artifact | relates to | Canonical Need | Machine suggestion, then review |
| Capability | relates to | Capability | Curated framework |

## 3. Naming guidance

- Codes should be stable, uppercase identifiers with underscores or established prefixes.
- Display names should be concise and understandable without product-specific knowledge.
- Canonical needs should use complete grammatical sentences.
- Capability names should describe functions, not product features or implementation methods.
- Database names may preserve legacy terminology temporarily, but user-facing labels should follow the domain vocabulary in this document.

## 4. Maintenance

Update this dictionary only when a domain object, its authority, lifecycle, or principal relationships change. Field-level SQL details belong in migration files and database introspection rather than this concise reference.
