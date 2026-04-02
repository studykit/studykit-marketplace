---
name: deployment-diagram
disable-model-invocation: true
description: This skill provides PlantUML deployment diagram syntax reference. Use when writing, creating, or debugging PlantUML deployment diagrams. Applies when users mention "deployment diagram", "node", "artifact", "device", "server", "infrastructure", or need to diagram system deployment, infrastructure topology, or hardware architecture in PlantUML.
---

> Source: https://plantuml.com/deployment-diagram

# PlantUML Deployment Diagram Reference

## Declaring Elements

PlantUML deployment diagrams support a wide range of element keywords. Each keyword creates a distinct visual shape.

```plantuml
@startuml
actor actor
agent agent
artifact artifact
boundary boundary
card card
circle circle
cloud cloud
collections collections
component component
control control
database database
entity entity
file file
folder folder
frame frame
hexagon hexagon
interface interface
label label
node node
package package
person person
process process
queue queue
rectangle rectangle
stack stack
storage storage
usecase usecase
@enduml
```

## Short Form Syntax

Several elements have abbreviated notation:

```plantuml
@startuml
:actor:
[component]
() "interface"
(usecase)
@enduml
```

## Aliases

Use the `as` keyword to assign aliases to elements with long names.

```plantuml
@startuml
node "Application Server" as appServer
file "config.yml" as cfg
cloud "AWS Cloud" as aws

appServer --> cfg
appServer --> aws
@enduml
```

## Long Descriptions with Brackets

Elements support multi-line descriptions using square brackets. You can use separators (`--`, `==`, `..`, `__`) inside descriptions.

```plantuml
@startuml
folder myFolder [
  This is a <b>folder</b>
  ----
  You can use separator
  ====
  of different kind
  ....
  dotted separator
  ____
  underlined separator
]

node myNode [
  <b>Production Server</b>
  ----
  Ubuntu 22.04
  ====
  16 GB RAM
  8 vCPU
]
@enduml
```

## Linking and Arrows

### Basic Line Styles

Connect elements with different line styles:

```plantuml
@startuml
node node1
node node2
node node3
node node4
node node5

node1 -- node2 : "-- plain"
node1 .. node3 : ".. dashed"
node1 ~~ node4 : "~~ dotted"
node1 == node5 : "== bold"
@enduml
```

### Arrow Head Types

```plantuml
@startuml
artifact f1
artifact f2
artifact f3
artifact f4
artifact f5
artifact f6
artifact f8
artifact f9
artifact f10
artifact f11
artifact f12
artifact f13

artifact b1
artifact b2
artifact b3
artifact b4
artifact b5
artifact b6
artifact b8
artifact b9
artifact b10
artifact b11
artifact b12
artifact b13

f1 --> b1 : "-->"
f2 -->> b2 : "-->>"
f3 --* b3 : "--*"
f4 --o b4 : "--o"
f5 --+ b5 : "--+"
f6 --# b6 : "--#"
f8 --^ b8 : "--^"
f9 --|> b9 : "--|>"
f10 --||> b10 : "--||>"
f11 --:|> b11 : "--:|>"
f12 --@ b12 : "--@"
f13 --0 b13 : "--0"
@enduml
```

`--\` 형태는 parser-sensitive 해서 복붙 시 `Syntax Error?`를 유발할 수 있으므로 예제에서 제외했습니다.

### Circle Arrows

```plantuml
@startuml
cloud f1
cloud f2
cloud f3
cloud f4
cloud f5
cloud f6
cloud f7
cloud f8
cloud f9
cloud f10

cloud b1
cloud b2
cloud b3
cloud b4
cloud b5
cloud b6
cloud b7
cloud b8
cloud b9
cloud b10

