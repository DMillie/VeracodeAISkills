#!/usr/bin/env python3
"""Print the image or the script of one step of a bitbucket-pipelines.yml written in this pack's
layout (`- step: &name`, one `- |` block per script). Standard library only, no YAML parser.
  usage: extract_step.py <file> <anchor> image|script"""
import re, sys
lines = open(sys.argv[1]).read().splitlines(); name, what = sys.argv[2], sys.argv[3]
start = next(i for i, l in enumerate(lines) if re.match(rf"\s*- step: &{re.escape(name)}\s*(#.*)?$", l))
end = next((i for i in range(start + 1, len(lines)) if re.match(r"\s*- step: &|^pipelines:", lines[i])), len(lines))
body = lines[start + 1:end]
if what == "image":
    print(next(l.split("image:", 1)[1].strip() for l in body if l.strip().startswith("image:"))); sys.exit(0)
b = next(i for i, l in enumerate(body) if l.strip() == "- |")
ind = len(body[b]) - len(body[b].lstrip()) + 2; out = []
for l in body[b + 1:]:
    if l.strip() and len(l) - len(l.lstrip()) < ind: break
    out.append(l[ind:])
print("\n".join(out))
