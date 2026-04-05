"""
V4 Snapshot Validation — RTL Runner

Invokes the existing Icarus Verilog simulation pipeline against a specific
run directory's hex files, then reads back rtl_output.hex.

This module does not reimplement any simulation logic. It calls
sim/run_sim.sh (which calls iverilog + vvp) with the run-specific
sim/ directory temporarily in place of the project-root sim/ directory.

Strategy:
  1. Temporarily copy the run's hex+meta files into project-root sim/
     (run_sim.sh is hardcoded to read from there)
  2. Run sim/run_sim.sh
  3. Copy sim/rtl_output.hex back to the run directory
  4. Restore the original sim/ contents

This approach keeps run_sim.sh unchanged and each run self-contained.

Returns:
    RTLRunResult with status ("pass" | "fail" | "no_simulator") and
    the path to rtl_output.hex written into the run directory.
"""

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass


@dataclass
class RTLRunResult:
    status: str        # "pass" | "fail" | "no_simulator" | "error"
    rtl_hex_path: str  # path to rtl_output.hex in run_dir/sim/
    sim_log: str       # captured stdout+stderr from simulation


def run_rtl_simulation(run_info: dict, project_root: str) -> RTLRunResult:
    """
    Run the RTL simulation for a snapshot run.

    Args:
        run_info:     Dict returned by snapshot_exporter.export_snapshot.
        project_root: Absolute path to the project root directory.

    Returns:
        RTLRunResult
    """
    # --- Check for iverilog ---
    if shutil.which("iverilog") is None:
        return RTLRunResult(
            status="no_simulator",
            rtl_hex_path="",
            sim_log="iverilog not found. Install with: brew install icarus-verilog",
        )

    run_dir  = run_info["run_dir"]
    sim_dir  = run_info["sim_dir"]          # run_dir/sim/
    root_sim = os.path.join(project_root, "sim")

    # Files that run_sim.sh reads from project-root sim/
    _FILES_TO_SWAP = ["input.hex", "kernel.hex", "expected.hex", "meta.json"]

    # --- Back up current project-root sim/ contents ---
    backups: dict[str, str | None] = {}
    for fname in _FILES_TO_SWAP + ["rtl_output.hex"]:
        src = os.path.join(root_sim, fname)
        if os.path.isfile(src):
            bak = src + ".bak"
            shutil.copy2(src, bak)
            backups[fname] = bak
        else:
            backups[fname] = None

    try:
        # --- Install run's hex files into project-root sim/ ---
        for fname in _FILES_TO_SWAP:
            shutil.copy2(os.path.join(sim_dir, fname),
                         os.path.join(root_sim, fname))

        # Remove stale rtl_output.hex so run_sim.sh starts clean
        stale = os.path.join(root_sim, "rtl_output.hex")
        if os.path.isfile(stale):
            os.remove(stale)

        # --- Run simulation ---
        result = subprocess.run(
            ["bash", "sim/run_sim.sh"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        sim_log = result.stdout + result.stderr

        # --- Collect rtl_output.hex ---
        rtl_out_src  = os.path.join(root_sim, "rtl_output.hex")
        rtl_out_dest = os.path.join(sim_dir, "rtl_output.hex")

        if result.returncode != 0:
            return RTLRunResult(status="error", rtl_hex_path="", sim_log=sim_log)

        if not os.path.isfile(rtl_out_src):
            return RTLRunResult(status="error", rtl_hex_path="",
                                sim_log=sim_log + "\nrtl_output.hex not produced.")

        shutil.copy2(rtl_out_src, rtl_out_dest)

        # Determine pass/fail from simulation log
        if "ALL PASS" in sim_log:
            status = "pass"
        else:
            status = "fail"

        return RTLRunResult(status=status, rtl_hex_path=rtl_out_dest, sim_log=sim_log)

    finally:
        # --- Always restore original sim/ contents ---
        for fname, bak in backups.items():
            dest = os.path.join(root_sim, fname)
            if bak is not None:
                shutil.copy2(bak, dest)
                os.remove(bak)
            else:
                # File didn't exist before — remove if we created it
                if os.path.isfile(dest):
                    os.remove(dest)
