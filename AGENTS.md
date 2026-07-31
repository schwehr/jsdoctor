# AGENTS.md: AI Assistant & Developer Guidelines for jsdoctor

This document provides guidelines, conventions, and architectural context for AI
assistants and developers contributing to `jsdoctor`.

## 1. Project Overview & Architecture

`jsdoctor` is a Python tool and library designed to extract Closure-style JSDoc
comments from JavaScript codebases and generate formatted HTML API reference
documentation.

The core architecture follows a pipeline:

1. **Scanning & Symbol Extraction**: Scans JavaScript source files for
   `goog.provide` and `goog.require` declarations, extracts JSDoc comment blocks
   (`/** ... */`), and locates the associated JavaScript identifier targets
   using regular expression scanning.
1. **Comment & Flag Parsing**: Parses JSDoc comments into structured `Comment`
   objects with description text and parsed JSDoc tags/flags (such as `@param`,
   `@return`, `@constructor`, `@interface`, `@enum`, etc.).
1. **Symbol Classification & Namespace Mapping**: Classifies extracted symbols
   into symbol types (`constructor`, `interface`, `enum`, `function`,
   `property`) and groups symbols by their Closure namespace.
1. **HTML Documentation Generation**: Renders HTML documentation pages for each
   namespace using `xml.dom.minidom` and `html5lib`, linking web URLs and
   cross-symbol references.
1. **Archiving**: Bundles generated HTML documentation into tar archives via the
   CLI.

## 2. Repository & File Layout

- `jsdoctor/`: Core package containing CLI, scanning, modeling, parsing, and
  rendering modules:
  - `cli.py`: Main CLI script for parallel source file scanning, symbol map
    construction, and tar archive output generation.
  - `__main__.py`: CLI entrypoint module allowing `python -m jsdoctor`
    execution.
  - `scanner.py`: Regex scanners for `goog.provide`, `goog.require`, JSDoc
    comments, and target identifier resolution.
  - `source.py`: Data structures (`Source`, `Symbol`, `Comment`, `Flag`) and
    top-level `ScanScript` orchestration.
  - `jsdoc.py`: Sectioning and flag extraction logic for JSDoc comment blocks.
  - `flags.py`: Sets and definitions for supported JSDoc flags (`@param`,
    `@return`, etc.).
  - `symboltypes.py`: Classification logic for determining symbol categories.
  - `namespace.py`: Helper functions for splitting, comparing, and manipulating
    namespaces.
  - `linkify.py`: Utility functions for auto-linking URLs and symbol references
    in text.
  - `generator.py`: DOM-based HTML document generator for namespace
    documentation.
  - `esprima.py`: Prototype AST-based parsing integration using Esprima.
- `genjsonfiletree.py` / `processjsontree.py` / `node/`: Experimental AST/JSON
  file tree processing utilities and Node.js helpers.
- `tests/`: Comprehensive `pytest` test suite (`jsdoc_test.py`,
  `scanner_test.py`, `source_test.py`, `namespace_test.py`, `flags_test.py`,
  `linkify_test.py`, `symboltypes_test.py`).
- `.github/workflows/ci.yml` / `.github/dependabot.yml`: GitHub Actions CI
  pipeline and Dependabot automated dependency update configuration.
- `pyproject.toml` / `uv.lock`: Project metadata, dependencies (`html5lib`), and
  configuration for `uv`, `pytest`, `pylint`, `ty`, `pyrefly`, and `codespell`.

## 3. Structure & API Summary

- **`jsdoctor.source`**:
  - `ScanScript(script: str, path: str | None = None) -> Source`: Parses script
    text and returns a populated `Source` object.
  - `Source`: Holds `script`, `path`, `provides`, `requires`, `symbols`, and
    `filecomment`.
  - `Symbol`: Represents a documented identifier with `identifier`, `namespace`,
    `comment`, and `source`.
  - `Comment`: Contains `text`, `descriptions`, and `flags`.
  - `Flag`: Simple `(name, text)` container for JSDoc tags.
- **`jsdoctor.scanner`**:
  - `ExtractDocumentedSymbols(script)`: Yields pairs of comment match and
    identifier target match.
  - `YieldProvides(source)` / `YieldRequires(source)`: Yields provided/required
    namespace strings.
  - `FindJsDocComments(script)` / `FindCommentTarget(script, pos)`: Regex search
    helpers.
- **`jsdoctor.jsdoc`**:
  - `ProcessComment(comment_text: str) -> tuple[list[str], list[tuple[str, str]]]`:
    Extracts descriptions and raw flag tuples from JSDoc comments.
- **`jsdoctor.symboltypes`**:
  - `DetermineSymbolType(symbol: Symbol) -> str`: Identifies symbol type
    (`CONSTRUCTOR`, `INTERFACE`, `ENUM`, `FUNCTION`, `PROPERTY`).
- **`jsdoctor.namespace`**:
  - `GetNamespaceParts(namespace: str) -> list[str]`: Splits dot-separated
    namespace strings.
  - `IsPrototypeProperty(namespace: str) -> bool`: Checks if a namespace
    represents a prototype property.
  - `IsSymbolPartOfNamespace(symbol: str, namespace: str) -> bool`: Determines
    namespace membership.
- **`jsdoctor.generator`**:
  - `GenerateHtmlDocs(namespace_map: Mapping[str, Iterable[Symbol]]) -> Iterator[tuple[str, bytes]]`:
    Generates `(filename, html_bytes)` pairs for all namespaces.
- **`jsdoctor.linkify`**:
  - `LinkifyWebUrls(content: str) -> str`: Replaces `http(s)://` URLs with HTML
    anchor tags.

