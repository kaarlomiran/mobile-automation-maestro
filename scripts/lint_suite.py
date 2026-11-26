#!/usr/bin/env python3
"""Static checks for the rules in CLAUDE.md and the prompts. No device needed. Exit 0 = clean, 1 = problems.
Usage: .venv/bin/python scripts/lint_suite.py        (needs PyYAML and ./pom: run scripts/sync-pom.sh first)
Checks: flows (header, tags, launchApp first, page objects only, assertions, no coordinates), page-object files and
their inputs, test plans (format and flow references), repo paths named in docs, Android/iOS prompts in step.
It cannot judge whether an assertion proves the right thing: that stays a review job."""
import difflib, pathlib, re, sys
import yaml

root = pathlib.Path(__file__).resolve().parent.parent
PLATFORMS = ("android", "ios")
ASSERTS = ("assertVisible", "assertNotVisible", "extendedWaitUntil", "assertTrue")
problems = []
def bad(where, msg): problems.append(f"{where.relative_to(root) if isinstance(where, pathlib.Path) else where}: {msg}")
if not (root / "pom").is_dir(): sys.exit("./pom is missing: run scripts/sync-pom.sh first")

cache = {}
def load(path):
    """(config, commands) of a Maestro file, or None when it cannot be read."""
    if path not in cache:
        try:
            docs = list(yaml.safe_load_all(path.read_text()))
            assert len(docs) == 2 and isinstance(docs[0], dict) and isinstance(docs[1], list), "expected a config block, '---', then a command list"
            cache[path] = (docs[0], docs[1])
        except Exception as e:
            bad(path, f"cannot parse: {e}"); cache[path] = None
    return cache[path]

def command(c):
    """(name, argument) of one command."""
    return (c, None) if isinstance(c, str) else next(iter(c.items()))

def walk(path, commands, env, seen):
    """Yield (file, name, argument) for every command, following runFlow; report missing files and missing inputs."""
    for c in commands:
        name, arg = command(c)
        yield path, name, arg
        if isinstance(arg, dict) and "point" in str(arg): bad(path, f"{name} uses screen coordinates (point:)")
        if name == "repeat" or (name == "runFlow" and isinstance(arg, dict) and "commands" in arg):
            yield from walk(path, arg.get("commands", []), env, seen)
        if name != "runFlow": continue
        ref, extra = (arg, {}) if isinstance(arg, str) else (arg.get("file"), arg.get("env") or {})
        if not ref: continue
        target = (path.parent / ref).resolve()
        if not target.is_file(): bad(path, f"runFlow file does not exist: {ref}"); continue
        loaded = load(target)
        if not loaded: continue
        inner = set(env) | set(extra)
        code = "\n".join(l.split(" #")[0] for l in target.read_text().splitlines() if not l.lstrip().startswith("#"))
        for var in sorted(set(re.findall(r"\$\{([A-Z][A-Z0-9_]*)\}", code)) - inner):
            bad(path, f"{ref} needs input {var}, which is not passed in env")
        if target not in seen:
            yield from walk(target, loaded[1], inner, seen | {target})

def starts_with_launch(path):
    loaded = load(path)
    if not loaded or not loaded[1]: return False
    name, arg = command(loaded[1][0])
    if name == "launchApp": return True
    ref = arg if isinstance(arg, str) else (arg or {}).get("file")
    return name == "runFlow" and bool(ref) and (path.parent / ref).is_file() and starts_with_launch((path.parent / ref).resolve())

# ---- flows and shared setup ------------------------------------------------------------------------------------------
def only_page_calls(path, commands):
    for c in commands:
        name, arg = command(c)
        if name not in ("launchApp", "runFlow") or (name == "runFlow" and isinstance(arg, dict) and "commands" in arg):
            bad(path, f"'{name}' in a test file: selectors and actions belong in a page object")

flows = {p: sorted((root / "flows" / p).glob("*.yaml")) for p in PLATFORMS + ("common",)}
for platform, files in flows.items():
    ids = {}
    for f in files:
        m = re.fullmatch(r"(TC\d{2})_[a-z0-9_]+\.yaml", f.name)
        if not m: bad(f, "file name is not TC<NN>_<category>_<short_title>.yaml")
        else:
            if m.group(1) in ids: bad(f, f"{m.group(1)} already used by {ids[m.group(1)]}")
            ids[m.group(1)] = f.name
            if not f.read_text().startswith(f"# {m.group(1)} ["): bad(f, f"first line is not '# {m.group(1)} [category][area] purpose'")
        loaded = load(f)
        if not loaded: continue
        config, commands = loaded
        if config.get("appId") != "${APP_ID}": bad(f, "appId is not ${APP_ID}")
        if not {"smoke", "regression"} & set(config.get("tags") or []): bad(f, "tags need smoke or regression")
        only_page_calls(f, commands)
        if not starts_with_launch(f): bad(f, "does not start with launchApp (directly or through its setup subflow)")
        done = list(walk(f, commands, {"APP_ID"}, {f}))
        used = {w for w, _, _ in done}
        if not any(w.name == "app_assert_no_crash.yaml" for w in used): bad(f, "no app_assert_no_crash call")
        if not any(n in ASSERTS and w.name != "app_assert_no_crash.yaml" for w, n, _ in done): bad(f, "no assertion besides the crash guard")
        other = "ios" if platform == "android" else "android"
        for w in used:
            if platform in PLATFORMS and (root / "pom" / other) in w.parents: bad(f, f"uses a {other} page object: {w.name}")
