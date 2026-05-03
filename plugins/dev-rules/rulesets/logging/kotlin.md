# Logging — Kotlin

Layered on top of `general.md`. Applies to `.kt` and `.kts` files.

Kotlin runs on the JVM, so the underlying logging stack is the same as Java (SLF4J + a binding). The differences below are Kotlin-idiom-specific.

## Coroutines: propagate MDC explicitly

Coroutines hop threads, and MDC is thread-local. Without explicit propagation, MDC values vanish on the first suspension point.

```kotlin
withContext(MDCContext()) {
    log.info { "still in request scope" }
}
```

`MDCContext()` from `kotlinx-coroutines-slf4j` snapshots the current MDC and re-applies it on every dispatch. Add it to the coroutine context at the request-scope boundary (e.g., where you launch the coroutine handling the request).

## `data class` `toString()` can leak secrets

`data class User(val email: String, val passwordHash: String)` has an auto-generated `toString` that includes every field. Logging a data class instance prints the secret. Override `toString()` on classes that hold credentials, or never log them whole — log specific safe fields.

## Don't use `error()` (the stdlib) for log-and-throw

Kotlin's stdlib `error("msg")` throws `IllegalStateException` and does **not** log. Many developers mis-read it as a logger call. If you mean "log at error level," use `log.error { ... }`. If you mean "throw," use `error("...")` and let the boundary log it.
