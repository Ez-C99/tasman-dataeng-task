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
2. Theory recap
3. Sample data pull & initial analysis
4. Planning (including comparison, selection and justification)
5. Design & Implementation
6. Post-implementation review

# Gather Requirements

## Task Brief
>
>[!question] What is the problem to be solved?

I need to present data from the USA Jobs database in my own database

>[!question] What is the task to solve the problem?

Programmatically extracting data from the USA Jobs database, filter and format it then load it into a database. All of this must be in a containerised ETL solution that is easily deployable with the minimum required software and skills.

> What is meant by loading the data **"durably"**?

> Is there anything here I’m inexperienced on or unable to do? How do I overcome this?

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

>[!question] Do I run the API request batch sequentially or concurrently?
>
>- How does affect performance and retrieval time? (Worth it or negligible? Impact on scalability?)
>- Does this have any negative effect on the API constraints?
>
> For the sake of this task and the low bandwidth, low data size and low daily demand, sequential should be fine but cases of larger throughput high demand would need parallelism/concurrency. This also means I avoid testing the API limits and constraints, but this would also need to be a consideration for the larger data case just mentioned

Based on these insights, there’s a new base case API request (for now):
`https://data.usajobs.gov/api/search?Keyword=data engineering&ResultsPerPage=500&Page=1`

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
Results Schema
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
  
Details Schema
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
> Normalise all `"ApplyURI"` fields from `list<str>` to `str`
>
> - There only ever seems to be a single apply link in the field

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

| Field      | Type        | Notes                                              |
| ---------- | ----------- | -------------------------------------------------- |
| created_at | `timestamp` | Lineage and auditing for records                   |
| updated_at | `timestamp` | More lineage in case of DB operations e.g. queries |
| deleted_at | `timestamp` | Soft delete indicator if not null                  |
