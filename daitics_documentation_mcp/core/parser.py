"""
Markdown → list[Section].

A *section* is one H2-heading block in a markdown file plus everything under
it up to the next H2 (or end of file). This is the unit of retrieval (plan §4).

The parser:
  1. Reads YAML frontmatter from the top of each file (required).
  2. Finds the H1 (the file title — used in breadcrumb).
  3. Splits the body by H2 lines, extracting the pinned slug from
     `## heading {#kebab-slug}` (plan §10d).
  4. Pulls per-section aliases from `<!-- aliases: x, y, z -->` HTML comments.
  5. Computes a content_hash so the indexer can skip unchanged sections on
     reload (plan §5).
  6. Special-cases glossary.md: each H2 is a glossary term, and the parser
     returns a parallel list of GlossaryEntry records.

Strict by design — missing frontmatter or missing `{#slug}` annotations on
H2 headings are deployment misconfigurations, not runtime conditions to
recover from. We fail loudly with the file/line context so the writer can
fix the source. (Plan §13 Phase 2 — "no frontmatter → fail loudly".)
"""
from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

log = logging.getLogger(__name__)

# Allowed values for the `category` frontmatter field. Mirrors plan §3 + §10a.
VALID_CATEGORIES = {
    "getting-started",
    "features",
    "how-to",
    "troubleshooting",
    "glossary",
    "overview",
}

# Required frontmatter keys per plan §10a. We don't validate the *content* of
# `tags` / `aliases` beyond shape — empty lists are allowed (a writer might
# legitimately not yet have synonyms for a section).
_REQUIRED_FRONTMATTER = {
    "id", "title", "category", "summary", "tags", "aliases",
    "last_updated", "version",
}

# `## heading text {#stable-slug}` — slug is required (plan §10d).
_H2_LINE = re.compile(r"^##\s+(?P<title>.+?)\s*\{#(?P<slug>[a-z0-9][a-z0-9\-]*)\}\s*$")

# `# heading text` (optional `{#...}` ignored — H1 is for display, not retrieval).
_H1_LINE = re.compile(r"^#\s+(?P<title>.+?)(?:\s*\{#[^}]+\})?\s*$")

# `<!-- aliases: foo, bar baz, qux -->` — optional, attached to a section.
_ALIASES_COMMENT = re.compile(
    r"<!--\s*aliases:\s*(?P<list>[^>]+?)\s*-->", re.IGNORECASE,
)

# Human-readable category name used in breadcrumbs.
_CATEGORY_LABEL = {
    "getting-started": "Getting Started",
    "features": "Features",
    "how-to": "How-To",
    "troubleshooting": "Troubleshooting",
    "glossary": "Glossary",
    "overview": "Overview",
}


@dataclass
class Section:
    section_id: str         # "<category>/<basename>#<slug>" or "<category>#<slug>"
    title: str              # H2 heading text
    category: str
    file_basename: str
    file_title: str         # H1 of the file (used in breadcrumb)
    file_summary: str       # frontmatter.summary (used by docs_browse)
    breadcrumb: str         # e.g. "How-To › Reset password › Default flow"
    content: str            # markdown body of the section, including the H2 line
    tags: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)   # file aliases ∪ section aliases
    last_updated: str = ""
    version: int = 1
    content_hash: str = ""

    def embedding_input(self) -> str:
        """
        Text that goes into the embedding (plan §4 table). Title + breadcrumb
        + aliases + body — explicit > implicit, since the body might not
        repeat every keyword that should match.
        """
        parts = [self.title, self.breadcrumb]
        if self.aliases:
            parts.append("Aliases: " + ", ".join(self.aliases))
        parts.append(self.content)
        return "\n\n".join(parts)


@dataclass
class GlossaryEntry:
    term: str               # H2 heading text in glossary.md (canonical form)
    definition: str         # markdown body of the entry, with HTML aliases comment stripped
    aliases: list[str]      # synonyms from the `<!-- aliases: ... -->` comment
    section_id: str         # e.g. "glossary#audience" — same id as the underlying Section


# ── Public entry point ────────────────────────────────────────────────────────

