# Source Attribution on UCs

Each UC body produced by `extract-usecase` includes a `## Source` section identifying where the UC came from. The section is mandatory for every UC in `extract-usecase` output.

## Allowed values

- `input` — from the user's idea / brainstorm directly.
- `research — <systems>` — from similar-systems research (list the products that surfaced this UC).
- `code — <path>` — from code analysis of an existing implementation (cite the path).
- `implicit` — surfaced during reviewer / explorer completeness analysis.

## Why it's mandatory

Autonomous generation makes interpretation choices the user did not explicitly authorize. The `## Source` section makes those choices auditable: a reviewer can trace any UC back to the input that justified it. Implicit-source UCs in particular flag UCs that no upstream artifact directly named — these are the highest-value items to confirm with the user.

## Interaction with `## Source` and `kind: question`

When the composer chooses a specific interpretation autonomously (per the autonomous decision rules), the choice is recorded in `## Source`. When the composer cannot resolve an ambiguity even with a default rule, it emits a separate `kind: question` review item. The two are distinct: `## Source` records *what was decided*; `kind: question` records *what is still undecided*.
