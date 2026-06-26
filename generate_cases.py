#!/usr/bin/env python3
"""
generate_cases.py — deterministic Python regex backtracking footgun corpus.

Uses Python stdlib (re, subprocess, json, pathlib) as source of truth.
Seed: 42

SAFETY: Catastrophic patterns are marked must_run_in_subprocess=True with tiny inputs.
They are NEVER run inline in generate_cases.py — only compile-tested.
"""
import json
import re
import sys
from pathlib import Path

SEED = 42
OUT_DIR = Path("cases")
OUT_FILE = OUT_DIR / "cases.jsonl"

# Detect atomic/possessive support
def check_atomic_support():
    tests = [
        (r"(?>a+)b", "ab"),  # atomic group
        (r"a++b", "ab"),      # possessive
    ]
    supported = []
    for pat, test_str in tests:
        try:
            re.compile(pat)
            re.search(pat, test_str)
            supported.append(pat)
        except re.error:
            pass
    return len(supported) > 0, supported

ATOMIC_SUPPORTED, ATOMIC_PATTERNS = check_atomic_support()

RAW_CASES = [
    # id, category, pattern, input_str, flags, safe_inline, timeout_s, notes, expected
    # expected: dict with match:True/False, groups:list|None, span:tuple|None, error:bool, timeout_expected:bool
    
    # normal
    ("R001", "normal", r"hello", "hello world", 0, True, 0.5, "literal substring",
     {"match": True}),
    ("R002", "normal", r"^start", "start middle end", 0, True, 0.5, "anchored start",
     {"match": True}),
    ("R003", "normal", r"end$", "start middle end", 0, True, 0.5, "anchored end",
     {"match": True}),
    
    # greedy overcapture
    ("R004", "greedy_overcapture", r'a="(.*)"', 'a="foo" b="bar"', 0, True, 0.5, "greedy dot-star overcaptures",
     {"match": True, "groups": ["foo\" b=\"bar"], "overcapture": True}),
    ("R005", "greedy_overcapture", r'<.*>', '<b>hi</b>', 0, True, 0.5, "greedy tag match",
     {"match": True, "groups": [], "overcapture": True}),
    
    # precise pattern
    ("R006", "precise_pattern", r'a="([^"]*)"', 'a="foo" b="bar"', 0, True, 0.5, "negated char class precise",
     {"match": True, "groups": ["foo"]}),
    ("R007", "precise_pattern", r'<[^>]*>', '<b>hi</b>', 0, True, 0.5, "precise tag match",
     {"match": True}),
    
    # non-greedy
    ("R008", "greedy_overcapture", r'a="(.*?)"', 'a="foo" b="bar"', 0, True, 0.5, "non-greedy extractor",
     {"match": True, "groups": ["foo"]}),
    ("R009", "greedy_overcapture", r'<.*?>', '<b>hi</b>', 0, True, 0.5, "non-greedy tag",
     {"match": True}),
    
    # nested quantifier danger - safe short inputs
    ("R010", "catastrophic_risk", r"(a+)+b", "aaab", 0, True, 0.5, "nested quantifier - matching (safe)",
     {"match": True}),
    ("R011", "catastrophic_risk", r"(a+)+b", "a" * 15 + "X", 0, False, 1.0, "nested quantifier - failing (SLOW - subprocess)",
     {"match": False, "may_timeout": True}),
    ("R012", "catastrophic_risk", r"(a|a)*b", "a" * 12 + "X", 0, False, 1.0, "alternation overlap - failing (subprocess)",
     {"match": False, "may_timeout": True}),
    ("R013", "catastrophic_risk", r"(a*)*b", "a" * 12 + "X", 0, False, 1.0, "optional-repeat explode (subprocess)",
     {"match": False, "may_timeout": True}),
    
    # safer equivalent
    ("R014", "precise_pattern", r"a+b", "aaab", 0, True, 0.5, "safer equivalent to (a+)+b",
     {"match": True}),
    
    # atomic / possessive
    ("R015", "atomic_or_possessive", r"(?>a+)b", "aaab", 0, True, 0.5, "atomic group - if supported",
     {"match": True, "requires_atomic": True}),
    ("R016", "atomic_or_possessive", r"a++b", "aaab", 0, True, 0.5, "possessive quantifier - if supported",
     {"match": True, "requires_atomic": True}),
    ("R017", "atomic_or_possessive", r"(?>a+)b", "a" * 15 + "X", 0, True, 0.5, "atomic group fails fast",
     {"match": False, "requires_atomic": True}),
    
    # backreference
    ("R018", "backreference", r"(['\"])(.*?)\1", 'x="foo" y=\'bar\'', 0, True, 0.5, "matching quote backreference",
     {"match": True}),
    ("R019", "backreference", r"(\w+)\s+\1", "hello hello world", 0, True, 0.5, "repeated word",
     {"match": True, "groups": ["hello"]}),
    
    # lookaround
    ("R020", "lookaround", r"\w+(?=;)", "foo; bar; baz", 0, True, 0.5, "positive lookahead",
     {"match": True}),
    ("R021", "lookaround", r"(?<!\w)foo(?!\w)", "foo food foobar", 0, True, 0.5, "lookbehind + lookahead word boundary",
     {"match": True}),
    
    # flags caveat
    ("R022", "flags_caveat", r"^foo", "bar\nfoo\nbaz", 0, True, 0.5, "multiline without re.M - no match",
     {"match": False}),
    ("R023", "flags_caveat", r"^foo", "bar\nfoo\nbaz", re.MULTILINE, True, 0.5, "multiline with re.M - match",
     {"match": True}),
    ("R024", "flags_caveat", r"a.b", "a\nb", 0, True, 0.5, "dotall off - no match",
     {"match": False}),
    ("R025", "flags_caveat", r"a.b", "a\nb", re.DOTALL, True, 0.5, "dotall on - match",
     {"match": True}),
    
    # word boundary
    ("R026", "flags_caveat", r"\bfoo\b", "foobar foo baz", 0, True, 0.5, "word boundary",
     {"match": True}),
    
    # unicode word char
    ("R027", "unicode_caveat", r"\w+", "café_123", 0, True, 0.5, "unicode word chars",
     {"match": True}),
    ("R028", "unicode_caveat", r"\w+", "café_123", re.ASCII, True, 0.5, "ascii-only word chars - é breaks",
     {"match": True}),
    
    # email-ish / url-ish (scoped, not oversold)
    ("R029", "normal", r"[\w.+-]+@[\w-]+\.[\w.-]+", "test@example.com", 0, True, 0.5, "simple email-ish (not RFC5322)",
     {"match": True}),
    ("R030", "normal", r"https?://[^\s]+", "visit https://example.com/path ok", 0, True, 0.5, "simple url-ish",
     {"match": True}),
    
    # string method baseline cases
    ("R031", "string_method", None, "hello world", 0, True, 0.5, "str.find baseline",
     {"string_method": "find", "needle": "world", "found": True}),
    ("R032", "string_method", None, "foo,bar,baz", 0, True, 0.5, "str.split baseline",
     {"string_method": "split", "sep": ",", "found": True}),
    ("R033", "string_method", None, "hello.py", 0, True, 0.5, "str.endswith baseline",
     {"string_method": "endswith", "needle": ".py", "found": True}),
    ("R034", "string_method", None, "test@example.com", 0, True, 0.5, "str in baseline",
     {"string_method": "in", "needle": "@", "found": True}),
    
    # invalid regex
    ("R035", "invalid_regex", r"[unclosed", "test", 0, True, 0.5, "invalid regex syntax",
     {"compile_error": True}),
    ("R036", "invalid_regex", r"(?invalid)", "test", 0, True, 0.5, "invalid group syntax",
     {"compile_error": True}),
    
    # no-match cases
    ("R037", "normal", r"xyz", "abc def", 0, True, 0.5, "no match case",
     {"match": False}),
    ("R038", "normal", r"\d+", "no digits here", 0, True, 0.5, "no match digits",
     {"match": False}),
    
    # naive greedy failure cases
    ("R039", "naive_negative", r'.*=.*', 'a="foo" b="bar"', 0, True, 0.5, "naive greedy overcapture",
     {"match": True, "overcapture": True}),
    ("R040", "naive_negative", r"<.*>", "<a><b><c>", 0, True, 0.5, "naive tag greedy",
     {"match": True, "overcapture": True}),
    
    # more catastrophic - tiny inputs, subprocess guarded
    ("R041", "catastrophic_risk", r"(a+|b+)*c", "a" * 12 + "X", 0, False, 1.0, "alt nested quantifier fail",
     {"match": False, "may_timeout": True}),
    ("R042", "catastrophic_risk", r"(.*)*x", "a" * 12 + "y", 0, False, 1.0, "dot-star nested fail",
     {"match": False, "may_timeout": True}),
    
    # safer versions
    ("R043", "precise_pattern", r"[^=]*=[^ ]*", 'a="foo" b="bar"', 0, True, 0.5, "precise attr pattern",
     {"match": True}),
    
    # backreference more
    ("R044", "backreference", r"<(\w+)>.*?</\1>", "<b>hi</b>", re.DOTALL, True, 0.5, "matching tag backreference",
     {"match": True, "groups": ["b"]}),
    
    # lookaround more
    ("R045", "lookaround", r"\d+(?=px)", "10px 20em 30px", 0, True, 0.5, "digits followed by px",
     {"match": True}),
    
    # flags: IGNORECASE
    ("R046", "flags_caveat", r"foo", "FOO bar", 0, True, 0.5, "case sensitive no match",
     {"match": False}),
    ("R047", "flags_caveat", r"foo", "FOO bar", re.IGNORECASE, True, 0.5, "ignorecase match",
     {"match": True}),
    
    # unicode word boundary caveat
    ("R048", "unicode_caveat", r"\b\w+\b", "café naïve", 0, True, 0.5, "unicode word boundaries",
     {"match": True}),
    
    # string method cases - more
    ("R049", "string_method", None, "  trim me  ", 0, True, 0.5, "str.strip baseline",
     {"string_method": "strip", "found": True}),
    ("R050", "string_method", None, "FOO", 0, True, 0.5, "str.lower baseline",
     {"string_method": "lower", "found": True}),
    
    # invalid / no-match
    ("R051", "invalid_regex", r"*foo", "test", 0, True, 0.5, "nothing to repeat",
     {"compile_error": True}),
    ("R052", "normal", r"nomatch", "completely different", 0, True, 0.5, "guaranteed no match",
     {"match": False}),
]

