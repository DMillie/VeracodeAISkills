// Reads a Veracode Pipeline Scan results.json and flags the ways a wrong package scans green.
// Every check comes from a case observed on 2026-11-12 (see VALIDATED.md). Zero dependencies.
'use strict';
const SEV = { 5: 'Very High', 4: 'High', 3: 'Medium', 2: 'Low', 1: 'Very Low', 0: 'Informational' };
const THIRD = /(^|\/)(node_modules|vendor|site-packages|dist-packages|\.venv|bower_components)\//i;
const TESTS = /(^|\/)(tests?|__tests__|spec|testdata)\/|[._-](test|spec)\.[a-z]+$/i;

function checkScan(d, opts = {}) {
  const expectedModules = opts.expected_modules || [];
  const expectedPlaces = opts.expected_places || [];
  const flags = [];
  const findings = Array.isArray(d.findings) ? d.findings : [];
  const modules = Array.isArray(d.modules) ? d.modules : [];
  const files = findings.map(f => (((f.files || {}).source_file || {}).file) || '');
  const lines = findings.map(f => Number((((f.files || {}).source_file || {}).line) || 0));

  if (d.scan_status !== 'SUCCESS') flags.push({ level: 'fail', check: 'status', text: `scan_status is ${d.scan_status || 'missing'}: ${d.message || 'no message'}` });
  if (!modules.length) flags.push({ level: 'fail', check: 'modules', text: 'No modules reported: nothing was analysed.' });
  for (const m of expectedModules) {
    if (!modules.some(x => x.toLowerCase().includes(String(m).toLowerCase())))
      flags.push({ level: 'fail', check: 'expected-module', text: `Expected module "${m}" is not in the module list. A deployable was ignored (seen with single-file .NET publish: only the JS module was listed, SUCCESS, 0 findings).` });
  }
  if (findings.length === 0 && d.scan_status === 'SUCCESS')
    flags.push({ level: 'fail', check: 'zero-findings', text: 'SUCCESS with 0 findings. Treat as a packaging problem until a with/without comparison says otherwise (seen with minified bundles, a source zip holding pnpm-workspace.yaml, an unsupported language).' });
  if (findings.length) {
    const unknown = files.filter((f, i) => !f || /^unknown$/i.test(f) || lines[i] <= 1).length;
    if (unknown / findings.length >= 0.8)
      flags.push({ level: 'fail', check: 'no-debug-info', text: `${unknown} of ${findings.length} findings have no file or sit on line 1: the build has no debug information (.NET Release with DebugType=none, Java without -g). Rebuild with symbols.` });
    const third = files.filter(f => THIRD.test(f)).length;
    if (third / findings.length >= 0.3)
      flags.push({ level: 'warn', check: 'third-party', text: `${third} of ${findings.length} findings are in third-party folders: dependencies are being counted as first-party code.` });
    const tests = files.filter(f => TESTS.test(f)).length;
    if (tests) flags.push({ level: 'warn', check: 'tests', text: `${tests} findings are in test code: tests are in the package.` });
  }
  for (const m of modules) {
    if (/^(C#|Java|Scala|Kotlin|Go) files within/i.test(m))
      flags.push({ level: 'warn', check: 'source-of-compiled', text: `Module "${m}" is a source scan of a compiled language. For C# this scanned slowly and missed the SQL injection, path, SSRF and deserialization findings the compiled scan reported.` });
    if (/\d+\.\d+\.\d+/.test(m))
      flags.push({ level: 'warn', check: 'versioned-name', text: `Module "${m}" has a version in its name: the Platform will treat every release as a new module. Rename in the packaging job.` });
  }
  if (modules.length > 1 && modules.filter(m => /\.(dll|exe)$/i.test(m)).length > 1)
    flags.push({ level: 'warn', check: 'two-executables', text: 'More than one .NET executable in one upload: both modules were listed and the second one\'s findings were dropped in testing. Scan one zip per executable.' });
  // A place matches when the reported file and the expected path agree on their tail (absolute or repo-relative paths both work).
  const norm = p => String(p).toLowerCase().split(':')[0].replace(/\\/g, '/');
  const tail = p => norm(p).split('/').filter(Boolean).slice(-2).join('/');
  const missing = expectedPlaces.filter(p => !files.some(f => { const x = norm(f), y = norm(p); return x && (x.includes(y) || y.endsWith(x) || x.endsWith(tail(p)) || y.endsWith(tail(f))); }));
  if (expectedPlaces.length && missing.length)
    flags.push({ level: missing.length === expectedPlaces.length ? 'fail' : 'warn', check: 'expected-places', text: `No finding in ${missing.length} of ${expectedPlaces.length} expected places: ${missing.join(', ')}. Compare package variants; if every variant agrees, report "package proven, result thin" and list them.` });

  const bySev = {}; const byCwe = {};
  for (const f of findings) { const s = SEV[Number(f.severity)] || String(f.severity); bySev[s] = (bySev[s] || 0) + 1; byCwe[f.cwe_id] = (byCwe[f.cwe_id] || 0) + 1; }
  const verdict = flags.some(f => f.level === 'fail') ? 'suspect' : flags.length ? 'check' : 'plausible';
  return { verdict, scan_status: d.scan_status, modules, findings_total: findings.length, by_severity: bySev, by_cwe: byCwe, flags,
    note: 'A plausible verdict is not proof. Proof is a comparison: your package, the auto-packager output, and one deliberate variation give the same findings in the places you expected.' };
}
module.exports = { checkScan };

if (require.main === module) {
  const fs = require('fs'); const a = process.argv.slice(2);
  if (!a.length) { console.error('usage: node scan-check.js results.json [--module NAME]... [--place PATH]...'); process.exit(2); }
  const o = { expected_modules: [], expected_places: [] };
  for (let i = 1; i < a.length; i += 2) { if (a[i] === '--module') o.expected_modules.push(a[i + 1]); if (a[i] === '--place') o.expected_places.push(a[i + 1]); }
  const r = checkScan(JSON.parse(fs.readFileSync(a[0], 'utf8')), o);
  console.log(JSON.stringify(r, null, 2)); process.exit(r.verdict === 'suspect' ? 1 : 0);
}
