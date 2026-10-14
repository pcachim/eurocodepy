"""Generate the EN 1992-1-1:2023 clause map (clause or equation -> function) from the docstrings."""

import importlib
import inspect
import re

MODULES = [
    ("shear", "Shear, clause 8.2"),
    ("torsion", "Torsion, clause 8.3"),
    ("shear_torsion", "Shear and torsion"),
    ("annex_g", "Annex G, membranes, slabs and shells"),
    ("detailing", "Detailing, clause 12"),
]
NUM = r"\(?[A-G]?\d+\.\d+\)?(?![\d(]|\.\d)"
EQ = re.compile(rf"Eqs?\.\s*{NUM}(?:\s*(?:-|–|/|,|and)\s*{NUM})*")
TABLE = re.compile(r"(?:Tables?|Figure)\s+[A-G]?\d+(?:\.\d+)?(?:\s+(?:row|rows)\s+\d+(?:-\d+)?)?")
CLAUSE = re.compile(r"\b\d{1,2}\.\d+(?:\.\d+)*(?:\(\d+\))?(?:[a-z]\))?|\bG\.\d+(?:\(\d+\))?")


def references(text: str) -> str:
    """Return the equations, tables and clauses quoted in ``text``."""
    found = [m.group(0) for m in EQ.finditer(text)]
    rest = EQ.sub(" ", text)
    found += [m.group(0) for m in TABLE.finditer(rest)]
    rest = TABLE.sub(" ", rest)
    found += [m.group(0) for m in CLAUSE.finditer(rest)]
    return "; ".join(dict.fromkeys(found))


def build() -> str:
    """Return the markdown of the clause map."""
    out = ["# EN 1992-1-1:2023 clause map\n",
           "Generated from the docstrings of `eurocodepy.ec2.uls2023`: the clause or equation is the one "
           "quoted in the first line of each docstring, and each function links to the code reference.\n"]
    for name, title in MODULES:
        mod = importlib.import_module(f"eurocodepy.ec2.uls2023.{name}")
        rows = []
        for fname, func in inspect.getmembers(mod, inspect.isfunction):
            if func.__module__ != mod.__name__ or fname.startswith("_"):
                continue
            first = (inspect.getdoc(func) or "").split("\n")[0].replace("|", "\\|")
            rows.append((references(first), fname, first.rstrip(".")))
        out.append(f"\n## {title}\n\n| Clause / equation | Function | Returns |\n|---|---|---|")
        # the function links to its entry in the code reference (mkdocs-autorefs)
        out += [f"| {ref} | [`uls2023.{name}.{fname}`][eurocodepy.ec2.uls2023.{name}.{fname}] | {desc} |"
                for ref, fname, desc in rows]
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    print(build())
else:
    import mkdocs_gen_files

    with mkdocs_gen_files.open("modules/ec2/clauses.md", "w") as fd:
        fd.write(build())
