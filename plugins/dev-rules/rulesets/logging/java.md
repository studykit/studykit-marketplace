# Logging — Java

Layered on top of `general.md`. Applies to `.java` files.

## Don't catch-and-swallow

A bare `catch` that logs and returns turns a failure into silent success. Either re-throw, wrap in a runtime exception, or translate to a domain error at the boundary. The only place catch-and-log-only is acceptable is the outermost request/job handler.

## Use MDC for correlation context

```java
MDC.put("requestId", requestId);
try {
    handleRequest();
} finally {
    MDC.clear();
}
```

Configure the appender pattern to include MDC keys (`%X{requestId}`) and every log line in the request scope picks them up automatically. This is the standard Java way to satisfy the "always include correlation id" rule from `general.md`.

In reactive code (Project Reactor, RxJava, virtual threads with structured concurrency), MDC propagation is non-trivial — use the framework's context propagation hooks rather than rolling your own.

## Don't log and rethrow at every layer

Logging the same exception three times as it bubbles up creates duplicate noise and confuses post-incident analysis. Log it once at the layer that has the most context (usually the boundary), then re-throw.
