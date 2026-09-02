#!/usr/bin/env python3
"""
월간 자동 갱신 (EC2 cron 용)
- 전체 파이프라인 재실행(원데이터 재수집) → CSV 갱신 → 변경 시 commit/push + GitHub Release
- 실행: KFF_CREDS=~/.kff/api_keys.ini python3 src/update_monthly.py
- cron 예: 0 21 2 * *  (매월 2일 06:00 KST — 전월 데이터 확정 후)
"""
import os, io, re, sys, subprocess, datetime

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "src")
DATA = os.path.join(REPO, "data")
os.environ["KFF_OUT"] = DATA
sys.path.insert(0, SRC)

def run(cmd, **kw):
    print("+", " ".join(cmd))
    return subprocess.run(cmd, cwd=REPO, check=True, capture_output=True, text=True, **kw)

def load_gh_token():
    try:
        creds = io.open(os.path.expanduser("~/.git-credentials")).read()
        m = re.search(r"(ghp_[A-Za-z0-9]+|github_pat_[A-Za-z0-9_]+)", creds)
        if m:
            os.environ["GH_TOKEN"] = m.group(1)
    except Exception:
        pass

def main():
    load_gh_token()
    # 1. 원데이터 강제 재수집 후 FF5 파이프라인 실행
    for f in ["raw_secd.parquet", "raw_funda_full.parquet", "raw_delist.parquet"]:
        p = os.path.join(DATA, f)
        if os.path.exists(p):
            os.remove(p)
    subprocess.run([sys.executable, os.path.join(SRC, "build_ff5.py")],
                   check=True, env={**os.environ})

    # 2. 변경 여부 확인
    st = run(["git", "status", "--porcelain", "data/factors_monthly_kr_ff5.csv"])
    if not st.stdout.strip():
        print("no changes — skip commit")
        return

    # 3. 커밋 · push · 릴리스 (릴리스 → Zenodo가 새 Version DOI 자동 발급)
    tag = "v2." + datetime.date.today().strftime("%Y.%m")
    run(["git", "add", "data/factors_monthly_kr_ff5.csv"])
    run(["git", "commit", "-m", f"Monthly update: factors through previous month ({tag})"])
    run(["git", "push", "origin", "main"])
    try:
        run(["gh", "release", "create", tag, "--title", f"Monthly release {tag}",
             "--notes", "Automated monthly factor update. See data/factors_monthly_kr_ff5.csv"])
    except subprocess.CalledProcessError as e:
        print("release failed (tag may exist):", e.stderr[:200])
    print("done:", tag)

if __name__ == "__main__":
    main()