f1 --0 b1 : "--0"
f2 --( b2 : "--("
f3 --(0 b3 : "--(0"
f4 -(0- b4 : "-(0-"
f5 -(0)- b5 : "-(0)-"
f6 -0)- b6 : "-0)-"
f7 0)-- b7 : "0)--"
f8 0)--(0 b8 : "0)--(0"
f9 )--( b9 : ")--("
f10 0--0 b10 : "0--0"
@enduml
```

### Arrow Length

Use more dashes to increase arrow length:

```plantuml
@startuml
node n1
node n2
node n3

n1 -> n2 : short
n1 --> n3 : longer
@enduml
```

### Arrow Direction

Use `-left->`, `-right->`, `-up->`, `-down->` (or shorthand `-l->`, `-r->`, `-u->`, `-d->`) to control direction.

```plantuml
@startuml
node center
node left
node right
node up
node down

center -left-> left
center -right-> right
center -up-> up
center -down-> down
@enduml
```

## Bracketed Arrow Styling

### Line Styles

```plantuml
@startuml
node foo
node bar1
node bar2
node bar3
node bar4
node bar5

foo -[bold]-> bar1 : bold
foo -[dashed]-> bar2 : dashed
foo -[dotted]-> bar3 : dotted
foo -[hidden]-> bar4 : hidden
foo -[plain]-> bar5 : plain
@enduml
```

### Line Colors

```plantuml
@startuml
node foo
node bar1
node bar2
node bar3
node bar4

foo -[#red]-> bar1 : red
foo -[#green]-> bar2 : green
foo -[#blue]-> bar3 : blue
foo -[#blue;#yellow;#green]-> bar4 : gradient
@enduml
```

### Line Thickness

```plantuml
@startuml
node foo
node bar1
node bar2
node bar3
node bar4

foo -[thickness=1]-> bar1 : 1
foo -[thickness=2]-> bar2 : 2
foo -[thickness=4]-> bar3 : 4
foo -[thickness=8]-> bar4 : 8
@enduml
```

### Mixed Styling

```plantuml
@startuml
node foo
node bar1
node bar2
node bar3

foo -[#red,thickness=1]-> bar1 : red thin
foo -[#red,dashed,thickness=2]-> bar2 : red dashed
foo -[#green,dashed,thickness=4]-> bar3 : green dashed thick
@enduml
```

## Inline Arrow Color and Style

```plantuml
@startuml
node foo
node bar1
node bar2
node bar3

foo --> bar1 #line:red;line.bold;text:red : red bold
foo --> bar2 #green;line.dashed;text:green : green dashed
foo --> bar3 #blue;line.dotted;text:blue : blue dotted
@enduml
```

## Inline Element Styling

Change colors and styles directly on individual elements:

```plantuml
@startuml
agent a
cloud c #pink;line:red;line.bold;text:red
file f #palegreen;line:green;line.dashed;text:green
node n #aliceblue;line:blue;line.dotted;text:blue
database d #lightyellow;line:orange;text:orange
@enduml
```

## Nesting Elements

Many elements can contain other elements using curly braces. This is useful for modeling deployment topology.

### Nestable Elements

The following elements support nesting: `artifact`, `card`, `cloud`, `component`, `database`, `file`, `folder`, `frame`, `hexagon`, `node`, `package`, `process`, `queue`, `rectangle`, `stack`, `storage`.

```plantuml
@startuml
cloud "AWS" {
  node "EC2 Instance" {
    artifact "webapp.war"
    database "H2 (embedded)"
  }
  database "RDS" {
    folder "schemas" {
      file "users.sql"
      file "orders.sql"
    }
  }
  storage "S3" {
    file "static-assets"
  }
}
@enduml
```

### Multi-Level Nesting

```plantuml
@startuml
cloud "Production VPC" {
  frame "Public Subnet" {
    node "Load Balancer" as lb
  }
  frame "Private Subnet" {
    node "App Server 1" as app1 {
      artifact "api.jar"
    }
    node "App Server 2" as app2 {
      artifact "api.jar" as api2
    }
  }
  frame "Data Subnet" {
    database "Primary DB" as db1
    database "Replica DB" as db2
  }
}

lb --> app1
lb --> app2
app1 --> db1
app2 --> db1
db1 --> db2 : replication
@enduml
```

## Ports

Ports define named connection points on nodes. Three keywords are available: `port` (bidirectional), `portin` (input), and `portout` (output).

### Basic Port Usage

```plantuml
@startuml
node node {
  port p1
  portin p2
  portout p3
  file f1
}

actor user
database db
user --> p1
user --> p2
p3 --> db
@enduml
```

### Input Ports

```plantuml
@startuml
node "Web Server" {
  portin http
  portin https
  file "nginx.conf"
}

actor client
client --> http : "port 80"
client --> https : "port 443"
@enduml
```

### Output Ports

```plantuml
@startuml
node "Application" {
  portout api
  portout events
  file "app.jar"
}

database "Database" as db
queue "Message Queue" as mq

api --> db
events --> mq
@enduml
```

### Mixed Ports

```plantuml
@startuml
node "API Gateway" {
  portin request
  portout upstream
  file "routes.conf"
}

actor client
node "Backend"

client --> request
upstream --> Backend
@enduml
```

## Diagram Direction

### Top to Bottom (Default)

```plantuml
@startuml
top to bottom direction
node "Web Server" as web
node "App Server" as app
database "Database" as db

web --> app
app --> db
@enduml
```

### Left to Right

```plantuml
@startuml
left to right direction
actor user
node "Web Server" as web
node "App Server" as app
database "Database" as db

user --> web
web --> app
app --> db
@enduml
```

## Stereotypes

Add stereotypes with `<< >>` after the element name:

```plantuml
@startuml
node "web01" << Linux >>
node "web02" << Linux >>
node "db01" << Windows >>
database "MySQL" << Primary >>
database "MySQL" << Replica >> as replica

"web01" --> "MySQL"
"web02" --> "MySQL"
"MySQL" --> replica : replication
@enduml
```

## Round Corners

### Per-Stereotype Round Corners

```plantuml
@startuml
skinparam rectangle {
  roundCorner<<Concept>> 25
}

rectangle "Concept Model" <<Concept>> {
  rectangle "Example 1" <<Concept>> as ex1
  rectangle "Example 2" <<Concept>> as ex2
}
@enduml
```

### Global Round Corners

```plantuml
@startuml
skinparam roundCorner 15

actor actor
component component
database database
node node
rectangle rect
@enduml
```

## Notes

```plantuml
@startuml
node "App Server" as app
database "DB" as db

app --> db

note right of app : Runs on port 8080

note left of db
  PostgreSQL 15
  with read replicas
end note

note "Secure connection\nover TLS" as n1
app .. n1
n1 .. db
@enduml
```

## Styling with `<style>` Block

### Global Style

```plantuml
@startuml
<style>
componentDiagram {
  BackGroundColor palegreen
  LineThickness 1
  LineColor red
}
</style>

node "Server"
database "DB"
"Server" --> "DB"
@enduml
```

### Element-Specific Styles

```plantuml
@startuml
<style>
node {
  BackGroundColor #lightblue
  LineColor #336699
  LineThickness 2
  FontColor #333333
}
database {
  BackGroundColor #ffe0b2
  LineColor #e65100
  LineThickness 2
}
artifact {
  BackGroundColor #e8f5e9
  LineColor #2e7d32
}
</style>

node "Web Server" {
  artifact "webapp.war"
}
database "PostgreSQL"

"Web Server" --> "PostgreSQL"
@enduml
```

### Stereotype-Based Styles

```plantuml
@startuml
<style>
.production {
  BackgroundColor #ffebee
  LineColor red
}
.staging {
  BackgroundColor #e3f2fd
  LineColor blue
}
</style>

node "prod-web01" << production >>
node "stg-web01" << staging >>
database "prod-db" << production >>
database "stg-db" << staging >>

"prod-web01" --> "prod-db"
"stg-web01" --> "stg-db"
@enduml
```

## Skinparam Customization

Use `skinparam` to globally configure colors, fonts, and rendering.

```plantuml
@startuml
skinparam node {
  BackgroundColor LightYellow
  BorderColor DarkSlateGray
  FontName Courier
  FontSize 14
}

skinparam database {
  BackgroundColor LightBlue
  BorderColor Navy
}

skinparam artifact {
  BackgroundColor PaleGreen
  BorderColor DarkGreen
}

skinparam ArrowColor DarkSlateGray
skinparam ArrowThickness 2

node "App Server" {
  artifact "myapp.jar"
}
database "MySQL"

"App Server" --> "MySQL"
@enduml
```

### Handwritten Style

```plantuml
@startuml
skinparam handwritten true

node "Server"
database "Database"
"Server" --> "Database"
@enduml
```

## Title, Header, Footer, Legend

```plantuml
@startuml
title Production Deployment Architecture
header Deployment Diagram
footer Page %page% of %lastpage%

legend right
  Production environment
  deployed on AWS
endlegend

cloud "AWS" {
  node "EC2" as ec2
  database "RDS" as rds
}

ec2 --> rds
@enduml
```

## Mixing with Other Diagram Types

Use the `allowmixing` directive to combine deployment elements with other diagram types (class, object, JSON, etc.).

```plantuml
@startuml
allowmixing

component Component
actor Actor
usecase Usecase

json JSON {
  "fruit": "Apple",
  "size": "Large",
  "color": ["Red", "Green"]
}
@enduml
```

## Display JSON Data

```plantuml
@startuml
allowmixing

node "Config Server" as cfg
artifact "app-config" as ac

json "Application Config" {
  "server": {
    "port": 8080,
    "host": "0.0.0.0"
  },
  "database": {
    "url": "jdbc:postgresql://db:5432/mydb",
    "pool_size": 10
  }
}

cfg --> ac
@enduml
```

## Splitting Diagrams Across Pages

Use `newpage` to split a deployment diagram into multiple pages.

```plantuml
@startuml
node "Web Tier" as web
node "App Tier" as app
web --> app

newpage

node "App Tier" as app2
database "Data Tier" as db
app2 --> db
@enduml
```

## Comprehensive Example

A full deployment diagram combining multiple features:

```plantuml
@startuml
left to right direction
title Microservices Deployment Architecture

skinparam node {
  BackgroundColor #f5f5f5
  BorderColor #666666
}
skinparam database {
  BackgroundColor #e3f2fd
  BorderColor #1565c0
}

cloud "Internet" as internet

node "DMZ" {
  node "Nginx" as lb {
    artifact "nginx.conf"
  }
}

frame "Kubernetes Cluster" {
  node "Pod: API Gateway" as gw {
    artifact "gateway.jar"
    portin http
    portout upstream
  }
  node "Pod: User Service" as userSvc {
    artifact "user-svc.jar"
  }
  node "Pod: Order Service" as orderSvc {
    artifact "order-svc.jar"
  }
  queue "Kafka" as mq
}

frame "Data Layer" {
  database "PostgreSQL" as pg << Primary >>
  database "PostgreSQL" as pgr << Replica >>
  database "Redis" as redis
}

internet --> lb
lb --> http
upstream --> userSvc
upstream --> orderSvc

userSvc --> pg
orderSvc --> pg
pg --> pgr : replication
userSvc --> redis : cache
orderSvc --> mq : events
mq --> userSvc : consume
@enduml
```

## Validation

After writing a `.puml` file or a PlantUML fenced block in Markdown, always validate the syntax:

- **Local** (preferred): `bash ${CLAUDE_PLUGIN_ROOT}/scripts/validate.sh <file.puml>`
- **Online** (fallback): `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/validate_online.py <file.puml>`

For PlantUML blocks embedded in Markdown, extract the content to a temporary `.puml` file before validating. If validation fails, read the error output, fix the syntax, and re-validate.
