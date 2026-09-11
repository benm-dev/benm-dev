#!/usr/bin/env python3
"""Collect authenticated GitHub activity; publish only aggregate daily counts."""
from __future__ import annotations

import concurrent.futures
import datetime as dt
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import urllib.error
import urllib.parse
import urllib.request

LOGIN = "benm-dev"
KINDS = ("commits", "pull_requests", "issues")
SCOPE = (
    "Unique commits authored by benm-dev on default branches of accessible owned repositories "
    "pushed within this window; issues and pull requests authored by benm-dev and opened within "
    "this window across accessible repositories. Fork duplicates are counted once, as public "
    "if present in a public repository."
)


def api(path):
    """Use existing local authentication. Never print tokens or API payloads."""
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        request = urllib.request.Request("https://api.github.com/"+path, headers={
            "Authorization": "Bearer "+token, "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2026-03-10", "User-Agent": "benm-dev-profile-renderer"})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code == 409 and "Git Repository is empty" in error.read().decode():
                return []
            raise RuntimeError("GitHub request failed; check access and API limits") from None
    if shutil.which("gh"):
        result = subprocess.run(["gh", "api", path, "-H", "X-GitHub-Api-Version: 2026-03-10"],
                                capture_output=True, text=True, timeout=45)
        if result.returncode:
            if "Git Repository is empty" in result.stderr:
                return []
            raise RuntimeError("GitHub request failed; check gh authentication and API limits")
        return json.loads(result.stdout)
    raise RuntimeError("Refresh requires an authenticated GitHub CLI or an existing GH_TOKEN; offline rendering remains available")


def search(resource, query):
    records, page, expected = [], 1, None
    while True:
        data = api(f"search/{resource}?q={urllib.parse.quote(query)}&per_page=100&page={page}")
        if data.get("incomplete_results") or data["total_count"] > 1000:
            raise RuntimeError("Search is incomplete; narrow the collection window before publishing")
        expected = data["total_count"] if expected is None else expected
        if data["total_count"] != expected:
            raise RuntimeError("Activity changed during pagination; retry for a consistent snapshot")
        records.extend(data["items"])
        if len(records) >= expected:
            return records
        if not data["items"]:
            raise RuntimeError("Incomplete activity pagination")
        page += 1


def aggregate(days, commits, openings, captured_at):
    """Allowlist the exported schema; identifiers exist only during collection."""
    index = {date: i for i, date in enumerate(days)}
    metrics = {kind: {visibility: [0]*56 for visibility in ("public", "private")} for kind in KINDS}
    unique = {}
    for record in commits:
        if record["sha"] not in unique or record["visibility"] == "public":
            unique[record["sha"]] = record
    for record in unique.values():
        if record["day"] in index:
            metrics["commits"][record["visibility"]][index[record["day"]]] += 1
    for record in openings:
        if record["day"] in index:
            metrics[record["kind"]][record["visibility"]][index[record["day"]]] += 1
    public = [sum(metrics[k]["public"][i] for k in KINDS) for i in range(56)]
    private = [sum(metrics[k]["private"][i] for k in KINDS) for i in range(56)]
    series = [a+b for a, b in zip(public, private)]
    snapshot = {
        "schema_version": 2, "generated_at": captured_at, "days": days,
        "series": series, "public_series": public, "private_series": private, "metrics": metrics,
        "records_total": sum(series), "max": max(series),
        "seed": hashlib.sha256(json.dumps({"days": days, "metrics": metrics}, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
        "scope": SCOPE,
        "sources": ["GitHub REST commit listings", "GitHub REST issue search"],
        "coverage": "Snapshot of records visible to the authenticated connection; not GitHub's contribution-calendar total. Dates use UTC. Repository names, commit IDs, titles, bodies and source payloads are omitted.",
    }
    return validate(snapshot)


def validate(snapshot):
    allowed = {"schema_version", "generated_at", "days", "series", "public_series", "private_series", "metrics",
               "records_total", "max", "seed", "scope", "sources", "coverage"}
    if set(snapshot) != allowed or snapshot["schema_version"] != 2:
        raise ValueError("Unexpected export fields or schema version")
    days = snapshot["days"]
    if len(days) != 56:
        raise ValueError("Expected 56 days")
    dates = [dt.date.fromisoformat(d) for d in days]
    if any((b-a).days != 1 for a, b in zip(dates, dates[1:])):
        raise ValueError("Dates must be consecutive")
    metrics = snapshot["metrics"]
    if set(metrics) != set(KINDS):
        raise ValueError("Unexpected metrics")
    arrays = [snapshot[k] for k in ("series", "public_series", "private_series")]
    for metric in metrics.values():
        if set(metric) != {"public", "private"}:
            raise ValueError("Unexpected visibility")
        arrays.extend(metric.values())
    if any(len(a) != 56 or any(type(v) is not int or v < 0 for v in a) for a in arrays):
        raise ValueError("Counts must be 56 non-negative integers")
    for i in range(56):
        public = sum(metrics[k]["public"][i] for k in KINDS)
        private = sum(metrics[k]["private"][i] for k in KINDS)
        if (public, private, public+private) != (snapshot["public_series"][i], snapshot["private_series"][i], snapshot["series"][i]):
            raise ValueError("Aggregate totals do not match")
    if snapshot["records_total"] != sum(snapshot["series"]) or snapshot["max"] != max(snapshot["series"]):
        raise ValueError("Incorrect summary")
    expected_seed = hashlib.sha256(json.dumps({"days": days, "metrics": metrics}, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    if snapshot["seed"] != expected_seed:
        raise ValueError("Aggregate seed does not match")
    dt.datetime.fromisoformat(snapshot["generated_at"].replace("Z", "+00:00"))
    return snapshot


def collect():
    now = dt.datetime.now(dt.timezone.utc)
    days = [(now.date()-dt.timedelta(days=55-i)).isoformat() for i in range(56)]
    repositories = search("repositories", f"user:{LOGIN} pushed:>={days[0]} fork:true")

    def commits_in(repository):
        visibility = "private" if repository["private"] else "public"
        result, page = [], 1
        while True:
            records = api(f"repos/{repository['full_name']}/commits?author={LOGIN}&since={days[0]}T00:00:00Z&until={days[-1]}T23:59:59Z&per_page=100&page={page}")
            result.extend({"sha": r["sha"], "visibility": visibility, "day": r["commit"]["committer"]["date"][:10]} for r in records)
            if len(records) < 100:
                return result
            page += 1

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        commits = [r for batch in pool.map(commits_in, repositories) for r in batch]
    openings = []
    for kind, qualifier in (("pull_requests", "pr"), ("issues", "issue")):
        for visibility in ("public", "private"):
            records = search("issues", f"author:{LOGIN} created:{days[0]}..{days[-1]} is:{qualifier} is:{visibility}")
            openings.extend({"kind": kind, "visibility": visibility, "day": r["created_at"][:10]} for r in records)
    return aggregate(days, commits, openings, now.isoformat())


if __name__ == "__main__":
    output = pathlib.Path(__file__).resolve().parents[1]/"activity.json"
    snapshot = collect()
    output.write_text(json.dumps(snapshot, indent=2)+'\n')
    print("Saved aggregate activity:", snapshot["records_total"], "records")
