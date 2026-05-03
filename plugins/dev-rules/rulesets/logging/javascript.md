# Logging — JavaScript / TypeScript

Layered on top of `general.md`. Applies to `.js`, `.ts`, `.jsx`, `.tsx`, `.mjs`, `.cjs` files.

## Never log inside React render functions

A `console.log` (or any logger call) inside a render function fires on every re-render, often dozens of times per interaction. Move the log into an effect (`useEffect`) or an event handler.

## Async errors: log at the rejection boundary

A rejected promise that is never awaited becomes an unhandled rejection. Either:

- `await` the promise inside a `try/catch` that logs.
- Attach `.catch(err => log.error({ err }, "background task failed"))`.
- Register a global `unhandledRejection` handler at the process entry that logs.

Silent unhandled rejections are the #1 source of "the job just stopped working and we don't know why" incidents.
