> Source: https://plantuml.com/er-diagram

# PlantUML Entity-Relationship Diagram Reference

PlantUML supports two ER diagram notations:

1. **Information Engineering (IE) notation** — uses `@startuml`/`@enduml`, based on class diagram engine, best for database schemas
2. **Chen notation** — uses `@startchen`/`@endchen`, classic academic ER style with diamond relationships

---

## Information Engineering (IE) Notation

### Basic Structure

```plantuml
@startuml
entity EntityName {
}
@enduml
```

### Entity Declaration with Attributes

Use `*` to mark mandatory attributes. Separate the primary key section from other attributes with `--`.

```plantuml
@startuml
entity "User" as e01 {
  * user_id : number <<generated>>
  --
  * name : text
  description : text
}
@enduml
```

### Attribute Markers

| Marker | Meaning |
|--------|---------|
| `*` | Mandatory attribute |
| `<<generated>>` | Auto-generated value |
| `<<FK>>` | Foreign key |

Bold formatting is supported in attributes. Add a space after `*` before bold to avoid conflicts with creole markup:

```plantuml
@startuml
entity Entity01 {
  optional attribute
  **optional bold attribute**
  * **mandatory bold attribute**
}
@enduml
```

### Relationship Cardinality Symbols

Cardinality is expressed with symbols on each end of the relationship line:

| Symbol | Meaning |
|--------|---------|
| `\|\|` | Exactly one |
| `\|o` | Zero or one |
| `}o` | Zero or many |
| `}\|` | One or many |

The reverse direction mirrors the symbols:

| Symbol | Meaning |
|--------|---------|
| `\|\|` | Exactly one |
| `o\|` | Zero or one |
| `o{` | Zero or many |
| `\|{` | One or many |

### Relationship Line Styles

| Syntax | Style |
|--------|-------|
| `--` | Solid line |
| `..` | Dashed line |

### Relationship Examples

```plantuml
@startuml
Entity01 }|..|| Entity02
Entity03 }o..o| Entity04
Entity05 ||--o{ Entity06
Entity07 |o--|| Entity08
@enduml
```

Reading the above:
- `Entity01 }|..|| Entity02` — Entity01 is one-or-many to exactly-one Entity02 (dashed)
- `Entity03 }o..o| Entity04` — Entity03 is zero-or-many to zero-or-one Entity04 (dashed)
- `Entity05 ||--o{ Entity06` — Entity05 is exactly-one to zero-or-many Entity06 (solid)
- `Entity07 |o--|| Entity08` — Entity07 is zero-or-one to exactly-one Entity08 (solid)

### Entity Aliases

Use `"Display Name" as alias` to give entities readable names:

```plantuml
@startuml
entity "User Account" as user {
  * user_id : number <<generated>>
  --
  * username : varchar
  email : varchar
}

entity "Order" as order {
  * order_id : number <<generated>>
  --
  * user_id : number <<FK>>
  order_date : date
}

user ||--o{ order
@enduml
```

### Orthogonal Line Routing

Use `skinparam linetype ortho` to draw right-angle lines instead of diagonal ones. This avoids rendering issues with angled crow's feet:

```plantuml
@startuml
skinparam linetype ortho

entity "User" as e01 {
  * user_id : number <<generated>>
  --
  * name : text
  description : text
}

entity "Card" as e02 {
  * card_id : number <<generated>>
  --
  * user_id : number <<FK>>
  other_details : text
}

e01 }|..|| e02
@enduml
```

### Hiding the Circle/Spot

By default, entities display a colored circle. Hide it with:

```plantuml
@startuml
hide circle

entity "Customer" {
  * customer_id : number
  --
  * name : text
}
@enduml
```

### Complete IE Example

```plantuml
@startuml
hide circle
skinparam linetype ortho

entity "User" as e01 {
  * user_id : number <<generated>>
  --
  * name : text
  description : text
}

entity "Card" as e02 {
  * card_id : number <<generated>>
  sync_enabled : boolean
  version : number
  last_sync_version : number
  --
  * user_id : number <<FK>>
  other_details : text
}

entity "CardHistory" as e05 {
  * card_history_id : number <<generated>>
  version : number
  --
  * card_id : number <<FK>>
  other_details : text
}

entity "CardsAccounts" as e04 {
  * id : number <<generated>>
  --
  card_id : number <<FK>>
  account_id : number <<FK>>
  other_details : text
}

entity "Account" as e03 {
  * account_id : number <<generated>>
  --
  user_id : number <<FK>>
  other_details : text
}

entity "Stream" as e06 {
  * id : number <<generated>>
  version : number
  searchingText : string
  --
  owner_id : number <<FK>>
  follower_id : number <<FK>>
  card_id : number <<FK>>
  other_details : text
}

e01 }|..|| e02
e01 }|..|| e03

e02 }|..|| e05

e02 }|..|| e04
e03 }|..|| e04

e02 }|..|| e06
e03 }|..|| e06
@enduml
```

---

