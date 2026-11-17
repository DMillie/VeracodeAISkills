#!/usr/bin/env python3
"""Summarise a Pipeline Scan results.json (or filtered_results.json): counts by severity, top CWEs.
  usage: pipeline_scan_summary.py results.json [--details N]
Severity scale: 5 Very High, 4 High, 3 Medium, 2 Low, 1 Very Low, 0 Informational.
Field names verified live 2026-11-11 against pipeline-scan.jar output: findings[].severity (int),
findings[].cwe_id (str), findings[].issue_type, findings[].files.source_file.{file,line}.
"""
import collections, json, sys
SEV = {5: "Very High", 4: "High", 3: "Medium", 2: "Low", 1: "Very Low", 0: "Informational"}
p = sys.argv[1]; n = int(sys.argv[sys.argv.index("--details") + 1]) if "--details" in sys.argv else 0
d = json.load(open(p)); f = d.get("findings", [])
by = collections.Counter(int(x.get("severity", -1)) for x in f)
print(f"{p}: {len(f)} findings, scan_status={d.get('scan_status')} scan_id={d.get('scan_id')}")
for s in sorted(by, reverse=True): print(f"  {SEV.get(s, s):<13} {by[s]}")
cwes = collections.Counter((x.get("cwe_id"), x.get("issue_type")) for x in f)
print("  top issue types:", "; ".join(f"CWE-{c} {t} x{k}" for (c, t), k in cwes.most_common(6)))
for x in sorted(f, key=lambda x: -int(x.get("severity", 0)))[:n]:
    sf = x.get("files", {}).get("source_file", {})
    print(f"  [{SEV.get(int(x.get('severity', 0)))}] CWE-{x.get('cwe_id')} {x.get('issue_type')} at {sf.get('file')}:{sf.get('line')}")
