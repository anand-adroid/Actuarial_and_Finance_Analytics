"""Structured store = the source of truth for NUMBERS (SQLite).

Numbers are fetched by deterministic, templated SQL — never by similarity search.
In production this is Azure SQL / Synapse / Fabric; the interface is identical.
"""
from __future__ import annotations
import sqlite3, os, csv

class StructuredStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    @classmethod
    def build(cls, db_path: str, input_csvs: dict[str, str]):
        """(Re)create the metrics table and load each labelled input CSV, tagging its source.
        Uses DROP+CREATE instead of deleting the .db file, so it works even when another
        connection is still open (avoids Windows 'file in use' errors)."""
        conn = sqlite3.connect(db_path)
        conn.execute("DROP TABLE IF EXISTS metrics")
        conn.execute("CREATE TABLE metrics (metric TEXT PRIMARY KEY, value TEXT, unit TEXT, source TEXT)")
        for source, path in input_csvs.items():
            with open(path, newline="") as f:
                for row in csv.DictReader(f):
                    conn.execute("INSERT OR REPLACE INTO metrics VALUES (?,?,?,?)",
                                 (row["metric"], row["value"], row["unit"], source))
        conn.commit(); conn.close()
        return cls(db_path)

    def get(self, metric: str) -> dict:
        r = self.conn.execute("SELECT * FROM metrics WHERE metric=?", (metric,)).fetchone()
        if r is None:
            raise KeyError(f"Unknown metric '{metric}' — not in source of truth.")
        return dict(r)

    def fmt(self, metric: str) -> str:
        r = self.get(metric); v, u = r["value"], r["unit"]
        try: num = float(v)
        except ValueError: return v
        if u == "USD": return f"${num:,.0f}"
        if u == "percent": return f"{num:g}%"
        if u == "ratio": return f"{num:g}"
        if u == "count": return f"{int(num):,}"
        return v

    def verified_numbers(self) -> set[float]:
        out = set()
        import re
        for r in self.conn.execute("SELECT value FROM metrics").fetchall():
            try: out.add(round(float(r["value"]), 2))
            except ValueError:
                for tok in re.findall(r"\d+\.?\d*", r["value"]): out.add(round(float(tok), 2))
        return out

    def provenance(self) -> dict[float, str]:
        """Map each verified numeric value -> the metric/source it came from (for the audit table).
        Also maps numbers embedded in label values (e.g. 2026 from a '2026-Q1' period)."""
        import re
        prov = {}
        for r in self.conn.execute("SELECT metric, value, source FROM metrics").fetchall():
            label = f"{r['metric']} ({r['source']})"
            try:
                prov[round(float(r["value"]), 2)] = label
            except ValueError:
                for tok in re.findall(r"\d+\.?\d*", r["value"]):
                    prov.setdefault(round(float(tok), 2), label)
        return prov
