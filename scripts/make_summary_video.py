#!/usr/bin/env python3
"""Narrated test-summary video (<=60s .mp4) for one run folder: scope, run, risks, issues, summary.
Needs ffmpeg + a male TTS voice: macOS `say` (Daniel) or, on Linux/CI, `espeak-ng`. Optional report/findings.json: {"risks":[...], "issues":[...]} overrides the auto text."""
import json, sys, pathlib, subprocess, tempfile, collections
from PIL import Image, ImageDraw, ImageFont
root = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else "runs").resolve(); name = sys.argv[1]
rep = root / "report" / name
R = json.loads((rep / "results.json").read_text())
fj = rep / "findings.json"
F = json.loads(fj.read_text()) if fj.exists() else {}
import os
VOICE = os.environ.get("NARRATION_VOICE", "Daniel")   # male voice (en_GB)
W, H = 1280, 720
import shutil
FONT = next((p for p in ("/System/Library/Fonts/Helvetica.ttc", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf") if os.path.exists(p)), None)
USE_SAY = shutil.which("say") is not None
f = lambda s: ImageFont.truetype(FONT, s)
BG, FG, ACC, RED, GRN = (18, 24, 38), (240, 244, 250), (110, 168, 255), (255, 107, 107), (88, 214, 141)

tests = R["tests"]; failed = [t for t in tests if t["result"] == "FAIL"]
cats = collections.Counter(c for t in tests for c in t["tags"] if c not in ("smoke", "regression"))
mins, secs = divmod(R["seconds"], 60)
risks = F.get("risks") or ["Live Wikipedia content can change",
                           "Pop-ups such as feature intros can block flows",
                           f"Results apply to {R.get('device_id',R['device'])} only; see device matrix for others"]
issues = F.get("issues") or ([f"{t['tc']}: {t['reason'] or 'failed'}" for t in failed] or ["No failures"])
verdict = "PASS" if not failed else "FAIL"

slides = []  # (title, bullets, narration, thumbs)
slides.append(("Test run summary", [R["run_id"], f"{R['platform'].title()} app {R['app_id']} {R['app_version']}"],
               f"Test summary for {R['run_id'].split('_')[2].replace('-',' ')}, {R['platform']} app {R['app_id'].split('.')[-1]}.", []))
cov = ", ".join(f"{n} {c}" for c, n in cats.most_common())
slides.append(("What was covered", [f"{R['total']} test cases", f"Categories: {cov}", "Onboarding, search, article, navigation"],
               f"We covered {R['total']} test cases: {cov}. Scope spans onboarding, search, opening articles, and navigation.", []))
slides.append(("What was run", [f"Device: {R.get('device_id',R['device'])}, Android {R.get('android','?')}", f"Duration: {mins} min {secs} s", f"Passed {R['passed']} of {R['total']}"],
               f"The suite ran on the {R.get('device_id','emulator').replace('-',' ')} emulator, Android {R.get('android','')}, in {mins} minutes {secs} seconds. {R['passed']} of {R['total']} passed.", []))
slides.append(("Risks", risks, "Main risks. " + ". ".join(risks) + ".", []))
thumbs = [root / "screenshots" / name / f"{t['name']}_{t['result']}.png" for t in failed][:3]
slides.append(("Issues found", issues,
               "Issues found. " + (". ".join(i.replace("TC", "test ") for i in issues) if failed else "No failures in this run."), thumbs))
slides.append(("Summary", [f"Verdict: {verdict}", f"{R['passed']}/{R['total']} passed, {R['failed']} failed", "Screenshots, recordings, traces in run folder"],
               f"Summary. Overall result is {verdict}. " + ("Review the failed tests before release." if failed else "All checks passed. Outputs are saved in the run folder."), []))

def wrap(d, text, font, width):
    words, line, out = text.split(), "", []
    for w in words:
        t = (line + " " + w).strip()
        if d.textlength(t, font=font) > width and line: out.append(line); line = w
        else: line = t
    return out + [line]

tmp = pathlib.Path(tempfile.mkdtemp(prefix="vid-")); parts = []
def build(rate):
    parts.clear(); total = 0
    for i, (title, bullets, narr, th) in enumerate(slides):
        img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img)
        d.rectangle([0, 0, 14, H], fill=RED if (failed and title in ("Issues found", "Summary")) else ACC)
        d.text((70, 60), title, font=f(58), fill=ACC)
        y, maxw = 180, (W - 140 - (300 if th else 0))
        for b in bullets:
            for j, ln in enumerate(wrap(d, b, f(36), maxw)):
                d.text((70 + (0 if j == 0 else 28), y), ("• " if j == 0 else "") + ln, font=f(36), fill=FG); y += 52
            y += 14
        for k, p in enumerate(th):
            try:
                s = Image.open(p); s.thumbnail((260, 520)); img.paste(s, (W - 290 - k * 0, 150 + 0)); break
            except Exception: pass
        d.text((W - 140, H - 50), f"{i+1}/{len(slides)}", font=f(24), fill=(130, 140, 160))
        png, aif, mp4 = tmp / f"s{i}.png", tmp / f"s{i}.aiff", tmp / f"s{i}.mp4"
        img.save(png)
        if USE_SAY:
            subprocess.run(["say", "-v", VOICE, "-r", str(rate), "-o", str(aif), narr], check=True)
        else:   # Linux/CI: espeak-ng male voice (-s = words per minute)
            subprocess.run(["espeak-ng", "-v", "en-us+m3", "-s", str(rate), "-w", str(aif), narr], check=True)
        dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(aif)]).decode()) + 0.5
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(png), "-i", str(aif), "-af", "apad", "-t", f"{dur:.2f}",
                        "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p", "-r", "10", "-c:a", "aac", str(mp4)], check=True)
        parts.append(mp4); total += dur
    return total
for rate in (175, 195, 215, 235):
    total = build(rate)
    if total <= 57: break
lst = tmp / "list.txt"; lst.write_text("".join(f"file '{p}'\n" for p in parts))
(root / "video" / name).mkdir(parents=True, exist_ok=True)
out = root / "video" / name / f"{name}_summary.mp4"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out)], check=True)
print(f"Video: {out} ({total:.1f}s, speech rate {rate})")
