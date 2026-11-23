#!/usr/bin/env python3
"""The rules that decided outcomes in testing must stay in the instructions. Each line of
required-rules.tsv is: file <TAB> regular expression <TAB> why it matters. An edit that removes or
rewords one of them fails here; if the rewording is intended, update the line in the same change."""
import os, re
from _common import *
for n, line in enumerate(open(os.path.join(os.path.dirname(__file__), "required-rules.tsv"), encoding="utf-8"), 1):
    if line.startswith("#") or not line.strip(): continue
    f, rx, why = line.rstrip("\n").split("\t")
    p = os.path.join(ROOT, f); text = re.sub(r"\s+", " ", open(p, encoding="utf-8").read()) if os.path.isfile(p) else None
    check(f"{f}: {why}", text is not None and re.search(rx, text, re.I) is not None, "file missing" if text is None else f"line {n}: /{rx}/ not found")
done()