## 4. Development Environment & Tooling

Use modern Python tooling for dependency management, building, linting, and
static analysis:

- **Dependency Management (`uv`)**: Use `uv` for all virtual environments and
  package installations.
  ```bash
  uv sync
  ```
- **Linting & Formatting (`ruff`, `pylint`)**: Enforces code style, import
  sorting, formatting, and code quality checks.
  ```bash
  uv run ruff check --fix
  uv run ruff format
  uv run pylint *.py jsdoctor tests
  ```
- **Static Type Checking (`ty`, `mypy`, `pyrefly`, & `pyright`)**: Enforces
  strict type annotations across all modules.
  ```bash
  uv run ty check
  uv run mypy .
  uv run pyrefly check
  uv run pyright
  ```
- **Markdown Formatting (`mdformat`)**: Enforces 80-column line wrapping and
  standard GFM formatting across Markdown files.
  ```bash
  uv run mdformat --wrap 80 .
  ```
- **Spelling (`codespell`)**: Checks for typos and misspelled identifiers.
  ```bash
  uv run codespell
  ```
- **Static Analysis & Security Scanning (`semgrep`, `bandit`)**: Enforces static
  analysis and security rules.
  ```bash
  uv run bandit -c pyproject.toml -r .
  uv run semgrep scan --config p/default
  ```
- **Pre-commit Hooks**: Enforces standards prior to commits. Must be installed
  when setting up a workspace:
  ```bash
  uv run pre-commit install --hook-type pre-commit --hook-type commit-msg
  uv run pre-commit run --all-files
  ```

## 5. Testing Conventions & Standards

All testing is orchestrated via `pytest`, `pytest-cov`, and `pytest-benchmark`.

- **Running Tests**:
  ```bash
  uv run pytest
  ```
- **Continuous Fuzz Testing (`hypofuzz`)**: To continuously run adaptive,
  coverage-guided property-based fuzzing on our hypothesis test suite
  (`tests/test_properties.py`):
  ```bash
  uv run hypothesis fuzz tests/test_properties.py
  ```
- **Cross-Platform CI**: Automated matrix testing in GitHub Actions executes
  across Linux (`ubuntu-latest`), macOS (`macos-latest`), and Windows
  (`windows-latest`) for Python 3.14, while Python 3.13 testing is scoped to
  Linux. Benchmarks and type checks are also scoped to Linux.
- **Best Pytest Form**:
  - **CRITICAL RULE**: Write all new and refactored tests in the **best modern
    `pytest` form** using standard Python `assert` statements (e.g.,
    `assert bv.size == 8`).
  - **Do NOT use legacy `unittest` style** assertions (`self.assertEqual`,
    `self.assertTrue`, `self.assertRaises`, etc.) or inherit from
    `unittest.TestCase`.
  - Use `pytest.raises(...)` for expected exceptions.
  - Use `@pytest.mark.parametrize` to cleanly test multiple input combinations
    without repetitive boilerplate.
  - Use standard pytest fixtures (like `tmp_path` for temporary files) instead
    of manual cleanup or `tempfile`.
- **Coverage & Performance**: Maintain 100% test coverage for new features and
  bug fixes (enforced with a 95% minimum threshold via `--fail-under=95`).
  Ensure benchmark suites (`test_benchmarks.py`) remain functional and
  non-regressing. Continuous integration automatically formats and outputs
  read-only Markdown coverage reports to GitHub Actions job summaries.

## 6. Code & Docstring Style

- **Docstrings**:
  - **CRITICAL RULE**: All module, class, method, and function docstrings must
    strictly follow **Standard Google Python Docstring Style**.
  - Include clearly formatted `Args:`, `Returns:`, `Raises:`, `Yields:`, and
    `Attributes:` sections as applicable.
  - Avoid unstructured, verbose, or legacy docstring formatting.
- **String Formatting**:
  - Always use modern Python **f-strings** (`f"Value: {val}"`) for string
    concatenation and formatting. Never use legacy `%` formatting or
    `.format()`.
- **Type Annotations**:
  - Provide precise, tight type annotations for all function signatures and
    return types.
  - Avoid generic `Any` types; prefer specific types such as `Sequence[int]`,
    `Buffer`, `Self`, or `Literal`.
  - Avoid `Union`/`Optional`.

## 7. Version Control & Commit Messages

- **Feature Branches**:
  - **CRITICAL RULE**: All code changes and refactoring work MUST be performed
    on dedicated git feature branches (e.g., `git checkout -b <branch-name>`).
  - Never make direct commits on the `main` branch.
- **Code Review**:
  - Always do a code review before committing. In addition to finding and
    suggesting fixes to issues, try to create 1-3 suggestions for improvement to
    the code based on the current changes.
  - See if there needs to be any changes to `AGENTS.md` based on the current
    changes and propose improvements.
- **Conventional Commits**:
  - All git commit messages MUST adhere to the **Conventional Commits**
    specification (`<type>(<optional scope>): <subject>`).
  - Examples:
    - `feat(dunder): enable modern __add__ and __iadd__ support`
    - `refactor(tests): switch test_init.py from unittest to pytest`
    - `chore(license): replace __copyright__ variable with SPDX header`
    - `docs: import legacy manuals into docs/ directory`
- **NO Tag or Conversation ID Entries**:
  - **CRITICAL RULE**: Commit messages must **NEVER** contain `TAG=` or `CONV=`
    lines or entries. These are reserved for internal Piper/CL tools and must be
    omitted from all git commits in this repository.
