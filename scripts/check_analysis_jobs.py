#!/usr/bin/env python3
"""Check analysis job status."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.database import session_scope
from app.models.analysis import AnalysisJob
from sqlmodel import select

with session_scope() as session:
    jobs = session.exec(select(AnalysisJob).order_by(AnalysisJob.created_at.desc()).limit(3)).all()
    print("Recent analysis jobs:")
    for j in jobs:
        print(f"  Job: {j.id[:30]}...")
        print(f"    Status: {j.status}")
        print(f"    Progress: {j.progress}%")
        print(f"    Error: {j.error}")
        print()

