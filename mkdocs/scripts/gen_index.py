"""Generate the home page of the documentation from the README of the repository.

The README is the single source: this takes it, drops what only makes sense on GitHub (the part between
``<!-- docs:skip-start -->`` and ``<!-- docs:skip-end -->``), turns the links to files of the repository into
links to GitHub and adds the navigation of the site.
"""

import re
from pathlib import Path

REPO = "https://github.com/pcachim/eurocodepy/blob/master"
SKIP = re.compile(r"<!-- docs:skip-start -->.*?<!-- docs:skip-end -->\n?", re.S)
LOCAL_LINK = re.compile(r"\]\((?!https?://|#|mailto:)([^)\s]+)\)")

NAVIGATION = """## Navigation

- [Tutorials](tutorials.md) — step-by-step worked examples
- [How-to guides](how-to-guides.md) — recipes for common tasks
- [Modules](modules/ec2/index.md) — one page per Eurocode ([EC1](modules/ec1.md), [EC2](modules/ec2/index.md),
  [EC3](modules/ec3.md), [EC5](modules/ec5.md), [EC7](modules/ec7.md), [EC8](modules/ec8.md), [utils](modules/utils.md)),
  and [editions and National Annexes](modules/editions.md)
- [Code reference](reference/) — generated API documentation
- [Background](explanation.md) — design decisions and architecture
- [License & contributing](copyright.md)

---

"""


def build_index(readme: str) -> str:
    """Return the markdown of the home page built from the text of the README."""
    text = SKIP.sub("", readme)
    text = LOCAL_LINK.sub(lambda m: f"]({REPO}/{m.group(1)})", text)
    marker = "## Contributing"
    if marker not in text:
        msg = f"the README has no '{marker}' section to put the navigation before"
        raise ValueError(msg)
    return text.replace(marker, NAVIGATION + marker, 1)


if __name__ == "__main__":
    print(build_index((Path(__file__).parents[2] / "README.md").read_text(encoding="utf-8")))
else:
    import mkdocs_gen_files

    readme = (Path(__file__).parents[2] / "README.md").read_text(encoding="utf-8")
    with mkdocs_gen_files.open("index.md", "w") as fd:
        fd.write(build_index(readme))
