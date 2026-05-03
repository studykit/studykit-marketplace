# Logging — Python

Layered on top of `general.md`. These rules are Python-specific.

## Use `%`-style placeholders, not f-strings, in log calls

```python
# Good — formatting is deferred; skipped entirely if level is disabled
logger.info("processed %d records for tenant %s", count, tenant_id)

# Bad — string is built even when INFO is disabled
logger.info(f"processed {count} records for tenant {tenant_id}")
```

The Python logging library only formats the message when the level is enabled. f-strings defeat that optimization, and on hot paths the cost is real.

Exception: structured-logging libraries (`structlog`, `loguru`) accept kwargs and have their own conventions — follow the library's docs.

## Don't catch-and-log without re-raising

Swallowing an exception and logging it converts a failure into silent success. Either let it propagate (the framework will log it) or re-raise after logging:

```python
# Good
try:
    do_work()
except SomeError:
    logger.exception("do_work failed")
    raise

# Bad — caller has no idea anything went wrong
try:
    do_work()
except SomeError:
    logger.exception("do_work failed")
```

The exception to this rule: a top-level handler at the request/job boundary that translates exceptions into responses.

## Don't configure logging in library code

Library/package code only *gets* loggers and emits records. Calling `logging.basicConfig()`, adding handlers, or setting levels belongs in the application entry point (or the test fixture), never in importable modules. A library that configures logging will overwrite the application's settings.