def build_expected(pattern, input_str, flags, expected_dict, category):
    """Build expected observations using re as baseline (for safe patterns only)."""
    result = dict(expected_dict)
    result["pattern"] = pattern
    result["input"] = input_str
    result["flags"] = flags
    result["category"] = category
    
    # Try compiling (unless expected compile_error)
    if pattern is None:
        result["is_string_method_case"] = True
        return result
    
    try:
        cp = re.compile(pattern, flags)
        result["compile_ok"] = True
    except re.error as e:
        result["compile_ok"] = False
        result["compile_error_msg"] = str(e)
        return result
    
    # Only run search inline for safe cases
    safe = expected_dict.get("may_timeout") is not True and category not in {"catastrophic_risk"}
    if safe:
        try:
            m = cp.search(input_str)
            if m:
                result["actual_match"] = True
                result["actual_groups"] = list(m.groups())
                result["actual_span"] = m.span()
                result["actual_text"] = m.group(0)
            else:
                result["actual_match"] = False
        except Exception as e:
            result["search_error"] = str(e)
    
    return result

def main():
    OUT_DIR.mkdir(exist_ok=True)
    seen = set()
    with OUT_FILE.open("w", encoding="utf-8") as f:
        for case_id, category, pattern, input_str, flags, safe_inline, timeout_s, notes, expected_dict in RAW_CASES:
            if case_id in seen:
                raise ValueError(f"duplicate {case_id}")
            seen.add(case_id)
            expected = build_expected(pattern, input_str, flags, expected_dict, category)
            rec = {
                "case_id": case_id,
                "category": category,
                "pattern": pattern,
                "input": input_str,
                "flags": flags,
                "safe_inline": safe_inline,
                "timeout_s": timeout_s,
                "notes": notes,
                "expected": expected,
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    size = OUT_FILE.stat().st_size
    # Check atomic support
    atomic_ok = False
    try:
        re.compile(r"(?>a+)")
        atomic_ok = True
    except re.error:
        pass
    print(f"Wrote {len(RAW_CASES)} cases to {OUT_FILE} ({size} bytes), re_atomic_support={atomic_ok}, python={sys.version.split()[0]}")

if __name__ == "__main__":
    main()
