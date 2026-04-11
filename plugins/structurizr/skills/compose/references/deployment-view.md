> Source: https://docs.structurizr.com/dsl/cookbook/deployment-view/

# Deployment View Reference

Shows how software system containers are deployed onto infrastructure.

## View Syntax

```
deployment <*|software system identifier> <environment name> [key] [description] {
    include *
    autoLayout [tb|bt|lr|rl]
}
```

Use `*` to show all software systems, or scope to one system.

## Model Elements

### deploymentEnvironment

```
deploymentEnvironment <name> {
    deploymentNode ... { ... }
}
```

### deploymentNode

```
deploymentNode <name> [description] [technology] [tags] [instances] {
    [deploymentNode]           // nested nodes
    [infrastructureNode]       // load balancers, firewalls, etc.
    [softwareSystemInstance]   // deployed system
    [containerInstance]        // deployed container
}
```

Instances: `"1"`, `"4"`, `"1..N"`, `"0..1"`

### infrastructureNode

```
infrastructureNode <name> [description] [technology] [tags]
```

### containerInstance / softwareSystemInstance

```
containerInstance <container identifier> [deploymentGroups] [tags]
softwareSystemInstance <system identifier> [deploymentGroups] [tags]
```

## Example

```
workspace {

    model {
        user = person "User"
        system = softwareSystem "Web Platform" {
            webApp = container "Web Application" "Serves frontend" "Nginx"
            apiServer = container "API Server" "REST API" "Node.js"
            database = container "Database" "Primary data store" "PostgreSQL"
            cache = container "Cache" "Session and query cache" "Redis"
        }

        user -> webApp "Uses" "HTTPS"
        webApp -> apiServer "Forwards requests to"
        apiServer -> database "Reads/writes" "SQL/TCP"
        apiServer -> cache "Reads/writes" "TCP"

        production = deploymentEnvironment "Production" {
            deploymentNode "AWS" "" "Amazon Web Services" {
                deploymentNode "ALB" "" "Application Load Balancer" {
                    infrastructureNode "Load Balancer" "" "AWS ALB"
                }
                deploymentNode "ECS Cluster" "" "Amazon ECS" {
                    deploymentNode "Web Task" "" "Docker" "1..N" {
                        containerInstance webApp
                    }
                    deploymentNode "API Task" "" "Docker" "1..N" {
                        containerInstance apiServer
                    }
                }
                deploymentNode "RDS" "" "Amazon RDS" {
                    containerInstance database
                }
                deploymentNode "ElastiCache" "" "Amazon ElastiCache" {
                    containerInstance cache
                }
            }
        }
    }

    views {
        deployment system production "ProductionDeployment" {
            include *
            autoLayout
        }

        styles {
            element "Infrastructure Node" {
                shape RoundedBox
            }
        }
    }

}
```
