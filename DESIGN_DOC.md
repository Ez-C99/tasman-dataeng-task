# Design and Plannig Document

## Decision Log (ADRs)

| ID | Title | Status | Date | Link |
|---:|---|---|---|---|
| 0001 | Runtime for the extractor | Accepted | 2025-08-19 | [ADR-0001](docs/architecture/decisions/0001-runtime-extractor.md) |
| 0002 | Scheduling & orchestration | Accepted | 2025-08-19 | [ADR-0002](docs/architecture/decisions/0002-scheduling.md) |
| 0003 | Operational data store | Accepted | 2025-08-19 | [ADR-0003](docs/architecture/decisions/0003-database.md) |
| 0004 | Data model shape | Accepted | 2025-08-19 | [ADR-0004](docs/architecture/decisions/0004-data-model-shape.md) |
| 0005 | Idempotency & primary key strategy | Accepted | 2025-08-19 | [ADR-0005](docs/architecture/decisions/0005-idempotency-key-upsert.md) |
| 0006 | Secrets management | Accepted | 2025-08-19 | [ADR-0006](docs/architecture/decisions/0006-secrets-management.md) |
| 0007 | API paging and limits | Accepted | 2025-08-19 | [ADR-0007](docs/architecture/decisions/0007-api-paging-and-limits.md) |
| 0008 | DB security and durability | Accepted | 2025-08-19 | [ADR-0008](docs/architecture/decisions/0008-db-security-and-durability.md) |
| 0009 | Data quality strategy | Accepted | 2025-08-19 | [ADR-0009](docs/architecture/decisions/0009-data-quality.md) |
| 0010 | Integration testing approach | Accepted | 2025-08-19 | [ADR-0010](docs/architecture/decisions/0010-integration-testing.md) |

1. Gather Requirements
2. Sample data pull & initial analysis
3. Planning (including comparison, selection and justification)
4. Design

# Gather Requirements

As I iterate through all the thoughts, design and planning in this doc, I'll do my best to ground my thoughts and results of my research in concepts from the Fundamentals of Data Engineering (FoDE) book so everything has the foundations of the most sound solution possible.

## Task Brief

>[!question] What is the problem to be solved?

I need to present data from the USA Jobs database in my own database

>[!question] What is the task to solve the problem?

Programmatically extracting data from the USA Jobs database, filter and format it then load it into a database. All of this must be in a containerised ETL solution that is easily deployable with the minimum required software and skills.

> [!question] What is meant by loading the data **"durably"**?

“Durable” in this context means the data is persisted with guarantees against loss and with recoverability. Concretely:

- **ACID** storage (e.g., Postgres on RDS), not an ephemeral container volume.
- **Idempotent loads** (safe re-runs) keyed by a stable identifier (e.g. primary key) so duplicates don’t accumulate.
- **Backups & PITR** on the database (automated backups, snapshots) and **encryption at rest/in transit** when in the cloud. On Amazon RDS this means enabling encryption (KMS) and SSL/TLS to the instance, plus point-in-time restore.

> **FoDE:** “Plan for failure” and “prioritise security” are explicit architecture principles—design for recoverability, least privilege, encryption, and auditability from day one.

> [!question] Is there anything here I’m inexperienced on or unable to do? How do I overcome this?

**Using IaC to schedule specific resource types**: I've provisioned and managed common AWS resources many times but I have a feeling I may need to branch out a bit depending on the best solution I can research and come up with.

> [!question] Are there any immediate caveats or technicalities I can spot?
>

The subset that a Chicago jobseeker would find useful doesn't necessarily mean just in Chicago. A lot of people increase a search radius and don't mind commuting.

- It would be best to include a reasonable, arbitrary search distance and/or commute time to decide the radius to search in.

#### Stakeholder Expectations Summary

Solution:
USA Jobs reporting database connection, retrieval, search for data engineering jobs, parsing for Chicago-based jobseekers and loading into database

Technical:

- ETL
  - API connection and extraction with respect to response and rate constraints
  - Keyword data filtering based on field(s)
  - Domain-based field subset parsing
  - Database, schema and model design to be loaded according to
  - Loading into cloud-hosted DBMS
- IaC configured, easy setup and deployment from any machine (provided Python and Docker min. requirements)
- Zero/minimal cost running

Documentation and delivery:

- Full documentation and guides on context, instructions on usage and deployment
- Design decision justifications
- Clearly documented process E2E

## Scoping

>[!question] What research needs to be done?

- API and its output(s)
- Tech and tools to be considered
- Synergy of architecture
- Best standards and practices in the implementation

>[!question] What tools can help throughout the process?

- LLM(s)
- Docs
- Online support e.g. Stack Overflow

> [!question] What are the next steps?

1. Pull the data (or a sample) for initial insights
2. Plan and justify stack around insights
3. Implement (iterative)
4. Test (Iterative)

> [!question] What can feasibly be done in arbitrary time {x} hours / days?

Balancing work and life schedule and responsibilities, requirement gathering completed in half a day. Initial data pull can be done programmatically or in Postman (likely Postman for speed); both this and initial exploratory insights on the data should be another half day. Following this, the repo setup and extraction functionality could be one day, the transformation logic another day and the database and loading logic another day. Lastly a day for all types of testing and consolidation, including documentation. This is an estimated 5 days.

Note: This isn't 5 full days, but 5 days where time blocks can be found to work on the solution

## Sample Data Insights

Use the API key to pull the data (subset?) for initial insights
Methods:

- Postman
- Initial repo and `GET` request

### API

> [!question] What are the constraints and limits of requests?

- Authentication requires just API key and host email
- Terms of use are effectively that you must be authorised to access

 Search Jobs API:

- Defaults to only "Public" jobs
- User must make additional request to search for "Status" jobs
- Maximum of 10,000 rows (records) per query
- Maximum of 500 rows (records) per page

Code List API:

- No limits

Dynamic Search:

- No limits

> [!question] What endpoint(s) should I consider?
`GET /api/Search`

Key Parameters:

- `Keyword`
 Searches the job announcement for all of the words or synonyms
  - The task specifically asked for all jobs that have `"data engineering"` as a keyword. This is the way to go for the initial search
  - What further cleaning will need to be done?

