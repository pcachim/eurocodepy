"""Structured calculation report ("explain mode") for eurocodepy checks.

This is UI-agnostic **data**. A check function optionally records the steps it
performs — clause, symbolic expression, numeric substitution, value and unit — so
a consumer (a report generator, a web view, a Word/PDF exporter) can render a
full, auditable calculation *without re-deriving anything*. Rendering is the
consumer's job; only a plain-text / Markdown convenience renderer lives here.

Design rules:

* The check computes as it always did; the trace only **records** what was
  computed. Passing ``trace=None`` (the default) is a no-op, so existing callers
  are unaffected and the reported numbers are, by construction, the ones used.
* The schema is small and stable — treat it as an API between eurocodepy and its
  consumers, and version it (``SCHEMA_VERSION``) if it changes.

Typical use::

    from eurocodepy.calc_report import CalcReport
    rep = CalcReport(title="Member M12 — EC3 §6.3.3")
    res = eurocode3_member_check(inp, trace=rep)
    print(rep.to_markdown())        # or rep.to_dict() for a Word/HTML backend
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

SCHEMA_VERSION = 1


@dataclass
class CalcStep:
    """One line of a calculation.

    ``symbol`` is the quantity (e.g. ``"χ_y"``); ``value``/``unit`` its result.
    ``expr`` is the symbolic form and ``latex`` its LaTeX (for nice math);
    ``subst`` is the same expression with the numbers substituted. ``clause`` is
    the code reference. ``ok`` is set only when the step is a verification.
    """

    symbol: str
    value: float | str
    unit: str = ""
    clause: str = ""
    expr: str = ""
    latex: str = ""
    subst: str = ""
    note: str = ""
    ok: bool | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CalcSection:
    title: str
    steps: list = field(default_factory=list)


@dataclass
class CalcReport:
    """Collector passed into a check as ``trace=`` to record its steps.

    ``None`` (not an empty report) means "explain mode off"; the check simply
    never calls into the report.
    """

    title: str = ""
    meta: dict = field(default_factory=dict)
    sections: list = field(default_factory=list)
    schema_version: int = SCHEMA_VERSION

    # ── recording API (called by the checks) ───────────────────────────────
    def section(self, title: str) -> "CalcReport":
        self.sections.append(CalcSection(title=title))
        return self

    def step(self, symbol, value, unit="", *, clause="", expr="", latex="",
             subst="", note="", ok=None) -> None:
        if not self.sections:
            self.section("")
        self.sections[-1].steps.append(CalcStep(
            symbol=symbol, value=value, unit=unit, clause=clause, expr=expr,
            latex=latex, subst=subst, note=note, ok=ok))

    # ── convenience renderers (a consumer may ignore these) ─────────────────
    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "title": self.title,
            "meta": dict(self.meta),
            "sections": [
                {"title": s.title, "steps": [st.to_dict() for st in s.steps]}
                for s in self.sections
            ],
        }

    def to_markdown(self) -> str:
        def _fmt(v):
            return f"{v:.4g}" if isinstance(v, float) else str(v)

        out: list[str] = []
        if self.title:
            out.append(f"# {self.title}\n")
        for s in self.sections:
            if s.title:
                out.append(f"## {s.title}\n")
            for st in s.steps:
                head = f"**{st.symbol}** = {_fmt(st.value)} {st.unit}".rstrip()
                if st.clause:
                    head += f"  _[{st.clause}]_"
                out.append(head)
                if st.expr:
                    out.append(f"  - {st.expr}")
                if st.subst:
                    out.append(f"  - = {st.subst}")
                if st.ok is not None:
                    out.append(f"  - {'✓ verified' if st.ok else '✗ NOT verified'}")
                if st.note:
                    out.append(f"  - _{st.note}_")
            out.append("")
        return "\n".join(out)
