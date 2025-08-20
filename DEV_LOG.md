# Dev Log

A diary of the design and development of my solution

## 2025-08-19 - ETL Featureset Work

### Actions

- Iterated through a whole bunch of features for the project
  - [x] starter files & config
  - [x] bronze capture infra and extraction helpers
  - [x] initial pydantic validation models
  - [x] bronze to silver normalisation and transformation
  - [x] loader with idempotent upserts
- Next tasks
  - [x] pre-load gate Great Expectations validation (in progress)
  - [ ] EventBridge -> ECS RunTask scheduling
  - [ ] secrets & config
  - [ ] security & durability (DB and network)
  - [ ] observability (logs and alarms)
  - [ ] testing: unit, integration, E2E
  - [ ] CI/CD with GutHub Actions (*)
  - [ ] Gold views & serving (*)
  - [ ] performance & scale hardening (*)
  - [ ] docs and ADR maintenance
  - [ ] release & versioning (*)

> [!note]
>
> - There's a time constraint on the project so anytthing with "(*)" next to it is of a lower priority tier for the solution, in the context of what's needed to demonstrate a viable E2E solution
> - Anything asterisked can be spoken about in an interview to explain how I'd do it

### Notes

- Not a lot of sleep over the last 2 days when combining this with life and work responsiblities but nearly ready to deploy

---

## 2025-08-18 - Design doc and architecture finalising + development initialisation

### Actions

- Cross-referenced my completed design doc with fundamentals, best practices and an LLM to refine it.
- Generated the ADRs with LLM based on my finalised deisgn and architecture (see docs/architecture/decisions)
- Refined the solution design based on ADRs
- Setup the starting repo structure, based on design and architecture

### Notes

- Had to work quite a bit later than 5pm usual to fix some bugs but nothing a little nap to re-energise can't fix.
- Late/early hours finished but good progress made again. There's still some documentation stuff to refine and clarify but I've seen enough architecture for one night.
- With the base structure complete now, I can stop committing straight to main and work in branches for each component of the solution.

### To Do

- Implement starter files to support development (pre-commit, requirements, pyproject, docker files etc)
- Build helper functions for ETL process
- Implement DDL
- Implement GitHub Ac
- Produce architecture diagram for design doc (can be left until end of task in case architecture changes)

---

## 2025-08-17 - Completed the technical desdign doc

### Actions

- Completed the technical design doc and initial data analysis (mostly).
- Designed the first iteration of the schema, based on the analysis.
- Mostly completed stack design choice and justifications,
- Got a good way into implementation architecture, design and planning

### Notes

- It was another slightly disjointed working session since it was my mum's birthday now so I couldn't do anything in the morning and had to travel back to my flat in the evening. I progressed well in whatever time I had available though.

---

## 2025-08-16 - Finished requirements gathering and started design doc

### Actions

- Finished gathering requirements from the brief and put together high level solution overview diagram at the bottom.
- Started the [Technical Design & Planning]() doc.
- Progressed to the initial data pull and analysis from the API with Postman in the early hours of the next day.

### Notes

- I could only really work on the design and planning doc for a couple hours, from the late morning to early afternoon, since it was my aunt's birthday and she was visiting from Ghana. I had to travel from my flat to my family home but I liked the way the solution was coming together.
- Managed to work on it more in the very late night.

---

## 2025-08-15 - Brief insights and requirements gathering

### Actions

- Started the initial insights and requirements gathering from the brief by annotating and notetaking over the task brief with my iPad.
- The doc is linked here: [Brief Insights and Requirements](docs/Brief_Insights_and_Requirements.pdf).

### Notes

- Tired from work and the week but I finally had the time and energy to properly start the task, after some post-work rest.

---

## 2025-08-14 - Fundamentals and theory recap

### Actions

- Recapped the O'Reilly Fundamentals of Data Engineering book to revise the concepts I want to present in my solution.

### Notes

- As I explained to Aileen Tolentino in email the busy week wouldn't allow me to truly get onto the task until later but I had to do whatever I could to prepare.
- Just like in basketball (and basketball imitates life), fundamentals are key.

---

## 2025-08-xx - Title

### Actions

- Description

### Notes

- Description