def parse_file(path: Path, docs_root: Path) -> tuple[list[Section], list[GlossaryEntry]]:
    """
    Parse one markdown file into Sections (always) and GlossaryEntries (only
    for glossary.md). Returns (sections, glossary_entries). Empty lists are
    valid (e.g. a file with frontmatter but no H2s — though that should be
    rare in this corpus).
    """
    text = path.read_text(encoding="utf-8")
    fm, body = _split_frontmatter(text, path)

    category = fm["category"]
    if category not in VALID_CATEGORIES:
        raise ParseError(
            f"{path}: category {category!r} is not in {sorted(VALID_CATEGORIES)}"
        )

    file_basename = path.stem  # filename without .md
    file_title = _extract_h1(body, path)
    file_aliases = list(fm.get("aliases") or [])
    file_tags = list(fm.get("tags") or [])
    last_updated = str(fm.get("last_updated", ""))
    version = int(fm.get("version", 1))
    file_summary = str(fm.get("summary", ""))

    sections: list[Section] = []
    glossary_entries: list[GlossaryEntry] = []

    for h2 in _split_by_h2(body, path):
        # Per-section aliases (HTML comment) merge with file-level aliases.
        # Order matters only for the embedding's alias list (deterministic);
        # de-duplicated on the way out.
        section_aliases = _extract_aliases(h2.content)
        merged_aliases = _dedupe(file_aliases + section_aliases)

        section_id = _build_section_id(category, file_basename, h2.slug)
        breadcrumb = _build_breadcrumb(category, file_title, h2.title)

        # Canonical content for hashing: stripped+normalised body. Whitespace
        # tweaks shouldn't trigger re-embedding.
        canonical = _canonicalise(h2.content)
        content_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

        sections.append(Section(
            section_id=section_id,
            title=h2.title,
            category=category,
            file_basename=file_basename,
            file_title=file_title,
            file_summary=file_summary,
            breadcrumb=breadcrumb,
            content=h2.content,
            tags=list(file_tags),
            aliases=merged_aliases,
            last_updated=last_updated,
            version=version,
            content_hash=content_hash,
        ))

        if category == "glossary":
            # Definition body, with the aliases comment stripped so the LLM
            # doesn't see HTML noise when docs_glossary returns the entry.
            definition_body = _strip_aliases_comment(h2.content)
            # Strip the leading H2 line itself — the LLM already sees `term`
            # in the structured response, no need to repeat it.
            definition_body = _strip_h2_line(definition_body).strip()
            glossary_entries.append(GlossaryEntry(
                term=h2.title,
                definition=definition_body,
                aliases=section_aliases,   # file-level aliases don't apply to a single term
                section_id=section_id,
            ))

    return sections, glossary_entries


# ── Errors ────────────────────────────────────────────────────────────────────

class ParseError(ValueError):
    """Raised on malformed markdown — a deployment-time error, not runtime."""


# ── Frontmatter ───────────────────────────────────────────────────────────────

def _split_frontmatter(text: str, path: Path) -> tuple[dict, str]:
    """
    Returns (frontmatter_dict, body). Fails loudly if frontmatter is missing
    or doesn't carry every required key. Per plan §13 Phase 2.
    """
    if not text.startswith("---"):
        raise ParseError(f"{path}: missing YAML frontmatter (no leading ---)")

    # The second `---` marker terminates the block.
    end = text.find("\n---", 3)
    if end == -1:
        raise ParseError(f"{path}: unterminated YAML frontmatter (no closing ---)")

    raw_yaml = text[3:end].lstrip("\n")
    body_start = end + len("\n---")
    # Skip the newline after the closing ---, if present.
    if body_start < len(text) and text[body_start] == "\n":
        body_start += 1
    body = text[body_start:]

    try:
        fm = yaml.safe_load(raw_yaml) or {}
    except yaml.YAMLError as e:
        raise ParseError(f"{path}: invalid YAML frontmatter: {e}") from e
    if not isinstance(fm, dict):
        raise ParseError(f"{path}: frontmatter must be a YAML mapping, got {type(fm).__name__}")

    missing = _REQUIRED_FRONTMATTER - set(fm.keys())
    if missing:
        raise ParseError(
            f"{path}: frontmatter missing required keys: {sorted(missing)}"
        )
    return fm, body


# ── H1 / H2 extraction ────────────────────────────────────────────────────────

def _extract_h1(body: str, path: Path) -> str:
    """Return the text of the first H1 line. Required — front-page title."""
    for line in body.splitlines():
        m = _H1_LINE.match(line)
        if m:
            return m.group("title").strip()
    raise ParseError(f"{path}: no H1 heading found in body")


@dataclass
class _H2Block:
    title: str
    slug: str
    content: str   # full markdown of the section, starting with the H2 line