## Chen Notation

### Basic Structure

```plantuml
@startchen
entity ENTITY_NAME {
}
@endchen
```

### Entity with Attributes

```plantuml
@startchen
entity DIRECTOR {
  Number : INTEGER <<key>>
  Name : STRING
  Bonus : REAL <<derived>>
  Skills : STRING <<multi>>
  Age : INTEGER
}
@endchen
```

### Attribute Markers

| Marker | Meaning |
|--------|---------|
| `<<key>>` | Primary key (unique identifier) |
| `<<derived>>` | Computed/derived attribute |
| `<<multi>>` | Multi-valued attribute |

### Composite Attributes

Nest attributes using braces:

```plantuml
@startchen
entity DIRECTOR {
  Name {
    Fname
    Lname
  }
  Born
  Age
}
@endchen
```

### Relationship Declaration

Relationships are first-class elements (diamonds) that can have their own attributes:

```plantuml
@startchen
entity CUSTOMER {
  Number : INTEGER <<key>>
  Name : STRING
}

entity MOVIE {
  Code : INTEGER <<key>>
  Title : STRING
}

relationship RENTED_TO {
  Date
}

RENTED_TO -1- CUSTOMER
RENTED_TO -N- MOVIE
@endchen
```

### Cardinality Notation

**Simple cardinality:**

| Syntax | Meaning |
|--------|---------|
| `-1-` | Optional one (partial participation) |
| `-N-` | Optional many |
| `=1=` | Mandatory one (total participation, thick line) |
| `=N=` | Mandatory many |

**Range cardinality:**

| Syntax | Meaning |
|--------|---------|
| `-(0,1)-` | Zero or one |
| `-(1,1)-` | Exactly one |
| `-(0,N)-` | Zero or many |
| `-(1,N)-` | One or many |
| `-(N,M)-` | Many-to-many range |

```plantuml
@startchen
entity CUSTOMER {
  Number <<key>>
}

entity MOVIE {
  Code <<key>>
}

relationship RENTED_TO {
  Date
}

RENTED_TO -(1,N)- CUSTOMER
RENTED_TO -(0,1)- MOVIE
@endchen
```

### Weak Entities and Identifying Relationships

Mark entities as `<<weak>>` and relationships as `<<identifying>>`:

```plantuml
@startchen
entity PARENT {
  Number <<key>>
  Name
}

entity CHILD <<weak>> {
  Name <<key>>
  Age
}

relationship PARENT_OF <<identifying>> {
}

PARENT_OF -1- PARENT
PARENT_OF =N= CHILD
@endchen
```

### Generalization / Specialization

Use `->-` for subclass-to-superclass generalization:

```plantuml
@startchen
entity CUSTOMER {
  Number <<key>>
}

entity PARENT {
  ChildCount
}

entity MEMBER {
  MemberID
}

PARENT ->- CUSTOMER
MEMBER ->- CUSTOMER
@endchen
```

### Specialization Groups

**Disjoint specialization** (entity belongs to at most one subclass):

```plantuml
@startchen
entity CUSTOMER {
  Number <<key>>
}

entity PARENT {
}

entity MEMBER {
}

CUSTOMER ->- o { PARENT, MEMBER }
@endchen
```

**Overlapping specialization** (entity can belong to multiple subclasses):

```plantuml
@startchen
entity CHILD {
  Name <<key>>
}

entity TODDLER {
}

entity PRIMARY_AGE {
}

entity TEENAGER {
}

CHILD =>= d { TODDLER, PRIMARY_AGE, TEENAGER }
@endchen
```

**Union type / Category:**

```plantuml
@startchen
entity PERSON {
  ID <<key>>
}

entity CUSTOMER {
}

entity EMPLOYEE {
}

PERSON ->- U { CUSTOMER, EMPLOYEE }
@endchen
```

| Symbol | Meaning |
|--------|---------|
| `o` | Disjoint constraint |
| `d` | Disjoint constraint (alternative) |
| `U` | Union type / category |

### Aliases for Readable Names

```plantuml
@startchen
entity "Customer" as CUSTOMER {
  "customer number" as Number <<key>>
  "member bonus" as Bonus <<derived>>
  "first and last names" as Name <<multi>>
}

relationship "was-rented-to" as RENTED_TO {
  "date rented" as Date
}

RENTED_TO -1- CUSTOMER
@endchen
```

### Layout Direction

Control diagram direction with:

```plantuml
@startchen
left to right direction
entity A {
}
entity B {
}
relationship R {
}
R -1- A
R -N- B
@endchen
```

Options: `top to bottom direction` (default), `left to right direction`

### Styling with CSS-like Syntax

Apply colors and fonts using `<style>` blocks:

```plantuml
@startchen
<style>
.red {
  BackGroundColor Red
  FontColor White
}
.blue {
  BackGroundColor Blue
  FontColor White
}
</style>

entity "Director" as DIRECTOR {
  Died <<red>>
  Age <<blue>>
  Name
}
@endchen
```
