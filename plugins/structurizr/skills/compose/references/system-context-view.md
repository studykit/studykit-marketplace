> Source: https://docs.structurizr.com/dsl/cookbook/system-context-view/

# System Context View Reference

## System Landscape View

Shows all people and software systems. No scoping required.

```
systemLandscape [key] [description] {
    include *
    autoLayout [tb|bt|lr|rl]
}
```

## System Context View

Shows one software system with its direct relationships (users, external systems).

```
systemContext <software system identifier> [key] [description] {
    include *
    autoLayout [tb|bt|lr|rl]
}
```

`include *` adds the software system in scope plus all directly connected people and software systems.

## Example

```
workspace {

    model {
        customer = person "Customer" "A bank customer"
        bankingSystem = softwareSystem "Online Banking" "Allows customers to manage accounts"
        emailSystem = softwareSystem "E-mail System" "Sends notifications" {
            tags "External"
        }

        customer -> bankingSystem "Manages accounts using"
        bankingSystem -> emailSystem "Sends e-mails using"
    }

    views {
        systemContext bankingSystem "Context" {
            include *
            autoLayout lr
        }

        styles {
            element "Person" {
                shape Person
            }
            element "External" {
                background #999999
                color #ffffff
            }
        }
    }

}
```

## Include/Exclude

- `include *` — default set of elements
- `include <identifier>` — add a specific element
- `exclude <identifier>` — remove a specific element
- `include "element->element"` — include a specific relationship
