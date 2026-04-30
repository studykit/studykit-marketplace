# a4 — usecase abstraction guard

> **Audience:** Workspace authors writing `<project-root>/a4/usecase/*.md` files (or LLMs editing them on the user's behalf). Cited from `./usecase-authoring.md` § Abstraction discipline.

Flow steps and all other UC fields MUST describe **user-level actions only**. Before writing any flow step, verify it contains no implementation terms.

## Banned Terms and Concepts

- **Technology:** API, REST, GraphQL, HTTP, JSON, XML, webhook
- **Storage:** database, DB, SQL, cache, queue, index, schema, record, row
- **Infrastructure:** server, container, microservice, deployment, worker, job, cron
- **System internals:** "the system queries", "data is stored", "triggers a request", "sends a payload"

## How to Convert

| Implementation language | User-level language |
|------------------------|---------------------|
| "the system queries the database for matching records" | "matching results appear on screen" |
| "sends a webhook to the integration service" | "the connected tool is notified" |
| "caches the result for 5 minutes" | "results load instantly on the next visit" |
| "API returns a 200 status" | "the action completes successfully" |

## Where to Apply

Check these fields in every Use Case:

- **Goal** — must express what the actor wants, not how the system delivers it
- **Situation** — must describe an observable trigger, not a system event
- **Flow** — every step must be a user action or observable system response
- **Expected Outcome** — must be something verifiable by a person, not a system state