- `PositionTitle`
 A "contains" search specifically on job post titles
  - What's the discrepancy between data engineering titled jobs and keyword jobs?
  - Will this help with the cleaning of the data in any way? e.g. cross-referencing a `"data engineering"` search of the titles with a keyword and filtering

- `LocationName`
 The city of the job
  - Perfect for the Chicago search

- `Page`
 Page number to view of the results

- `ResultsPerPage`
 Returns the page size specified. Limit of 500 as specified before
  - Does the data set surpass the the result limit?
  - If so, what measures can be put in place to make sure all data is pulled (and for robustness and scalability, if not?)

- `Radius`
 Used with `LocationName` to specify a search radius around location
  - What unit of measurement is the radius in?
  - Does a job seeker based in Chicago have areas close enough that they'd commute to for work, worth including with the radius?
    - Check on a map and with differing radius value requests

Evidently, the search functionality is built into the API (very good for solution simplicity). All I need to do is decide the granularity with which I want to make the search

### First `data engineer` search requests

Running the API requests in Postman for speed, simplicity and visual formatting
Basic keyword run:
`GET https://data.usajobs.gov/api/search?Keyword=data engineering`

Immediately:

- There are 387 rows in the response - well under the 10,000 row maximum
- The response is made of various levels of nested JSON
- The data types seem to be `string`, `int` and `bool` so far but code will reveal anything missee

#### Response metadata (result items removed)

```JSON
{
 "LanguageCode": "EN", 
 "SearchParameters": {}, 
 "SearchResult": {
  "SearchResultCount": 25,  
  "SearchResultCountAll": 387,  
  "SearchResultItems": [],
  "UserArea": {  
   "NumberOfPages": "16",
   "IsRadialSearch": false
  }
 }
}
```

Insights:

- There are 387 data engineering key word roles
- The default result count on a page is 25 but all 387 can be shown with the `ResultsPerPage` parameter set to 500
  - `ResultsPerPage=500` should be a default parameter for requests now

> [!todo]
> The extraction logic's requests should be batched according to the `"SearchResultCountAll"` value of the first request. A value <=500 only needs 1 request, but a value >500 needs as many requests (that increment the `Page` parameter) as the quotient + 1
>
> e.g. a response where `"SearchResultCountAll": 3870,` would need `(3870 // 500) + 1 = 8` requests where the `Page` parameter increments from 1 to 8.  

>[!question] Does this now make `Page` a key parameter now? Or do I start declaring the parameter from 2
>
Best to declare it from the start for consistency and logical, programmatic simplicity

>[!question] Do I page the API sequentially or concurrently?
>
>- How does affect performance and retrieval time? (Worth it or negligible? Impact on scalability?)
>- Does this have any negative effect on the API constraints?

For the sake of this task and the low bandwidth, low data size and low daily demand, sequential should be fine but cases of larger throughput high demand would need parallelism/concurrency. This also means I avoid testing the API limits and constraints, but this would also need to be a consideration for the larger data case just mentioned.

**LLM response to the question:**
"With ~hundreds to a few thousand results, sequential (with a small retry w/ backoff on 429/5xx) is fine and easier on rate limiting. If you need later need speed, use bounded concurrency (e.g., 4–8 workers) and centralize throttling. (USAJOBS publishes limits; respect 10k rows/query and 500/page; backoff on any 429.)"

##### Handling the Chicago jobseeker requirement

If the schema works as I intend it to, I should just be okay to filter the jobs by location
There's one big question in this though:
> [!question]
> Will I filter the Chicago jobseeker on the API side? with a request like `GET https://data.usajobs.gov/api/search?Keyword=data engineering&ResultsPerPage=500&Page=1&LocationName=Chicago&Radius=50`
>
> - This would mean 2 separate data extractions that have the same transformation and schema logic applied to them before loafing
>
> **OR**
>
> Will I perform a singular API request and then filter the data on the logic side
>
> - This could work with a system like checking the `"Longitude"` and `"Latitude"` values against a predetermined range that Chicago workers would be in or commute to

> **FoDE:** minimise “data gravity” early in the pipeline and push filters upstream whenever possible.

LLM response:

- **API-side**: `LocationName=Chicago` plus `Radius` reduces payload, respects rate limits, and is simpler for end-users to reason about. **Recommended first**.
- **Client-side**: Fetch broader results and geo-filter by lat/long. **Use only** if you need custom geography (e.g., commute polygons) not supported by API.

> [!summary] API-side Chicago jobseeker filtering it is.