for f in sorted((root / "flows" / "subflows").glob("*.yaml")):
    if loaded := load(f):
        only_page_calls(f, loaded[1])
        list(walk(f, loaded[1], {"APP_ID"}, {f}))
for platform in PLATFORMS:
    for f in sorted((root / "pom" / platform / "pages").glob("*.yaml")):
        if loaded := load(f):
            if loaded[0].get("appId") != "${APP_ID}": bad(f, "appId is not ${APP_ID}")
            if re.search(r"^\s*(-\s*)?point:", f.read_text(), re.M): bad(f, "uses screen coordinates (point:)")

# ---- test plans (a ticket newer than its plan is normal work in progress; see ticket_status.py) -----------------------
for platform in PLATFORMS:
    planned = set()
    for plan in sorted((root / "specs" / platform).glob("*.md")):
        text = plan.read_text()
        src = re.search(r"^source:\s*(\S+)", text, re.M)
        if not src or src.group(1) != f"tickets/{platform}/{plan.name}": bad(plan, f"'source:' must be tickets/{platform}/{plan.name}")
        elif not (root / src.group(1)).is_file(): bad(plan, f"source ticket does not exist: {src.group(1)}")
        if not re.search(r"^source-sha:\s*[0-9a-f]{12}\s*$", text, re.M): bad(plan, "missing 'source-sha: <12 hex>'")
        parts = re.split(r"^(#### \d+\.\d+\b.*)$", text, flags=re.M)
        if len(parts) < 3: bad(plan, "no '#### N.N' scenarios")
        for head, body in zip(parts[1::2], parts[2::2]):
            sid = head[5:].split()[0]
            if not re.search(r"\(TC-\d{2}\)", head): bad(plan, f"scenario {sid}: heading lacks (TC-NN)")
            status = re.search(r"^\*\*Status:\*\*\s*(PENDING|GENERATED)", body, re.M)
            if not status: bad(plan, f"scenario {sid}: needs '**Status:** PENDING' or '**Status:** GENERATED...'"); continue
            refs = re.findall(rf"flows/{platform}/[\w.-]+\.yaml", body)
            planned |= set(refs)
            if status.group(1) == "GENERATED":
                if not refs: bad(plan, f"scenario {sid}: GENERATED but names no flow file")
                for r in refs:
                    if not (root / r).is_file(): bad(plan, f"scenario {sid}: flow file does not exist: {r}")
    for f in flows[platform]:
        if str(f.relative_to(root)) not in planned: bad(f, f"no scenario in specs/{platform}/ names this flow")

# ---- repo paths named in the docs -------------------------------------------------------------------------------------
docs = [root / n for n in ("CLAUDE.md", "README.md", "docs/DEVICE-MATRIX.md", "docs/KNOWN-ISSUES.md", "tickets/README.md")]
docs += sorted((root / "docs" / "prompts").rglob("*.md")) + sorted((root / ".claude" / "skills").rglob("SKILL.md"))
PATH = re.compile(r"(?<![\w/.-])((?:scripts|config|docs|flows|tickets|specs|sessions|\.claude|\.github|\.vscode)/[\w./-]*|[\w-]+\.lock\b)(?![\w<*{$])")
for d in docs:
    if not d.is_file(): bad(d, "expected document is missing"); continue
    text = d.read_text()
    for link in re.findall(r"\]\(([^)#\s]+)[^)]*\)", text):
        if "://" not in link and "<" not in link and not (d.parent / link).exists(): bad(d, f"broken link: {link}")
    for ref in {m.rstrip(".") for m in PATH.findall(re.sub(r"\]\([^)]*\)", "]", text))}:
        if not (root / ref).exists(): bad(d, f"names a path that does not exist: {ref}")

# ---- Android and iOS prompts stay in step ------------------------------------------------------------------------------
PLATFORM_ONLY = re.compile(r"Shared setup:|emulator|simulator|adb|xcrun|\.apk|\.app\b|iPhone|iPad|Tablets|Off-screen|regular expressions|run-matrix|DEVICE_|APP_ID|PLAT-only")
for name in ("pipeline", "planner", "generator", "heal"):
    pair = [root / "docs" / "prompts" / p / f"{name}.md" for p in PLATFORMS]
    if not all(f.is_file() for f in pair): bad(f"docs/prompts/*/{name}.md", "needed for both platforms"); continue
    a, i = [re.sub(r"\b(android|ios)\b", "PLAT", f.read_text(), flags=re.I).splitlines() for f in pair]
    for line in difflib.ndiff(a, i):
        if line[0] in "+-" and line[2:].strip() and not PLATFORM_ONLY.search(line[2:]):
            bad(pair[0 if line[0] == "-" else 1], f"shared wording differs from the other platform: '{line[2:].strip()[:80]}'")
    for f in pair:
        text = f.read_text()
        if "Follow CLAUDE.md" not in text: bad(f, "does not say 'Follow CLAUDE.md'")
        if name != "planner":
            for skill in ("verify-run-outputs", "triage-machine-failures"):
                if skill not in text: bad(f, f"does not invoke {skill}")

print("\n".join(f"- {p}" for p in problems))
n = sum(len(v) for v in flows.values())
print(f"LINT {'FAIL: ' + str(len(problems)) + ' problem(s)' if problems else 'PASS'} ({n} flows, {len(docs)} documents checked)")
sys.exit(1 if problems else 0)
