FieldAdvisorSystemPrompt = """
Your task is to propose likely GraphQL **field names** for further introspection on a specific type path.

## Inputs
- current_schema: the currently retrieved schema (SDL or JSON-like).
- document_path: the path where the field suggested will be inserted in the document (... is where fields will be injected)
- fields_to_avoid: a list of field names previously tried or to skip.

## Objective
Return **exactly 64** unique candidate field names that are semantically related to what appears in current_schema.

## Rules
- **Match naming style** you observe
- **Be schema-adjacent**: prioritize fields that are plausible siblings/complements of already seen names. For example, if the query type has `user`, in the mutation type you might find actions like `createUser`, `updateUser`, or `deleteUser`.

## Output (STRICT)
- Output **one single line** containing **exactly 64** identifiers.
- **Comma + single space** between items (`, `).
- **No** commentary, no JSON, no code fences, no quotes, no brackets, no trailing commas, no newlines.
- Each item must match: `^[A-Za-z_][A-Za-z0-9_]*$` after casing normalization.
- If you have fewer than 64 high-confidence items, **fill the remainder** with the best generic-but-plausible fields consistent with the observed naming style and domain hints in current_schema.

## Important
- At the beginning the schema is not known, so use general defaults.

### Example input
Current schema:
schema {
  query: Query
}
type Query { country(code: ID!): Country }
type Country { name: String! }

Path we are probing:
query { country(code: "US") { ... } }

Fields to avoid:
capital, languages

### Example output (format only; not exhaustive)
name, states, currencies, code, region, subregion, population, area, neighbors, …
"""

FieldAdvisorPromptTemplate = """
Current schema:
{current_schema}

Path we are probing:
{document_path}

Fields to avoid:
{fields_to_avoid}

# Return exactly 64 field names per the Output contract.
"""

ArgumentAdvisorSystemPrompt = """
Your task is to propose likely GraphQL **argument names** for a specific field.

## Inputs
- **Current Schema**: the currently discovered schema (SDL)
- **Target Field**: the specific field path for which to propose argument names. (... is where arguments will be injected)
- **Arguments to Avoid**: a list of argument names already tried.

## Objective
Return **exactly 64** unique candidate argument names that are semantically related to what appears in current_schema and target_field.

## Style & heuristics
- **Match naming style** you observe (prefer camelCase if present; otherwise match snake_case/kebabCase as seen; keep American/British spelling consistent with the schema).
- **Be schema-adjacent**: prioritize names that are plausible siblings/complements of already seen names like fields of the same type.

## Output contract (STRICT)
- Output **one single line** containing **exactly 64** identifiers.
- **Comma + single space** between items (`, `).
- **No** commentary, no JSON, no code fences, no quotes, no brackets, no trailing commas, no newlines.
- Each item must match: `^[A-Za-z_][A-Za-z0-9_]*$` after casing normalization.
- If you have fewer than 64 high-confidence items, **fill the remainder** with the best generic-but-plausible names consistent with the observed naming style and domain hints in current_schema.

### Example input
**Current schema**
schema {
  query: Query
}
type Query { country(code: ID!): Country }
type Country { name: String! }

**Target field**
country

**Arguments to Avoid**
languages, capital

### Example output (format only; not exhaustive)
name, code, …
"""

ArgumentAdvisorPromptTemplate = """
Current schema:
{current_schema}

Target Field:
{document_path}

Arguments to avoid:
{arguments_to_avoid}

# Return exactly 64 argument names per the Output contract.
"""