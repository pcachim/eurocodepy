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
        import re

        def _fmt(v):
            return f"{v:.4g}" if isinstance(v, float) else str(v)

        # Steps use a plain "M_Ed" / "f_yk" convention (underscore = subscript)
        # rather than real LaTeX grouping. Outside a math environment a lone
        # "_" is just a literal underscore to a Markdown renderer, not a
        # subscript, so texify it ("M_Ed" -> "M_{Ed}") and wrap in inline math.
        _sub_re = re.compile(r'([A-Za-zΑ-Ωα-ω][A-Za-z0-9]*)_([A-Za-z0-9,]+)')

        def _texify_one(m):
            prefix, sub = m.group(1), m.group(2)
            # "My_Ed" -> "M_{y,Ed}", not "My_{Ed}": a 2-letter prefix that is
            # BASE + one lower-case axis/component letter belongs inside the
            # subscript group too. A longer spelled-out name like "chi_y"
            # (prefix "chi") is a single symbol, left as plain "chi_{y}".
            if len(prefix) == 2 and prefix[0].isupper() and prefix[1].islower():
                return f'{prefix[0]}_{{{prefix[1]},{sub}}}'
            return f'{prefix}_{{{sub}}}'

        def _mathify(s):
            if not s:
                return s
            texified = _sub_re.sub(_texify_one, s)
            return f"${texified}$"

        def _mathify_bold(s):
            # Bold via LaTeX's own \mathbf{}, not Markdown's **…** — a "**"
            # glued directly onto a "$" delimiter trips up several
            # Markdown+LaTeX pipelines (pandoc, MathJax); \mathbf sidesteps
            # the interaction entirely.
            if not s:
                return s
            texified = _sub_re.sub(_texify_one, s)
            return "$\\mathbf{" + texified + "}$"

        out: list[str] = []
        if self.title:
            out.append(f"# {self.title}\n")
        for s in self.sections:
            if s.title:
                out.append(f"## {s.title}\n")
            for st in s.steps:
                head = f"{_mathify_bold(st.symbol)} = {_fmt(st.value)} {st.unit}".rstrip()
                if st.clause:
                    head += f"  _[{st.clause}]_"
                out.append(head)
                if st.latex:
                    out.append(f"$$ {st.latex} $$")
                elif st.expr:
                    out.append(f"  - {_mathify(st.expr)}")
                if st.subst:
                    out.append(f"  - = {_mathify(st.subst)}")
                if st.ok is not None:
                    out.append(f"  - {'✓ verified' if st.ok else '✗ NOT verified'}")
                if st.note:
                    out.append(f"  - _{st.note}_")
            out.append("")
        return "\n".join(out)
