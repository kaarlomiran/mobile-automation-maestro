#!/usr/bin/env python3
"""Append one sample of the test machine's load and memory: host_metrics.py <file.tsv> <label>. Never fails a run."""
import os, re, subprocess, sys, time
try:
    out, label = sys.argv[1], sys.argv[2]
    ncpu = os.cpu_count() or 1; load = os.getloadavg()[0]; swap = total = avail = ""
    if sys.platform == "darwin":
        run = lambda k: subprocess.check_output(["/usr/sbin/sysctl", "-n", k], text=True)
        total = int(run("hw.memsize")) // 2**20
        swap = int(float(re.search(r"used = ([\d.]+)M", run("vm.swapusage")).group(1)))
    else:
        m = dict(re.findall(r"^(\w+):\s+(\d+)", open("/proc/meminfo").read(), re.M))
        total, avail = int(m["MemTotal"]) // 1024, int(m["MemAvailable"]) // 1024
        swap = (int(m["SwapTotal"]) - int(m["SwapFree"])) // 1024
    new = not os.path.exists(out)
    with open(out, "a") as f:
        if new: f.write("time\tlabel\tload1\tncpu\tswap_used_mb\tmem_total_mb\tmem_avail_mb\n")
        f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')}\t{label}\t{load:.2f}\t{ncpu}\t{swap}\t{total}\t{avail}\n")
except Exception as e:
    print(f"host_metrics: skipped ({e})")
