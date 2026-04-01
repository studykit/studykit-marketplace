---
name: container-view
disable-model-invocation: true
description: Structurizr DSL container view syntax reference. Use when creating or debugging C4 container diagrams that zoom into a software system to show its applications, services, and data stores.
---

> Source: https://docs.structurizr.com/dsl/cookbook/container-view/

# Container View Reference

Zooms into a software system to show its containers (web apps, APIs, databases, message queues, etc.).

## Syntax

```
container <software system identifier> [key] [description] {
    include *
    autoLayout [tb|bt|lr|rl]
}
```

`include *` adds all containers within the system, plus all directly connected people and software systems from outside.

## Container Definition

Inside a `softwareSystem` block:

```
container <name> [description] [technology] [tags] {
    [component definitions]
    [-> relationships]
}
```

## Example

```
workspace {

    model {
        user = person "User"
        system = softwareSystem "E-Commerce Platform" {
            webApp = container "Web Application" "Serves the frontend" "React"
            apiGateway = container "API Gateway" "Routes API requests" "Kong"
            orderService = container "Order Service" "Manages orders" "Java and Spring Boot"
            database = container "Database" "Stores orders and products" "PostgreSQL" {
                tags "Database"
            }
            messageQueue = container "Message Queue" "Async event processing" "RabbitMQ" {
                tags "Queue"
            }
        }

        user -> webApp "Browses products using" "HTTPS"
        webApp -> apiGateway "Makes API calls to" "JSON/HTTPS"
        apiGateway -> orderService "Routes to"
        orderService -> database "Reads from and writes to" "SQL/TCP"
        orderService -> messageQueue "Publishes events to" "AMQP"
    }

    views {
        container system "Containers" {
            include *
            autoLayout
        }

        styles {
            element "Database" {
                shape Cylinder
            }
            element "Queue" {
                shape Pipe
            }
        }
    }

}
```

## Multiple Software Systems

To show containers from multiple systems, use `include` with specific identifiers:

```
container systemA {
    include *
    include systemB.container1
}
```
