---
name: dynamic-view
disable-model-invocation: true
description: Structurizr DSL dynamic view syntax reference. Use when creating or debugging C4 dynamic diagrams that show runtime behavior, interaction flows, or sequence-like step-by-step scenarios.
---

> Source: https://docs.structurizr.com/dsl/cookbook/dynamic-view/

# Dynamic View Reference

Shows runtime behavior as a sequence of interactions between elements. Similar to UML sequence diagrams but uses the C4 model elements.

## Syntax

```
dynamic <*|software system identifier|container identifier> [key] [description] {
    <source> -> <destination> [description] [technology]
    [autoLayout]
    [title]
}
```

Scope determines which elements can appear:
- `*` — any element
- `<software system>` — containers within that system plus external people/systems
- `<container>` — components within that container plus external elements

## Ordering

Interactions are automatically numbered in the order they appear. You can also specify explicit ordering:

```
dynamic system {
    1: user -> webApp "Opens page"
    2: webApp -> api "Requests data"
    3: api -> database "Queries"
}
```

## Multiple Dynamic Views

Create separate views for different scenarios by giving each a unique key:

```
dynamic system "login" "Login Flow" {
    user -> webApp "Submits credentials"
    webApp -> authService "Validates"
    authService -> database "Checks user record"
    autoLayout lr
}

dynamic system "checkout" "Checkout Flow" {
    user -> webApp "Places order"
    webApp -> orderService "Creates order"
    orderService -> paymentService "Processes payment"
    autoLayout lr
}
```

## Example

```
workspace {

    model {
        customer = person "Customer"
        system = softwareSystem "E-Commerce" {
            spa = container "SPA" "Frontend application" "React"
            api = container "API" "Backend service" "Spring Boot"
            auth = container "Auth Service" "Authentication" "Spring Security"
            db = container "Database" "Data store" "PostgreSQL"
            notification = container "Notification Service" "Sends emails" "Node.js"
        }

        customer -> spa "Uses"
        spa -> api "Calls" "JSON/HTTPS"
        api -> auth "Authenticates via"
        api -> db "Reads/writes"
        api -> notification "Triggers notifications"
    }

    views {
        dynamic system "SignUp" "User registration flow" {
            title "User Registration"
            customer -> spa "Fills in registration form"
            spa -> api "Submits registration data"
            api -> auth "Creates user account"
            auth -> db "Stores user credentials"
            api -> notification "Sends welcome email"
            autoLayout lr
        }

        dynamic system "Login" "User login flow" {
            title "User Login"
            customer -> spa "Enters credentials"
            spa -> api "Submits login request"
            api -> auth "Validates credentials"
            auth -> db "Looks up user"
            autoLayout lr
        }
    }

}
```
