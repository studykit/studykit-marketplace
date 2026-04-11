> Source: https://docs.structurizr.com/dsl/cookbook/component-view/

# Component View Reference

Zooms into a container to show its internal components (controllers, services, repositories, etc.).

## Syntax

```
component <container identifier> [key] [description] {
    include *
    autoLayout [tb|bt|lr|rl]
}
```

`include *` adds all components within the container, plus directly connected containers, people, and software systems.

## Component Definition

Inside a `container` block:

```
component <name> [description] [technology] [tags] {
    [-> relationships]
}
```

## Example

```
workspace {

    model {
        user = person "User"
        system = softwareSystem "System" {
            apiServer = container "API Server" "Backend API" "Spring Boot" {
                authController = component "Auth Controller" "Handles login and registration" "Spring Controller"
                userService = component "User Service" "Business logic for users" "Spring Service"
                userRepo = component "User Repository" "Data access for users" "Spring Repository"
            }
            database = container "Database" "Stores user data" "PostgreSQL" {
                tags "Database"
            }
        }

        user -> authController "Authenticates via" "HTTPS"
        authController -> userService "Uses"
        userService -> userRepo "Uses"
        userRepo -> database "Reads from and writes to" "SQL"
    }

    views {
        component apiServer "Components" {
            include *
            autoLayout
        }

        styles {
            element "Database" {
                shape Cylinder
            }
        }
    }

}
```