def _split_by_h2(body: str, path: Path) -> list[_H2Block]:
    """
    Walk lines; whenever we see an H2 line, start a new block. Lines before
    the first H2 (intro paragraphs under the H1) are dropped — the agent
    retrieves at the section level, and intro text belongs to the file as
    a whole, not to any one section.
    """
    blocks: list[_H2Block] = []
    current: _H2Block | None = None
    buf: list[str] = []

    def flush() -> None:
        if current is not None:
            current.content = "\n".join(buf).rstrip() + "\n"
            blocks.append(current)

    for lineno, line in enumerate(body.splitlines(), start=1):
        if line.startswith("## "):
            m = _H2_LINE.match(line)
            if not m:
                # Heading with no `{#slug}` — fail loudly per plan §10d.
                raise ParseError(
                    f"{path}:{lineno}: H2 heading is missing required "
                    f"`{{#kebab-slug}}` annotation: {line.rstrip()!r}"
                )
            flush()
            current = _H2Block(title=m.group("title").strip(), slug=m.group("slug"), content="")
            buf = [line]
            continue
        if current is not None:
            buf.append(line)
    flush()
    return blocks


# ── Aliases / canonicalisation helpers ────────────────────────────────────────

def _extract_aliases(section_content: str) -> list[str]:
    """Pull alias terms from a `<!-- aliases: x, y, z -->` comment if present."""
    m = _ALIASES_COMMENT.search(section_content)
    if not m:
        return []
    raw = m.group("list")
    return [a.strip() for a in raw.split(",") if a.strip()]


def _strip_aliases_comment(text: str) -> str:
    return _ALIASES_COMMENT.sub("", text)


def _strip_h2_line(text: str) -> str:
    """Remove the first non-empty line if it's an H2 heading."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip():
            if line.startswith("## "):
                return "\n".join(lines[i + 1:])
            break
    return text


def _canonicalise(text: str) -> str:
    """
    Normalise whitespace before hashing. Trailing spaces and blank-line
    differences shouldn't churn the index; semantic edits should.
    """
    lines = [line.rstrip() for line in text.splitlines()]
    # Collapse runs of blank lines to a single one.
    out: list[str] = []
    prev_blank = False
    for line in lines:
        is_blank = line == ""
        if is_blank and prev_blank:
            continue
        out.append(line)
        prev_blank = is_blank
    return "\n".join(out).strip() + "\n"


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


# ── ID + breadcrumb construction ──────────────────────────────────────────────

def _build_section_id(category: str, file_basename: str, slug: str) -> str:
    # Top-level "category file" (e.g. glossary.md, troubleshooting.md): the
    # filename equals the category, so collapse to "<category>#<slug>" rather
    # than the redundant "<category>/<category>#<slug>". Plan §4 examples.
    if file_basename == category:
        return f"{category}#{slug}"
    return f"{category}/{file_basename}#{slug}"


def _build_breadcrumb(category: str, file_title: str, section_title: str) -> str:
    """
    "<Category Label> › <File Title> › <Section Title>", e.g.
    "How-To › How to reset your password › Default flow".

    For files where the file title and the section title overlap heavily,
    we still include both — the LLM benefits from seeing the parent context
    explicitly.
    """
    label = _CATEGORY_LABEL.get(category, category)
    return f"{label} › {file_title} › {section_title}"


# ── Walk-the-tree convenience ────────────────────────────────────────────────

def parse_corpus(docs_root: Path) -> tuple[list[Section], list[GlossaryEntry]]:
    """
    Parse every *.md file under `docs_root`. Used by the indexer at startup
    and on /api/admin/reload.
    """
    if not docs_root.exists():
        raise ParseError(f"DOCS_PATH {docs_root!r} does not exist")
    if not docs_root.is_dir():
        raise ParseError(f"DOCS_PATH {docs_root!r} is not a directory")

    md_files = sorted(docs_root.rglob("*.md"))
    if not md_files:
        # Plan §5: "If the docs directory is missing or empty, fail fast —
        # that is a deployment misconfiguration, not a runtime condition."
        raise ParseError(f"DOCS_PATH {docs_root!r} contains no markdown files")

    all_sections: list[Section] = []
    all_glossary: list[GlossaryEntry] = []
    for path in md_files:
        sections, glossary = parse_file(path, docs_root)
        all_sections.extend(sections)
        all_glossary.extend(glossary)

    # Sanity check: section_ids must be unique across the whole corpus,
    # otherwise docs_get is ambiguous. Catch this at parse time, not in
    # Qdrant where the duplicate would silently overwrite the first one.
    seen: dict[str, Section] = {}
    for sec in all_sections:
        if sec.section_id in seen:
            raise ParseError(
                f"duplicate section_id {sec.section_id!r}: "
                f"appears in {seen[sec.section_id].file_basename!r} and "
                f"{sec.file_basename!r}. "
                f"Pin a unique `{{#kebab-slug}}` on at least one of them."
            )
        seen[sec.section_id] = sec

    return all_sections, all_glossary
