# Python Regex Backtracking Footgun Correctness Lab — Results

**Python:** 3.12.3 (CPython)

**re atomic/possessive support:** True

**Platform:** Linux-6.17.0-1009-aws-x86_64-with-glibc2.39

**Cases:** 52 (20486 bytes)

**Seed:** 42 (deterministic)

**Timing:** time.perf_counter()

**Memory:** tracemalloc — current 354.5 KiB, peak 411.6 KiB

**Total wall time:** 3.6587s

**Subprocess count:** 52

## Summary

| Method | Kind | Pass | Fail | Skip | Expected-Fail | Timeouts | Overcaptures | Time (ms) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| re_search_baseline | inline-re | 41 | 0 | 11 | 0 | 0 | 0 | 10.081 |
| re_fullmatch_baseline | inline-re | 41 | 0 | 11 | 0 | 0 | 0 | 0.628 |
| re_compile_error_baseline | compile-check | 46 | 0 | 6 | 0 | 0 | 0 | 2.240 |
| subprocess_timeout_guard | subprocess-guarded | 46 | 0 | 6 | 0 | 0 | 0 | 3622.562 |
| precise_negated_class_extractor | precise-extraction | 10 | 0 | 42 | 0 | 0 | 0 | 0.708 |
| non_greedy_extractor | non-greedy-extraction | 10 | 0 | 42 | 0 | 0 | 0 | 1.011 |
| atomic_or_possessive_if_supported | atomic-demo | 3 | 0 | 49 | 0 | 0 | 0 | 0.236 |
| naive_greedy_dotstar_extractor | naive-extraction | 5 | 5 | 42 | 5 | 0 | 5 | 0.179 |
| plain_string_method_baseline | string-method | 6 | 0 | 46 | 0 | 0 | 0 | 0.194 |

## Skip Matrix

| Method | Total | Passed | Failed | Skipped |
|---|---:|---:|---:|---:|
| re_search_baseline | 52 | 41 | 0 | 11 |
| re_fullmatch_baseline | 52 | 41 | 0 | 11 |
| re_compile_error_baseline | 52 | 46 | 0 | 6 |
| subprocess_timeout_guard | 52 | 46 | 0 | 6 |
| precise_negated_class_extractor | 52 | 10 | 0 | 42 |
| non_greedy_extractor | 52 | 10 | 0 | 42 |
| atomic_or_possessive_if_supported | 52 | 3 | 0 | 49 |
| naive_greedy_dotstar_extractor | 52 | 5 | 5 | 42 |
| plain_string_method_baseline | 52 | 6 | 0 | 46 |

## Failures / Timeouts (grouped by method)

### naive_greedy_dotstar_extractor

- **R004** [greedy_overcapture]  — greedy overcapture detected [OVERCAPTURE] (expected)
- **R006** [precise_pattern]  — greedy overcapture detected [OVERCAPTURE] (expected)
- **R008** [greedy_overcapture]  — greedy overcapture detected [OVERCAPTURE] (expected)
- **R039** [naive_negative]  — greedy overcapture detected [OVERCAPTURE] (expected)
- **R043** [precise_pattern]  — greedy overcapture detected [OVERCAPTURE] (expected)

## Notes

- `re_search_baseline` / `re_fullmatch_baseline`: stdlib `re` works correctly for safe patterns.
- `re_compile_error_baseline`: invalid regex syntax is correctly caught at compile time.
- `subprocess_timeout_guard`: catastrophic patterns run in subprocess with timeout — prevents hangs. Timeout count is recorded.
- `precise_negated_class_extractor`: patterns like `a="([^"]*)"` correctly extract quoted attributes without overcapture.
- `non_greedy_extractor`: `.*?` helps avoid overcapture but is still not a substitute for precise patterns.
- `atomic_or_possessive_if_supported`: atomic groups `(?>...)` / possessive quantifiers `++`/` *+`/`?+` — supported=True in this Python. When supported, they fail fast on catastrophic inputs.
- `naive_greedy_dotstar_extractor`: greedy `.*` overcaptures — expected failures demonstrate the footgun.
- `plain_string_method_baseline`: `str.find`/`split`/`startswith`/`endswith`/`in` work for simple cases, skip regex-only cases.
- No external regex engines (RE2, PCRE, ripgrep, hyperscan, etc.) were used — out of scope.
- This lab is NOT a production ReDoS detector.

## Conclusion

Regex is powerful but easy to overuse. Greedy `.*` often captures more than humans expect. Nested quantifiers can cause catastrophic backtracking on failing inputs. A timeout or process boundary is useful for untrusted patterns. CPython's GIL matters for long-running C-level regex work but is not the whole problem. Atomic groups and possessive quantifiers help where supported but are not a complete strategy. Precise patterns (`[^"]*`) or simple string methods are often safer for simple extraction. Use a real parser with timeouts — never rely on naive greedy regex for untrusted input.
