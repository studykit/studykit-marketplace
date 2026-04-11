> Source: https://docs.structurizr.com/dsl/cookbook/

# Structurizr DSL Cookbook

Practical examples for common diagram patterns.

## Table of Contents

1. [System Context View](#system-context-view)
2. [Container View](#container-view)
3. [Component View](#component-view)
4. [Deployment View](#deployment-view)
5. [Dynamic View](#dynamic-view)
6. [Filtered View](#filtered-view)
7. [Groups](#groups)
8. [Element Styles](#element-styles)
9. [Relationship Styles](#relationship-styles)
10. [Complete Example](#complete-example)

---

## System Context View

Shows a software system in scope with its users and external dependencies.

```
workspace {

    model {
        u = person "User"
        s = softwareSystem "Software System"

        u -> s "Uses"
    }

    views {
        systemContext s {
            include *
            autoLayout lr
        }
    }

}
```

---

## Container View

Zooms into a software system to show its containers (applications, data stores).

```
workspace {

    model {
        u = person "User"
        s = softwareSystem "Software System" {
            webapp = container "Web Application"
            database = container "Database"
        }

        u -> webapp "Uses"
        webapp -> database "Reads from and writes to"
    }

    views {
        container s {
            include *
            autoLayout lr
        }
    }

}
```

---

## Component View

Zooms into a container to show its internal components.

```
workspace {

    model {
        u = person "User"
        s = softwareSystem "Software System" {
            webapp = container "Web Application" {
                c1 = component "Component 1"
                c2 = component "Component 2"
            }
            database = container "Database"
        }

        u -> c1 "Uses"
        c1 -> c2 "Uses"
        c2 -> database "Reads from and writes to"
    }

    views {
        component webapp {
            include *
            autoLayout lr
        }
    }

}
```

---

## Deployment View

Shows how containers are deployed onto infrastructure.

```
workspace {

    model {
        u = person "User"
        s = softwareSystem "Software System" {
            webapp = container "Web Application" "" "Spring Boot"
            database = container "Database" "" "Relational database schema"
        }

        u -> webapp "Uses"
        webapp -> database "Reads from and writes to"

        development = deploymentEnvironment "Development" {
            deploymentNode "Developer Laptop" {
                containerInstance webapp
                deploymentNode "MySQL" {
                    containerInstance database
                }
            }
        }
    }

    views {
        deployment * development {
            include *
            autoLayout lr
        }
    }

}
```

---

## Dynamic View

Shows runtime behavior and interaction sequences.

```
workspace {

    model {
        customer = person "Customer"
        onlineBookStore = softwareSystem "Online book store" {
            webapp = container "Web Application"
            database = container "Database"
        }

        customer -> webapp "Browses and makes purchases using"
        webapp -> database "Reads from and writes to"
    }

    views {
        dynamic onlineBookStore {
            title "Request past orders feature"
            customer -> webapp "Requests past orders from"
            webapp -> database "Queries for orders using"
            autoLayout lr
        }

        dynamic onlineBookStore {
            title "Browse top 20 books feature"
            customer -> webapp "Requests the top 20 books from"
            webapp -> database "Queries the top 20 books using"
            autoLayout lr
        }
    }

}
```

---

## Filtered View

Creates a filtered subset of a base view using tags.

```
workspace {

    model {
        a = softwareSystem "A" {
            tags "Tag 1"
        }
        b = softwareSystem "B" {
            tags "Tag 2"
        }
        c = softwareSystem "C" {
            tags "Tag 3"
        }

        a -> b
        b -> c
    }

    views {
        systemLandscape "landscape" {
            include *
            autolayout lr
        }

        filtered "landscape" include "Tag 1,Tag 2,Relationship" "landscape1"
        filtered "landscape" exclude "Tag 1" "landscape2"
        filtered "landscape" include "Element,Relationship" "landscape-all"
    }

}
```

---

## Groups

Organize elements into named groups with visual boundaries.

### Basic groups

```
workspace {

    model {
        group "Company 1" {
            a = softwareSystem "A"
        }

        group "Company 2" {
            b = softwareSystem "B"
        }

        a -> b
    }

    views {
        systemLandscape {
            include *
            autolayout lr
        }
    }

}
```

### Nested groups

```
workspace {

    model {
        properties {
            "structurizr.groupSeparator" "/"
        }

        group "Company 1" {
            group "Department 1" {
                a = softwareSystem "A"
            }

            group "Department 2" {
                b = softwareSystem "B"
            }
        }

        a -> b
    }

    views {
        systemLandscape {
            include *
            autolayout lr
        }

        styles {
            element "Group:Company 1/Department 1" {
                color #ff0000
            }
            element "Group:Company 1/Department 2" {
                color #0000ff
            }
        }
    }

}
```

---

## Element Styles

Apply visual styles to elements using tags.

```
workspace {

    model {
        a = softwareSystem "A" {
            tags "Tag 1"
        }
        b = softwareSystem "B"
        c = softwareSystem "C"

        a -> b
        b -> c
    }

    views {
        systemLandscape {
            include *
            autolayout lr
        }

        styles {
            element "Tag 1" {
                background #1168bd
                color #ffffff
                shape RoundedBox
            }
        }
    }

}
```

---

## Relationship Styles

Style all relationships or individual ones via tags.

### Style all relationships

```
styles {
    relationship "Relationship" {
        color #ff0000
    }
}
```

### Style individual relationships

```
a -> b
b -> c {
    tags "Tag 1"
}

styles {
    relationship "Tag 1" {
        color #ff0000
    }
}
```

---

## Complete Example

A realistic multi-view workspace combining multiple patterns.

```
workspace "Online Banking System" "Architecture of the online banking system" {

    model {
        customer = person "Customer" "A customer of the bank" "Customer"
        supportStaff = person "Support Staff" "Customer support within the bank"

        bankingSystem = softwareSystem "Online Banking System" "Allows customers to manage accounts" {
            webApp = container "Web Application" "Delivers static content and the SPA" "Java and Spring MVC"
            spa = container "Single-Page Application" "Provides banking functionality" "JavaScript and React"
            apiServer = container "API Server" "Provides banking API" "Java and Spring Boot" {
                authController = component "Auth Controller" "Handles authentication" "Spring Controller"
                accountController = component "Account Controller" "Provides account operations" "Spring Controller"
                securityComponent = component "Security Component" "Authentication and authorization" "Spring Security"
            }
            database = container "Database" "Stores user and account data" "PostgreSQL" {
                tags "Database"
            }
        }

        emailSystem = softwareSystem "E-mail System" "Sends e-mails to customers" {
            tags "External"
        }

        customer -> webApp "Visits" "HTTPS"
        customer -> spa "Views accounts using"
        webApp -> spa "Delivers"
        spa -> apiServer "Makes API calls to" "JSON/HTTPS"
        apiServer -> database "Reads from and writes to" "SQL/TCP"
        apiServer -> emailSystem "Sends e-mails using" "SMTP"
        supportStaff -> apiServer "Uses admin endpoints on"

        authController -> securityComponent "Uses"
        accountController -> database "Reads from and writes to"

        production = deploymentEnvironment "Production" {
            deploymentNode "AWS" {
                deploymentNode "EC2 Instance" "" "Amazon Linux" {
                    containerInstance webApp
                    containerInstance apiServer
                }
                deploymentNode "RDS" "" "Amazon RDS" {
                    containerInstance database
                }
            }
        }
    }

    views {
        systemContext bankingSystem "SystemContext" {
            include *
            autoLayout
        }

        container bankingSystem "Containers" {
            include *
            autoLayout
        }

        component apiServer "Components" {
            include *
            autoLayout
        }

        deployment bankingSystem production "Deployment" {
            include *
            autoLayout
        }

        dynamic bankingSystem "SignIn" "Sign-in flow" {
            customer -> spa "Opens banking app"
            spa -> apiServer "Submits credentials to"
            apiServer -> database "Queries user record"
            autoLayout lr
        }

        styles {
            element "Person" {
                shape Person
                background #08427b
                color #ffffff
            }
            element "Software System" {
                background #1168bd
                color #ffffff
            }
            element "Container" {
                background #438dd5
                color #ffffff
            }
            element "Component" {
                background #85bbf0
                color #000000
            }
            element "Database" {
                shape Cylinder
            }
            element "External" {
                background #999999
                color #ffffff
            }
            relationship "Relationship" {
                color #707070
                thickness 2
            }
        }
    }

}
```
