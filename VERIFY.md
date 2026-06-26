# VERIFY.md — Fresh-clone verification

## Commit 4918df8 (HEAD)

Verified 2026-06-26.

```bash
$ git clone https://github.com/necat101/python-regex-backtracking-footgun-correctness-lab.git regex-verify
Cloning into 'regex-verify'...

$ cd regex-verify
$ python3 -m py_compile generate_cases.py run_lab.py
$ python3 generate_cases.py
Wrote 52 cases to cases/cases.jsonl (20486 bytes), re_atomic_support=True, python=3.12.3

$ python3 run_lab.py
Results: results/results.jsonl (153620 bytes)
Report: RESULTS.md
  re_search_baseline: pass=41 fail=0 skip=11 timeouts=0 time=10.30ms
  re_fullmatch_baseline: pass=41 fail=0 skip=11 timeouts=0 time=0.63ms
  re_compile_error_baseline: pass=46 fail=0 skip=6 timeouts=0 time=2.00ms
  subprocess_timeout_guard: pass=46 fail=0 skip=6 timeouts=0 time=3602.34ms
  precise_negated_class_extractor: pass=10 fail=0 skip=42 timeouts=0 time=0.69ms
  non_greedy_extractor: pass=10 fail=0 skip=42 timeouts=0 time=0.99ms
  atomic_or_possessive_if_supported: pass=3 fail=0 skip=49 timeouts=0 time=0.21ms
  naive_greedy_dotstar_extractor: pass=5 fail=5 skip=42 timeouts=0 time=0.17ms
  plain_string_method_baseline: pass=6 fail=0 skip=46 timeouts=0 time=0.18ms
```

All 52 cases generated deterministically (seed 42).
- `re_search_baseline`, `re_fullmatch_baseline`: 41 pass, 0 fail, 11 skip
- `re_compile_error_baseline`: 46 pass, 0 fail, 6 skip
- `subprocess_timeout_guard`: 46 pass, 0 fail, 6 skip, 0 timeouts — catastrophic patterns completed within timeout budget (inputs intentionally tiny)
- `precise_negated_class_extractor`: 10 pass, 0 fail, 42 skip
- `non_greedy_extractor`: 10 pass, 0 fail, 42 skip
- `atomic_or_possessive_if_supported`: 3 pass, 0 fail, 49 skip — atomic groups supported=True in Python 3.12.3
- `naive_greedy_dotstar_extractor`: 5 pass, **5 fail**, 42 skip — all 5 failures expected (greedy overcapture)
- `plain_string_method_baseline`: 6 pass, 0 fail, 46 skip

Python: CPython 3.12.3 on Linux-6.17.0-1009-aws-x86_64-with-glibc2.39
re atomic/possessive support: True
