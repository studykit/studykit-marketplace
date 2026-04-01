# D2 Special Diagram Types

## Table of Contents

1. [SQL Tables (ERD)](#sql-tables-erd)
2. [Sequence Diagrams](#sequence-diagrams)
3. [UML Class Diagrams](#uml-class-diagrams)
4. [Grid Diagrams](#grid-diagrams)

---

## SQL Tables (ERD)

Use `shape: sql_table` to define database tables with columns and constraints.

### Basic Table

```d2
users: {
  shape: sql_table
  id: int {constraint: primary_key}
  username: varchar(255) {constraint: unique}
  email: varchar(255) {constraint: unique}
  created_at: timestamp
}
```

### Column Constraints

| Constraint | Abbreviation |
|-----------|--------------|
| `primary_key` | PK |
| `foreign_key` | FK |
| `unique` | UNQ |
| Custom text | Displayed as-is |

Multiple constraints:

```d2
column_name: type {constraint: [primary_key; unique]}
```

### Foreign Key Relationships

Connect specific columns between tables:

```d2
users: {
  shape: sql_table
  id: int {constraint: primary_key}
  name: varchar(255)
}

orders: {
  shape: sql_table
  id: int {constraint: primary_key}
  user_id: int {constraint: foreign_key}
  total: decimal
}

orders.user_id -> users.id
```

### Complete ERD Example

```d2
direction: right

users: {
  shape: sql_table
  id: int {constraint: primary_key}
  username: varchar(255) {constraint: unique}
  email: varchar(255)
  created_at: timestamp
}

posts: {
  shape: sql_table
  id: int {constraint: primary_key}
  user_id: int {constraint: foreign_key}
  title: varchar(255)
  body: text
  published_at: timestamp
}

comments: {
  shape: sql_table
  id: int {constraint: primary_key}
  post_id: int {constraint: foreign_key}
  user_id: int {constraint: foreign_key}
  body: text
  created_at: timestamp
}

posts.user_id -> users.id
comments.post_id -> posts.id
comments.user_id -> users.id
```

### Reserved Keywords

Wrap SQL reserved words in quotes:

```d2
table: {
  shape: sql_table
  "select": int
  "from": varchar
}
```

---

## Sequence Diagrams

Use `shape: sequence_diagram` on a container to create sequence diagrams.

### Basic Sequence Diagram

```d2
interaction: {
  shape: sequence_diagram

  alice: Alice
  bob: Bob

  alice -> bob: Hello
  bob -> alice: Hi there
  alice -> bob: How are you?
  bob -> alice: Great, thanks!
}
```

### Key Rules

- The **order of connections** determines the visual sequence (top to bottom)
- **Actors** (children of the sequence diagram) share the same scope throughout
- Actors are declared as direct children and referenced in connections

### Spans (Activation Boxes)

Show when an actor is actively processing:

```d2
api_flow: {
  shape: sequence_diagram

  client: Client
  server: Server
  db: Database

  client -> server: POST /users
  server.process: {
    server -> db: INSERT INTO users
    db -> server: OK
  }
  server -> client: 201 Created
}
```

### Groups

Organize sequences into labeled sections:

```d2
auth_flow: {
  shape: sequence_diagram

  user: User
  app: App
  auth: Auth Service

  Login: {
    user -> app: Enter credentials
    app -> auth: Validate
    auth -> app: Token
    app -> user: Welcome
  }

  Access Resource: {
    user -> app: Request data
    app -> auth: Verify token
    auth -> app: Valid
    app -> user: Data
  }
}
```

### Notes

Notes are nested objects on actors with no outgoing connections:

```d2
flow: {
  shape: sequence_diagram

  alice: Alice
  bob: Bob

  alice -> bob: Hello
  alice."alice thinks": Should I tell Bob?
  alice -> bob: I have news
}
```

### Self-Messages

```d2
flow: {
  shape: sequence_diagram

  server: Server
  server -> server: Internal processing
}
```

---

## UML Class Diagrams

Use `shape: class` to define UML classes with fields and methods.

### Basic Class

```d2
User: {
  shape: class

  # Fields
  +id: int
  +name: string
  -password: string
  #email: string

  # Methods
  +getName(): string
  +setName(name: string): void
  -hashPassword(): string
}
```

### Visibility Modifiers

| Prefix | Meaning |
|--------|---------|
| `+` | Public |
| `-` | Private |
| `#` | Protected |

### Class Relationships

```d2
User: {
  shape: class
  +id: int
  +name: string
}

Admin: {
  shape: class
  +role: string
  +permissions: list
}

User <-> Admin: inherits
```

---

## Grid Diagrams

Grid diagrams arrange elements in a structured grid layout.

### Basic Grid

```d2
grid: {
  grid-rows: 2

  cell1: A
  cell2: B
  cell3: C
  cell4: D
}
```

### Grid with Columns

```d2
grid: {
  grid-columns: 3

  item1: First
  item2: Second
  item3: Third
  item4: Fourth
  item5: Fifth
  item6: Sixth
}
```

### Both Rows and Columns

When both are set, the first-defined keyword is the dominant direction (fill order):

```d2
layout: {
  grid-rows: 2
  grid-columns: 3

  a; b; c; d; e; f
}
```

### Gap Control

```d2
grid: {
  grid-rows: 2
  grid-columns: 3
  grid-gap: 20
  # Or individually:
  # vertical-gap: 10
  # horizontal-gap: 20

  a; b; c; d; e; f
}
```

### Sized Cells

```d2
dashboard: {
  grid-rows: 2
  grid-columns: 2

  header: Header {
    width: 400
    height: 50
  }
  sidebar: Sidebar {
    width: 100
    height: 200
  }
  main: Main Content {
    width: 300
    height: 200
  }
  footer: Footer {
    width: 400
    height: 50
  }
}
```

### Zero Gap (Pixel-Art / Tight Layouts)

```d2
pixel: {
  grid-rows: 3
  grid-columns: 3
  grid-gap: 0

  a; b; c; d; e; f; g; h; i
}
```
