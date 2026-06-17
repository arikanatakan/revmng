# Contributing

Thanks for your interest in revmng.

## Development setup

```
git clone https://github.com/arikanatakan/revmng
cd revmng
python -m pip install -e ".[dev]"
```

## Before opening a pull request

```
ruff check .
mypy revmng
pytest
```

All three must pass. New methods should come with a validation case in
`tests/validation_cases.json`: the inputs and the expected result, taken from a
published worked example (cite the source) or derived by hand and documented in
the case.

## Scope

revmng computes revenue-management decisions from the demand you supply. It does
not forecast demand, estimate willingness-to-pay, or connect to a reservation or
property-management system; those belong upstream. New methods are welcome when
they are computed from a standard formulation and validated.

## Conventions

- Keep the result contract append-only: add fields, do not rename or remove.
- Compute from the textbook methods and cite the source; EMSR-a and EMSR-b are
  heuristics and should be documented as such.
