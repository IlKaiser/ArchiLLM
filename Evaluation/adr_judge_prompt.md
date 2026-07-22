# ADR Pattern-Fidelity Judge

You are scoring how faithfully a generated Architecture Decision Record
(ADR) captures the information in its source architectural-pattern
description.

## Source Pattern Description
{{INSERT_PATTERN_HERE}}

## Generated ADR
{{INSERT_ADR_HERE}}

## Task
Score the ADR from 1 to 5 on how completely and accurately it reflects the
context, problem, forces, solution, and consequences described in the
source pattern description:

- **5** — Every material piece of pattern information (context, problem,
  forces, solution, consequences/trade-offs) is present and accurately
  represented in the ADR.
- **3** — Most pattern information is present, but some forces,
  consequences, or trade-offs are missing or only partially represented.
- **1** — The ADR omits most of the pattern's information or misrepresents
  the solution/consequences.

## Output Format
Respond with ONLY a JSON object in a fenced code block:

```json
{
  "score": <integer 1-5>,
  "reasoning": "<2-3 sentence justification>",
  "missing_elements": ["<pattern detail the ADR omitted>", "..."]
}
```
