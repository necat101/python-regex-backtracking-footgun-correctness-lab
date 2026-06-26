# Python Regex Backtracking Footgun Correctness Lab

A tiny, reproducible Python-only lab testing the Hacker News debate around Python regex / catastrophic backtracking.

**HN thread:** https://news.ycombinator.com/item?id=33582664
**Linked article:** https://www.benfrederickson.com/python-catastrophic-regular-expressions-and-the-gil/

## What HN was debating

- Regex is powerful but easy to overuse.
- Greedy `.*` often captures more than humans expect.
- Nested quantifiers can cause catastrophic backtracking on failing inputs.
- A timeout or process boundary is useful for untrusted patterns or inputs.
- CPython's GIL matters for long-running C-level regex work but is not the whole problem.
- The underlying backtracking behavior still matters even outside Python.
- Atomic groups and possessive quantifiers can help in supported Python versions but are not a complete design strategy.
- Precise patterns or simple string methods are often better for simple extraction tasks.
- Third-party engines like RE2 are out of scope here.
- This lab is NOT a production ReDoS detector.

The linked article walks through CVE-2022-36027 (Python quadratic / exponential backtracking DoS), the GIL preventing other threads from running during catastrophic regex, and practical mitigations (timeouts, better patterns, third-party engines).

## What this lab does

Tests 52 deterministic regex edge cases across 9 stdlib-only methods:

| Method | Description |
|---|---|
| `re_search_baseline` | `re.search` — stdlib baseline, safe inline cases only |
| `re_fullmatch_baseline` | `re.fullmatch` — full-string matching |
| `re_compile_error_baseline` | verifies invalid regex syntax is caught at compile time |
| `subprocess_timeout_guard` | runs risky patterns in subprocess with timeout — prevents hangs |
| `precise_negated_class_extractor` | `a="([^"]*)"` style — precise extraction, no overcapture |
| `non_greedy_extractor` | `.*?` — non-greedy, better than greedy but still vague |
| `atomic_or_possessive_if_supported` | atomic groups `(?>...)` / possessive `++` — skip if unsupported |
| `naive_greedy_dotstar_extractor` | intentionally unsafe greedy `.*` — expected to overcapture |
| `plain_string_method_baseline` | `str.find`/`split`/`startswith`/`endswith`/`in` — skip regex-only cases |

**Categories covered:** normal, greedy_overcapture, precise_pattern, catastrophic_risk, timeout_guard, atomic_or_possessive, unsupported_syntax, backreference, lookaround, flags_caveat, unicode_caveat, invalid_regex, string_method, naive_negative

**Safety:** Catastrophic patterns run in subprocess with short timeout (0.5–1.0s). Input lengths are tiny and bounded. No unbounded catastrophic patterns run in the main process.

No compilers, no package managers, no Docker, no external corpora, no network calls during the benchmark. Python stdlib only.

## Running

```bash
python3 -m py_compile generate_cases.py run_lab.py
python3 generate_cases.py
python3 run_lab.py
```

Output:
- `cases/cases.jsonl` — 52 deterministic cases (seed 42)
- `results/results.jsonl` — per-method results
- `RESULTS.md` — summary table, skip matrix, failure list, conclusions

## Results (CPython 3.12.3)

| Method | Pass | Fail | Skip |
|---|---|---:|---:|
| re_search_baseline | 41 | 0 | 11 |
| re_fullmatch_baseline | 41 | 0 | 11 |
| re_compile_error_baseline | 46 | 0 | 6 |
| subprocess_timeout_guard | 46 | 0 | 6 |
| precise_negated_class_extractor | 10 | 0 | 42 |
| non_greedy_extractor | 10 | 0 | 42 |
| atomic_or_possessive_if_supported | 3 | 0 | 49 |
| naive_greedy_dotstar_extractor | 5 | 5 | 42 |
| plain_string_method_baseline | 6 | 0 | 46 |

All 5 naive failures are **expected** — greedy overcapture detected.

**Note on catastrophic patterns:** The intentionally risky nested-quantifier cases (`(a+)+b`, `(a|a)*b`, etc.) with short failing inputs (12–15 repetitions) completed within the subprocess timeout in CPython 3.12.3 — no actual timeouts occurred. Longer inputs would trigger exponential backtracking, but are intentionally excluded to keep the lab fast and safe. The point is demonstrated: the pattern is risky, subprocess guarding prevents hangs.

**Atomic/possessive support:** `re` atomic groups `(?>...)` and possessive quantifiers (`++`, `*+`, `?+`) ARE supported in the test Python (3.12.3) — 3 atomic test cases all pass.

See [RESULTS.md](RESULTS.md) for full details.

## Key findings

- `re.search` / `re.fullmatch` work correctly for safe patterns.
- Invalid regex syntax is caught at compile time — `re.error` raised, not crash.
- Subprocess timeout guarding prevents catastrophic backtracking from hanging the main process.
- Precise negated character classes (`a="([^"]*)"`) correctly extract quoted attributes without overcapture.
- Non-greedy `.*?` helps avoid overcapture but is still less precise than negated classes.
- Atomic groups `(?>...)` / possessive quantifiers (`++`) fail fast on catastrophic inputs — when supported (Python 3.11+).
- Naive greedy `.*` overcaptures reliably — `a="(.*)"` on `a="foo" b="bar"` captures `foo" b="bar` instead of `foo`.
- Plain string methods (`find`/`split`/`startswith`) work for simple cases; skip regex-only cases.
- No external regex engines (RE2, PCRE, ripgrep, hyperscan, etc.) were used — out of scope.
- This lab is NOT a production ReDoS detector.

## Scope

This lab is intentionally tiny. It does **not** claim regex is bad, and does **not** compare Python against RE2, Rust, Tcl, Perl, PCRE, ripgrep, or any external engine. It tests the HN debate in a reproducible way: greedy wildcards capture too much, nested quantifiers can be extremely slow on failing inputs, the stdlib `re` engine is a backtracking engine, timeouts/process isolation matter for untrusted patterns, atomic groups help where supported, and simple string operations or more precise patterns are sometimes safer.

No external regex libraries (regex, re2, pyre2, hyperscan), no system grep/perl, no online regex testers, no exploit corpora or CVE lists were used.

## Verify

See [VERIFY.md](VERIFY.md) for a fresh-clone verification transcript.