> [!todo]
> Since `Radius` units aren’t documented, pick a default (e.g., the 50 I'm using) and make it configurable. Then document that I validated with a test call.

##### Ideal API request (so far)

Based on these insights, there’s a new base case API request (for now):

- `https://data.usajobs.gov/api/search?Keyword=data engineering&ResultsPerPage=500&Page=1`
This expands slightly in the Chicago jobseeker requirement:
- `GET https://data.usajobs.gov/api/search?Keyword=data engineering&ResultsPerPage=500&Page=1&LocationName=Chicago&Radius=50`

#### Response results: `"SearchResultItems"`

Programmatic parsing of the JSON structure through schema inference logic that could be reused in a helper function later
Generated with the following prompt in GitHub Copilot:

```plaintext
I need to create a JSON parser that will read the object in sampe_get.json and tell me the data type for each key in the object. The JSON seems to be nested to multiple levels so I want this to be respresented in the output too
```

```bash
python json_parse.py data/sample_get.json
# Schema (tree view)
LanguageCode: str
SearchParameters: object
SearchResult: object
  SearchResultCount: int
  SearchResultCountAll: int
  SearchResultItems: list<object>
    MatchedObjectId: str
    MatchedObjectDescriptor: object
      PositionID: str
      PositionTitle: str
      PositionURI: str
      ApplyURI: list<str>
      PositionLocationDisplay: str
      PositionLocation: list<object>
        LocationName: str
        CountryCode: str
        CountrySubDivisionCode: str
        CityName: str
        Longitude: float
        Latitude: float
      OrganizationName: str
      DepartmentName: str
      JobCategory: list<object>
        Name: str
        Code: str
      JobGrade: list<object>
        Code: str
      PositionSchedule: list<object>
        Name: str
        Code: str
      PositionOfferingType: list<object>
        Name: str
        Code: str
      QualificationSummary: str
      PositionRemuneration: list<object>
        MinimumRange: str
        MaximumRange: str
        RateIntervalCode: str
        Description: str
      PositionStartDate: str
      PositionEndDate: str
      PublicationStartDate: str
      ApplicationCloseDate: str
      PositionFormattedDescription: list<object>
        Label: str
        LabelDescription: str
      UserArea: object
        Details: object
          JobSummary: str
          WhoMayApply: object
            Name: str
            Code: str
          LowGrade: str
          HighGrade: str
          PromotionPotential: str
          OrganizationCodes: str
          Relocation: str
          HiringPath: list<str>
          MCOTags: list<str>
          TotalOpenings: str
          AgencyMarketingStatement: str
          TravelCode: str
          ApplyOnlineUrl: str
          DetailStatusUrl: str
          MajorDuties: list<str>
          Education: str
          Requirements: str
          Evaluations: str
          HowToApply: str
          WhatToExpectNext: str
          RequiredDocuments: str
          Benefits: str
          BenefitsUrl: str
          BenefitsDisplayDefaultText: bool
          OtherInformation: str
          KeyRequirements: list<>
          WithinArea: str
          CommuteDistance: str
          ServiceType: str
          AnnouncementClosingType: str
          AgencyContactEmail: str
          SecurityClearance: str
          DrugTestRequired: str
          PositionSensitivitiy: str
          AdjudicationType: list<str>
          TeleworkEligible: bool
          RemoteIndicator: bool
          FinancialDisclosure: bool
          BargainingUnitStatus: bool
        IsRadialSearch: bool
    RelevanceRank: int
  UserArea: object
    NumberOfPages: str
    IsRadialSearch: bool
```

> [!question] What are the data types and structures in the fields in the response?

Apart from the objects that contain many nested keys of varying data types, we have:

- string
- integer
- float
- boolean
- list of strings

### Initial proposed Schema

This is what I aim to achieve by the rest of ETL process, respective of the `data engineer` search and Chicago subset

Assume all necessary data has been loaded and appended so the extraction metadata isn't necessary anymore

Definitions of all keys in the JSON object are provided in the reference: <https://developer.usajobs.gov/api-reference/get-api-search>

```plaintext
Results table
  Id: int                   (primary key)
  MatchedObjectId: str
  PositionID: str
  PositionTitle: str
  PositionURI: str
  ApplyURI: str
  PositionLocationDisplay: str
  LocationName: str
  CountryCode: str
  CountrySubDivisionCode: str
  CityName: str
  Longitude: float
  Latitude: float
  OrganizationName: str
  DepartmentName: str
  JobCategory: str
  JobGrade: str
  PositionSchedule: str
  PositionOfferingType: str
  QualificationSummary: str
  MinimumPayRange: int
  MaximumPayRange: int
  PayRateIntervalCode: str
  PayDescription: str
  PositionStartDate: timestamp
  PositionEndDate: timestamp
  PublicationStartDate: timestamp
  ApplicationCloseDate: timestamp
  
Details table
  DetailId: int                (foreign key to the Id primary key in Results)
  JobSummary: str
  LowGrade: str
  HighGrade: str
  PromotionPotential: str
  OrganizationCodes: str
  Relocation: str
  HiringPath: str
  MCOTags: str
  TotalOpenings: str
  AgencyMarketingStatement: str
  TravelCode: str
  ApplyOnlineUrl: str
  DetailStatusUrl: str
  MajorDuties: str
  Education: str
  Requirements: str
  Evaluations: str
  HowToApply: str
  WhatToExpectNext: str
  RequiredDocuments: str
  Benefits: str
  BenefitsUrl: str
  BenefitsDisplayDefaultText: bool
  OtherInformation: str
  KeyRequirements: str
  WithinArea: str
  CommuteDistance: str
  ServiceType: str
  AnnouncementClosingType: str
  AgencyContactEmail: str
  SecurityClearance: str
  DrugTestRequired: bool
  PositionSensitivitiy: str
  AdjudicationType: str
  TeleworkEligible: bool
  RemoteIndicator: bool
  FinancialDisclosure: bool
  BargainingUnitStatus: bool
```

> [!note] All schema points and decisions are made with the task and stakeholder requirements in mind e.g. the management of nested fields

#### `Id`
>
> [!info] Since the results were obtained through a search, there's no sequential primary key. I've added my own

#### `"SearchResultItems"`
>
> [!todo]
> All results data will need to be unwrapped from `"SearchResultItems": list<object>`. Each individual result is a JSON object inside this list.

#### `"MatchedObjectDescriptor"`
>
> [!important]
> All individual job post data (apart from `MatchedObjectId`) is nested in `MatchedObjectDescriptor: object`  so it will be the point of entry for full parsing.

#### `"ApplyURI"`
>
> [!todo]
> Normalise all `"ApplyURI"` fields from `list<str>` to `text[]` (Postgres array)
>
> - There only ever seems to be a single apply link in the field but some jobs might get multiple apply links. This way I can avoid lossy flattening in those rare cases.

#### `"PositionLocation"`
>
> [!important]
> The sub-fields of `"PositionLocation"` (`list<object>` type) consist of `"LocationName"`, `"CountryCode"`, `"CountrySubDivisionCode"`, `"CityName"`, `"Longitude"` and `"Latitude"`. These would all be valuable for location data in a table.
>
> - This goes deeper when `"PositionLocationDisplay"`, the same-level field before `"PositionLocation"` has the value of `"Multiple Locations"`; the aforementioned fields form >1 dictionary nesting of them, all inside the list.
> - This will be a key point of transformation and normalisation for the final data structure I have in mind, since location data will be necessary for the Chicago jobseeker part of the task

>[!question] How do I structure the location fields when there are multiple?
> My immediate thought is to place them all in the same field, separated by commas. Creating multiple tables with foreign keys attached to job records, just to show the different locations, seems like overkill

> [!caution]
> Searches also return positions with international locations so the Chicago job seeker table will need to have some validation in place that shows only the necessary jobs to them

#### `"JobCategory"`
>
> [!todo]
Convert my equivalent of the `"JobCategory"` field to a string concatenation of categories listed inside it
>
> - The `"JobCategory"` list of objects has the names (useful) and codes (not useful for my DB since there's not need for me to replicate their code mapping).

#### `"JobGrade"`
>
> [!todo]
Convert my equivalent of the `"JobGrade"` field to a string with the code inside it

#### `"PositionSchedule"`
>
> [!info]
> The API reference provides a code mapping for the `"Code"` entity of `"PositionSchedule"`, as below:

| Value | Definition         |
| ----- | ------------------ |
| 1     | Full-Time          |
| 2     | Part-Time          |
| 3     | Shift Work         |
| 4     | Intermittent       |
| 5     | Job Sharing        |
| 6     | Multiple Schedules |

> [!todo]
> Add some data mapping logic to convert the code to the text string definition of the code and append whatever was in the `"Name"` sub-field for it (mostly an empty string but sometimes a description)
>
> - Repeat for any other code mappings necessary to the data
> - This minimises any data loss and increase durability in the transformation to my schema, while increasing data clarity

> [!important] UPDATE: The mapping logic should be API-based since the USA Jobs API has codelist endpoints for search result entities
>
> - There's no need for any authorisation headers in codelist requests either so retrieval is simple

In this case, the request `GET /api/codelist/positionscheduletypes` yields the response:

```json
{
    "CodeList": [
        {
            "ValidValue": [
                {
                    "Code": "1",
                    "Value": "Full-time",
                    "LastModified": "2021-03-19T10:35:31.407",
                    "IsDisabled": "No"
                },
                {
                    "Code": "2",
                    "Value": "Part-time",
                    "LastModified": "2021-03-19T10:35:31.423",
                    "IsDisabled": "No"
                },
                {
                    "Code": "3",
                    "Value": "Shift work",
                    "LastModified": "2021-03-19T10:35:31.44",
                    "IsDisabled": "No"
                },
                {
                    "Code": "4",
                    "Value": "Intermittent",
                    "LastModified": "2018-07-27T06:13:07.7",
                    "IsDisabled": "No"
                },
                {
                    "Code": "5",
                    "Value": "Job sharing",
                    "LastModified": "2021-03-19T10:35:31.453",
                    "IsDisabled": "No"
                },
                {
                    "Code": "6",
                    "Value": "Multiple Schedules",
                    "LastModified": "2018-07-27T06:13:07.703",
                    "IsDisabled": "No"
                }
            ],
            "id": "PositionScheduleType"
        }
    ],
    "DateGenerated": "2025-08-18T23:43:47.5645909Z"
}
```

> [!note]
> This means there's no need to store any local mapping and this part of the solution remains dynamic (as long as USA Jobs maintain the endpoint and structure)

> [!todo]
> Use the `/codelist` endpoints at load time and/or cache daily so I see the human labels in my tables

#### `"PositionOfferingType"`
>
> [!todo]
> Take the `"Name"` sub-field value of this object
>
> - It's mostly empty but some records have a value inside it

#### `"PositionRemuneration"`
>
> [!todo]
> For `"MinimumRange"` and `"MaximumRange"`:
>
> - Convert data type to `int`
> - Change the names to `"PayMinimumRange"` and `"PayMaximumRange"`
>   - The schema is being normalised so names need to be clear in the absence of nesting
>
> Change `"RateIntervalCode"` and `"Description"` names to `"PayRateIntervalCode"` and `"PayDescription"` for the same reason as above

#### `"UserArea"` and (most importantly) `"Details"`
>
> [!important]
> All front end job description information is stored in the `"Details"` object which is wrapped inside the `"UserArea"` object. There needs to be a double unwrapping here and will need to be unwrapped

> [!attention]
> There are 38 fields in this object alone and they are all specific to job posting information that a user would want access to.
> This changes my original perception of a single table for the model and makes me think it would be better to have the `"Details"` as its own table, linked to the original table I've been designing the schema for by a foreign key.
>
> - This is supported by the object having no deep nesting at all so even the string lists can just be appended to each other and separated by commas

#### Details table

Effectively all the inferred data types are kept the same apart from the following changes:
> [!todo]
>
> - Convert all `list<string>` into a concatenated string of all the items in the list
> - Convert `"DrugTestRequired"` into `bool`
>

#### Last (Initial) Schema Notes

- For best SOLID and DRY code, the JSON unwrapping and field code mapping functionalities should be their own encapsulated methods in a schema inference module/class. I'll vary the responsibility and granularity based on how it call comes together.

> [!question] What basic validations can be perceived for the data quality checking?

- Existence of key fields
- Types in all fields align with expectations
- Ranges of certain fields (more so numeric) are expected
 e.g. Longitude and Latitude within that of a valid range of Chicago (for that table)

>[!question] What are the estimated extra fields that will be necessary to create a schema for the DB later?

| Field             | Type               | Notes                                                                                                       |
| ----------------- | ------------------ | ----------------------------------------------------------------------------------------------------------- |
| created_at        | `timestamp`        | Lineage and auditing for records                                                                            |
| updated_at        | `timestamp`        | More lineage in case of DB operations e.g. queries                                                          |
| source_event_time | `timestamp`        |                                                                                                             |
| ingest_run_id     | `int`              |                                                                                                             |
| raw_json          | `JSONB` (Postgres) | Raw JSON descriptor. JSONB + GIN index lets you safely “reach back” if the physical schema missed something |
| deleted_at        | `timestamp`        | Soft delete indicator if not null                                                                           |

### Improved Proposed Schema

Further research and evaluation of my first schema idea design against best practices and yielded the following points:

**Pros** of 2 table schema

- Fast to implement, simple to query.
- Minimal joins; “good enough” for the task scope.

**Cons / Risks**

- Multi-valued fields flattened to comma-separated strings (locations, categories, hiring paths) are an anti-pattern: hard to query correctly and to index.
- Harder to evolve (schema drift, list growth).
- Hard to enforce referential integrity (e.g., multiple locations).

#### The new schema

This presents the need to further break down the model into a leaner, normalised core of tables as below:

- `job`: (1 row per job; keys, title, URI, org, remuneration summary, date fields…).
- `job_location`: (N rows per job; `city`, `state`, `lat`, `lon` + a **geography** type later if needed).
- `job_category`: (N rows per job; from `JobCategory`).
- `job_details`: (1 row per job; big text fields like summary, requirements, how-to-apply, flags like `RemoteIndicator`).

**Key choices**

- **Natural key:** `MatchedObjectId` (fallback: composite like `PositionID` + `PositionURI` if needed).
- **Arrays/JSONB:** `text[]` for `ApplyURI`; keep `raw_json JSONB` to preserve full payload and enable ad-hoc queries with GIN when needed.
- **Idempotency:** `INSERT … ON CONFLICT (matched_object_id) DO UPDATE` to refresh titles/URIs, update `last_seen_at`.
- **Codelists:** enrich `PositionSchedule`, remuneration interval, etc., from `/api/codelist/*` at load or via daily cache.

With this improved schema, I can put together a basic DDL sketch with the help of an LLM (full migration later):

```sql
create table job (
  job_id text primary key,                  -- MatchedObjectId
  position_id text,
  position_title text not null,
  position_uri text not null,
  organization_name text,
  department_name text,
  position_location_display text,
  publication_start timestamptz,
  application_close timestamptz,
  pay_min numeric,
  pay_max numeric,
  pay_rate_interval_code text,              -- enriched via codelist
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  source_event_time timestamptz,
  ingest_run_id uuid,
  raw_json jsonb
);

create index if not exists idx_job_raw_json_gin on job using gin (raw_json);

create table job_location (
  job_id text references job(job_id) on delete cascade,
  location_name text,
  country_code text,
  state_code text,
  city text,
  longitude double precision,
  latitude double precision,
  primary key (job_id, location_name)
);

create table job_category (
  job_id text references job(job_id) on delete cascade,
  category_code text,
  category_name text,
  primary key (job_id, category_code)
);

create table job_details (
  job_id text primary key references job(job_id) on delete cascade,
  job_summary text,
  low_grade text,
  high_grade text,
  promotion_potential text,
  hiring_path text[],                       -- or jsonb
  major_duties text[],                      -- or jsonb
  requirements text,
  evaluations text,
  how_to_apply text,
  remote_indicator boolean,
  telework_eligible boolean,
  drug_test_required boolean,
  benefits text,
  benefits_url text
);
```

**Pros** vs the 2 table plan

- Correctly models lists. Enables filtering and indexing
- Easier to answer “all locations near X,” “jobs with category Y,” etc.
- Evolves better as fields change for future-proofing

**Cons**

- Slightly more joins / DDL.
- More ETL code for exploding lists.

> **FoDE:** prefer modelling that supports evolution & correctness; avoid premature over-normalisation, but don’t block future change.

> [!note] `JSONB` alternative
> If pressed for time, keep `job_category` as `jsonb` and index with GIN (`category @> …` queries). Refactor to a child table later with a straightforward migration.

# Planning

## Stack

Notes:

- Cloud-based systems have the benefit of elasticity
- I'm thinking a multi-tier or microservices due to the diversity of tasks to accomplish (?)
- need for containerisation hints at a (partially) microservice architecture (not enough cost or usage for serverless)

Components:

- Scripting
- ETL
- Orchestration
- DBMS
- Cloud
- Infrastructure as Code (IaC)
- Testing
- Monitoring & Alerting
- Containerisation
- CI/CD

### Scripting

- Python (CLI/containerised app)
- Python (AWS Lambda)

#### Python

**Pros:**

- Full control of dependencies & runtime
- Easy local dev
- No 15-min timeout like with Lambda
- Same artefact runs locally and in multiple services of my choosing, like ECS

**Cons:**

- Manually manage the task runner and scheduling

#### Python (AWS Lambda)

**Pros**:

- Zero server mgmt, fast to deploy, native scheduling via EventBridge, can use container images

**Cons**:

- **Max 15-min timeout**
- Cold starts under heavy network I/O
- Less ergonomic for long paginations or large batch inserts.

> [!check] Python in a Docker image
> **Why this:**
>
> - Same artefact locally and in cloud
> - No Lambda 15-min limit
> - Easy dependency management and testing.  
>
**FoDE alignment:** Common components; reversible; low operational complexity.

### ETL

Options:

- **Python**: Minimal, fast, cheap; ideal for modest volumes and HTTP API ingestion.

- **AWS Glue**: Serverless Spark w/ crawlers & Data Catalog, great for large data lakes—**overkill** for this small API ingestion; not free beyond the catalog.

- **PySpark**: Distributed processing—great when you need it, but unnecessary complexity here.

> [!check] Python (requests + pydantic + SQLAlchemy/psycopg)
> **Why this:**
>
> - Small bounded batch
> - HTTP API ingestion
> - Idempotent upserts
> - Enrich with codelists
> - Glue/Spark would add cost/complexity for no gain here
>
> **FoDE alignment:** Keep it simple and build for reliability first.

### Orchestration

Options:

- Python
- AWS Step Function
- Airflow

#### Python

Pros:

- I have existing proficiency
- Great flexibility and creativity for solutions - mix and match libraries in code
- Generally open source with a large range of docs and support
- Free
Cons:
- More boilerplate needed for E2E solutions. Unlikely to be able to build solutions that can stand on their own, especially with containerisation and cloud

#### AWS Step Functions

Pros:

- AWS cloud ecosystem
- Easy integration with Lambda(s)
- 4000 state transitions per month in the free tier (should be enough if running once daily)
Cons:
- Need strict care monitoring to not start incurring costs
- Needed infrastructure understanding of properly provisioning resources with IaC

#### Airflow

Pros:

- Existing proficiency I have
- Market dominance and open source --> lots of docs and support
Cons:
- Core non-scalable components (scheduler, backend database) --> bottlenecks for performance, scale and reliability
  - Maybe not necessary for this task but a consideration for larger scale
- Lacks support for many data-native constructs (schema management, lineage, cataloging)
- Only truly free if self-hosting

> [!check] EventBridge (schedule) → ECS RunTask
> **Why this:**
>
> - Native AWS pattern for scheduled containers
> - Add Step Functions later if I chain stages
>
>**FoDE alignment:** Loosely coupled and plan for failure (retries/alarms).

### DBMS

Options:

- **PostgreSQL**: First-class **JSONB**, **GIN** indexing, **full-text search**, robust upsert (`ON CONFLICT`). Ideal when mixing structured rows with semi-structured job descriptors.

- **MySQL**: Has JSON but no direct JSON GIN; you index JSON via generated columns; fine, but less ergonomic for this use case.

- **SQL Server**: Excellent engine; Express has size limits; managed SQL Server adds license costs; less common in OSS ETL stacks.

> [!check] PostgreSQL (RDS or Aurora Postgres)
> **Why this:** JSONB + GIN, full-text options, and first-class upsert are perfect for semi-structured job descriptors + curated tables.
>
>**FoDE alignment:** Choose components that fit data shape and expected evolution.  

### Cloud

Options:

- AWS
- GCP
- Snowflake

> [!check] AWS
> **Why this:**
>
> - Familiarity
> - Straightforward EventBridge to ECS scheduling
> - Managed Postgres
> - Secrets Manager
>
> **FoDE alignment:** Reduce cognitive load and “always be architecting” - can move later if requirements change.

### IaC

Options:

- Terraform
- Docker

This is a simple decision. A hybrid of both solutions if using cloud services (highly likely) or all Docker if manually hosting (highly unlikely)

> [!check] Terraform for AWS resources + Docker for image
> **Why this:**
>
> - Reproducible infra
> - One command deploys schedule, task, roles, DB, VPC
> - Docker provides immutable app artefact
>
> **FoDE alignment:** DataOps discipline, reproducibility and separation of concerns.

### Testing

#### Unit

Options:

- pytest
- unittest

#### Integration

Options:

- Testcontainers (Postgres module for Python )
- pytest-docker

>[!check] `pytest` + `responses` (HTTP stubs) + Testcontainers (Postgres)
> **Why this:**
>
> - Unit tests for parsing/pagination
> - Integration tests for DDL & upserts against real Postgres in CI
>
> **FoDE alignment:** Software engineering hygiene and fast feedback.

#### Data Quality

Options:

- **pydantic**: validate and coerce API payloads into typed models (fast feedback).
- **Great Expectations**: declarative data tests (not null, value ranges, regex, row counts).
- **dbt tests**: if Ilater move to dbt models, dbt’s built-in tests can enforce constraints in SQL.

> [!check] `pydantic` validation + Great Expectations pre-load checks
> **Why this:**
>
> - Catch type/shape issues at parse time
> - Assert non-nulls, numeric ranges, and sensible coordinates before DB writes
>
> **FoDE alignment:** DataOps mindset and move quality left.

#### E2E

> [!check] A smoke test that runs the container against **USAJOBS sandbox** or a mocked endpoint, writes into a disposable Postgres, and asserts row counts & keys.

### Monitoring & Alerting

Options:

- CloudWatch (AWS)

> [!check] CloudWatch Logs + alarm on task failures + metric filter on “ERROR”
> **Why this:**
>
> - Native AWS visibility
> - Simple and cheap
> - Alerts on run failures
>
> **FoDE alignment:** Operability and plan for failure with actionable signals.

### Containerisation

Options:

- Docker

> [!check] Docker multi-stage + run as non-root + healthcheck
> **Why this:**
>
> - Small images
> - Security baseline
> - Consistent runtime everywhere
>
> **FoDE alignment:** Software engineering best practice and principle of least privilege.

### CI/CD

Options:

- GitHub Actions
- GitLab
- Jenkins
- Bitbucket

> [!check] GitHub Actions to build & push to ECR + Terraform plan/apply (manual or workflow)
> **Why this:**
>
> - One-click build & deploy
> - Reproducible artefacts and infra
>
> **FoDE alignment:** DataOps automation and repeatability.

## Overall Stack Proposal

- **Artifact**: Python ETL in Docker
- **Registry**: Amazon **ECR** (private)
- **Scheduler**: **EventBridge** cron → **ECS Fargate RunTask**
- **Secrets**: AWS **Secrets Manager** for API key & DB creds
- **DB**: **RDS PostgreSQL** (enable encryption at rest; require SSL)
- **Observability**: CloudWatch Logs + alarm on task failure
- **IaC**: Terraform modules for ECR, ECS, RDS, networking, EventBridge
- **CI/CD**: GitHub Actions to build/push Docker image to ECR

### Justification Against Balancing Factors

- **Cost**: Fargate per-run + small RDS instance; avoid Glue/Spark. Use Free Tier credibly for initial testing (need to be careful of RDS hours)
- **Agility**: Containerised Python means iterate rapidly and test locally.
- **Scalability**: If volume grows, increase task size or parallelise pages; later shift to Step Functions or Airflow (MWAA) without changing the core extractor.
- **Simplicity**: Few managed services (ECR, ECS, RDS, Secrets, EventBridge).
- **Reuse & Interoperability**: Generic HTTP to Postgres pattern. Also, codelists allow easy enrichment.

---

# Solution Design

## Architecture

_(diagram placeholder; labels below are the canonical names I’ll use in code & Terraform)_

Flow (daily):

1. EventBridge schedule
2. ECS Fargate RunTask
3. containerised Extractor (Python)
4. USAJOBS API
5. Bronze (raw JSON to S3 + `raw_json` shadow in Postgres)
6. Silver (normalised Postgres: `job`, `job_location`, `job_category`, `job_details`)
7. Gold (read-optimised views, e.g., “Chicago DE roles”)
8. Observability(CloudWatch Logs + metric filter + alarm; optional DLQ).

This layout mirrors the medallion pattern (Bronze/Silver/Gold) while acknowledging we’re landing curated tables in Postgres instead of a lakehouse; the pattern is still valid as a logical quality/processing progression.

> **FoDE alignment:** common components; plan for failure (idempotent upserts, retries); loose coupling (stateless task); security by default (KMS, TLS, least privilege).

## Logic Flow

1. **Kickoff & run context**
    - Generate `ingest_run_id` (UUID), collect config (radius, page size, etc.).
    - Log a structured run start event (JSON to stdout) with version, env, and run_id (12-factor log style). CloudWatch picks up stdout; alarms are driven by log metric filters.

2. **Discover pagination**
    - Call Search API with `Keyword="data engineering"`, `ResultsPerPage=500`, `Page=1`, and (for the Chicago slice) `LocationName=Chicago&Radius={cfg}`.
    - Read `SearchResultCountAll` to compute total pages; default to sequential paging; optional bounded concurrency (4–8 workers) later if needed.

3. **Ingest (Bronze)**
    - For each page: capture the raw response to S3 (`s3://…/bronze/date=YYYY-MM-DD/run=…/page=N.json`) with an S3 Lifecycle to transition or expire older payloads (e.g., transition to Glacier after 30 days, expire after 180).
    - Parse each `SearchResultItems[*]`.

4. **Validate & enrich**
    - Parse each record into Pydantic v2 models (`MatchedObjectDescriptor`, `Details`, the list fields) with coercion and custom validators for dates, URLs, pay ranges, and geo bounds. If parse fails → place into a quarantine list for reporting, not crash the run.
    - Resolve code lists (e.g., `PositionSchedule`) via `/codelist` endpoints at runtime or using a daily cache; attach human-readable labels.

5. **Normalise (Silver)**
    - Split into:
        - `job` (1:1): identity, core attributes, remuneration summary, key dates, `raw_json`, lineage fields.
        - `job_location` (N:1): one row per location in `PositionLocation`.
        - `job_category` (N:1): one row per category.
        - `job_details` (1:1): long text fields & flags from `UserArea.Details`.
    - Keep `JobGrade` and `HiringPath` as either child tables or JSONB on `job_details` initially (trade-off documented; easy GIN indexing later). Decision captured in ADR-0004.

6. **Load (idempotent)**
    - Use UPSERTs with `ON CONFLICT (job_id)` in a single transaction per batch; set `last_seen_at=NOW()` on each touch. Rows not seen in a run are not deleted; if “tombstones” are later needed, mark with `inactive_since`. (ADR-0005.)
    - Commit per page to balance throughput with recoverability.

7. **Gold**
    - Create views for end users (e.g., `vw_chicago_de_jobs`) that join the normalised tables and apply geospatial filters. Without PostGIS, implement a Haversine distance predicate against Chicago’s centroid (41.8781, -87.6298) and a configurable miles radius; with PostGIS later, replace predicate with `ST_DWithin`. Views are durable and composable.

8. **Post-run**
    - Emit a run summary: totals, inserted/updated counts, quarantined items, and S3 pointers. CloudWatch metric filter on the string `level=ERROR` drives an alarm; EventBridge rule uses DLQ for undeliverable events.

**Resilience notes**

- HTTP calls wrapped with timeouts and retries using exponential backoff with jitter to avoid retry storms; `tenacity` handles policy & jitter.
- DB writes use statement timeouts (e.g., session-level `statement_timeout`) to avoid wedged sessions during network blips.

## Transformation

### Bronze → Silver (validation gates)

**Field-level rules (representative)**

- `PositionTitle`: non-null, length ≤ 512.
- `PositionURI`, `ApplyURI[]`: valid HTTP(S) URLs.
- `PayMinimumRange`, `PayMaximumRange`: numeric; `min ≤ max`; positive; `RateIntervalCode` ∈ known set via codelist.
- Dates (`PublicationStartDate`, `ApplicationCloseDate`, `PositionStartDate`, `PositionEndDate`): RFC 3339 parseable; `PublicationStartDate ≤ ApplicationCloseDate`.
- Geo: `Latitude ∈ [-90,90]`, `Longitude ∈ [-180,180]`.  (Validated in Pydantic; echoed as Great Expectations checks in the pre-load suite.)

**Table-level rules**

- **Uniqueness**: `job.job_id` (USAJOBS stable identifier).
- **Referential integrity**: every `job_location.job_id` & `job_category.job_id` must exist in `job`.
- **Cardinality**: at least one `job_location` per `job`.
- **Row count sanity**: total rows == API `SearchResultCountAll` (allowing for quarantined records).

### Silver → Gold (consumer semantics)

- View naming is role-based: `vw_de_jobs_all`, `vw_de_jobs_chicago_{radius_mi}`.
- Gold presents denormalised columns for simple BI usage, but is view-backed to keep mutation in Silver only.

> **FoDE alignment:** separate concerns per lifecycle stage; reversible transformations; serving optimised for consumers.

## Design Patterns

### Storage & Retention

- **S3 Bronze**: retain 30 days in Standard, transition to Glacier Instant Retrieval at day 30, expire at day 180 (lifecycle policy).
- **Postgres**: PITR and automated backups enabled on RDS. (Captured in ADR-0008.)

### Security

- Secrets in AWS Secrets Manager; the extractor reads at runtime—never embed in Terraform variables that get serialised into tfstate. Treat state as sensitive; avoid writing secrets to state (e.g., reference secrets via data sources or runtime environment).
- TLS to RDS; encryption at rest (KMS) for RDS and S3.

### Fault Tolerance

- **HTTP**: timeout per call (e.g., 10s), exponential backoff with jitter, capped retries, and circuit-breaker semantics on repeated 5xx/429. AWS explicitly recommends jitter to prevent thundering herds.
- **DB**: session `statement_timeout` (e.g., 30s) and short transactions; connection retry (bounded), fail the page and continue.
- **Scheduling**: EventBridge → ECS with DLQ and retry policy on the rule.

### Idempotency

- Writes use **UPSERT** keyed by `job_id`; set `last_seen_at` every run. Optional SCD2 can be added later by splitting stable identity from versioned attributes (new `job_history` table).

### Medallion Architecture (adapted)

- **Bronze**: raw API responses (S3), `raw_json` copy on `job`.
- **Silver**: normalised Postgres tables with quality gates.
- **Gold**: analytic views & materialised views if needed.

### Data Lineage

- Lightweight lineage: `ingest_run` table (run id, timing, counts), foreign key `job.ingest_run_id`, and S3 object keys.
- If/when an orchestrator is added (Airflow, Dagster), emit OpenLineage events to a Marquez backend for end-to-end job/dataset lineage.

### CDC

- The source is a search API (no change feed). I’ll approximate change tracking via daily snapshot diffs plus `last_seen_at`. If a vacancy disappears from the API, I can mark `inactive_since` after N missed runs. (If full history is later required, introduce a `job_version` table and compute deltas.)

### Data Quality

- Pydantic at parse time (fail fast on shape/type).
- Great Expectations pre-load suite to enforce constraints (non-nulls, ranges, regex URL, date ordering) and to produce human-readable Data Docs.

### DataOps (Automation, Observability, Incident Response)

- **Automation**: CI runs unit + integration tests; build & push image; Terraform plan.
- **Observability**: CloudWatch Logs; **metric filters** on `level=ERROR` → alarm → notify.
- **Incident response**: capture run context in logs; alarms route to SNS/email; follow AWS Well-Architected Operational Excellence guidance for runbooks and game days.

> **FoDE alignment:** “Always be architecting,” DataOps discipline, measurable SLAs.

## Logic

### Paradigms

- Keep the executable stateless and idempotent; “functional core, imperative shell.”
- Prefer composition over inheritance; thin service objects.

### Modularity (packages/modules)

- `config/` – config models & env parsing.
- `http/` – API client with retries/backoff (tenacity), codelist client.
- `models/` – Pydantic models for payloads; typed DTOs for Silver.
- `transform/` – normalization & mapping functions.
- `dq/` – Great Expectations suite & fixtures.
- `db/` – SQL (queries, upserts), connection management.
- `runner/` – main entrypoint, run orchestration, summary.
- `utils/` – logging, metrics, timing.

> **FoDE alignment:** separation of concerns; reversible decisions.

## Build

- Use a `pyproject.toml` (PEP 621) instead of `setup.py`. Configure build backend (setuptools or Hatch), tool configs (ruff/black/mypy) in one place.
- Pin runtime dependencies in `requirements.txt` (or generate via pip-tools later).

> **FoDE alignment:** choose common components; simplicity & maintainability.

## Error Handling

- **Classification**:
  - _Retryable_: HTTP 429/5xx, transient DNS/TLS, socket timeouts → backoff+**jitter** (cap attempts).
  - _Non-retryable_: 4xx (except 429), validation errors → quarantine and continue.
  - _DB_ constraint violations → log with run_id, include sample key, increment failure metrics, continue batch.
- **Fail-fast on config** (missing secret, invalid DSN).
- **Per-page isolation**: a failing page doesn’t poison the entire run.

## Logging

- Structured JSON logs with keys: `ts`, `level`, `run_id`, `event`, `job_id` (when applicable), counts, durations. Emit to stdout (12-factor), consumed by CloudWatch; use structlog or stdlib logging + JSON formatter. Add a `TRACE`toggle for local debugging.

> **FoDE alignment:** observability & auditability.

## Code Cleanliness

- **Type hints**: (PEP 484) + **mypy** in CI.
- **Docstrings**: (PEP 257 style) on public functions.
- **Formatting & lint**: `black` + **ruff** (ruff also sorts imports & catches a broad set of issues).

## Formatting

- Enforce with pre-commit hooks: `ruff`, `black`, `mypy` (fast incremental checks).

## Docs

- **README** should cover: purpose, architecture diagram, quick start (local & Docker), configuration (env vars), running tests, deployment steps, troubleshooting, and ADR index.

## Testing

### Unit

- Pure functions in `transform/` and validators in `models/` (pytest).

### Integration

- **Testcontainers**: spin up ephemeral Postgres; run migrations; test UPSERT correctness and FK integrity. (If preferred later, `pytest-docker` works too.)

### Data Quality

- Minimal **Great Expectations** suite run against a temp schema: non-nulls, ranges, regex URL, date ordering, referential integrity (row counts per job).

### End-to-End

- Record/replay a sample API page (VCR-style fixture) or point at the live API with a small page size; assert row counts, a few content spot-checks, and that `ingest_run` is recorded.

> **FoDE alignment:** testable units; trust but verify; SLIs are measurable.

## Helpful Resources

Generated by LLM:

- Databricks medallion overview (for Bronze/Silver/Gold language). [Microsoft Learn](https://learn.microsoft.com/en-us/azure/databricks/lakehouse/medallion?utm_source=chatgpt.com)
- Great Expectations quickstart. [Great Expectations](https://docs.greatexpectations.io/docs/0.18/oss/tutorials/quickstart/?utm_source=chatgpt.com)
- OpenLineage & Marquez (lineage expansion path). [openlineage.io](https://openlineage.io/docs/?utm_source=chatgpt.com)
- 12-Factor logs and structured logging with structlog. [12factor](https://12factor.net/logs?utm_source=chatgpt.com)[structlog](https://www.structlog.org/?utm_source=chatgpt.com)
- AWS S3 lifecycle; EventBridge DLQ; CloudWatch metric filters & alarms; EventBridge Scheduler for ECS. [AWS Documentation+4AWS Documentation+4AWS Documentation+4](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html?utm_source=chatgpt.com)

## Pitfalls to Avoid (and how I’m avoiding them)

As advised before the task:

- **“ETL couldn’t reach Postgres.”**  
    Set explicit timeouts, short transactions, and connection retries; verify connectivity in an **integration test** with Testcontainers; use RDS security groups/VPC endpoints correctly.
- **Rushed structure.**  
    This doc, ADRs, and the module layout enforce a clear separation of concerns.
- **Low code quality.**  
    Types, docstrings, `black`+`ruff`, meaningful logging, and focused tests.
- **LLM-heavy README.**  
    Keep it concise and operational; link to ADRs and this design doc.

### (Optional) Chicago “Gold” view notes

- API-side filtering is primary. The **Gold** view adds a guard for edge cases: jobs with multiple locations get included if **any** location falls within `{radius_mi}` of the Chicago centroid, using a Haversine predicate (no PostGIS dependency). If PostGIS is enabled later, switch to `ST_DWithin` for accuracy.
