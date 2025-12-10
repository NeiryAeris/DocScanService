"""
docsearch_cli.py
Compact, end-to-end CLI for your unstructured-search pipeline on SQLite + FTS5.

Subcommands:
  init                                   -> create DB schema (idempotent)
  register-file   --image ... --filename ...
  attach-ocr      --doc-id ... --txt ... [--boxes ...] [--engine ... --lang ... --psm ... --oem ...]
  build-index                             -> rebuild FTS index from current texts (loads text from disk)
  search          --q "query"             -> run FTS query with snippets/highlights
  inspect tables|schema|counts|head|current|doc|fts|integrity|sql [args...]

Examples:
  python docsearch_cli.py init
  DOC_ID=$(python docsearch_cli.py register-file --image ./img.jpg --filename img.jpg)
  python ocr_test.py --image ./img.jpg --txt ./output/out.txt --boxes ./output/out.tsv --lang vie+eng --psm 6 --oem 1
  python docsearch_cli.py attach-ocr --doc-id $DOC_ID --txt ./output/out.txt --boxes ./output/out.tsv \
                                     --engine tesseract --lang vie+eng --psm 6 --oem 1
  python docsearch_cli.py build-index
  python docsearch_cli.py search --q "warranty"
  python docsearch_cli.py inspect current
"""

import argparse, os, sys, sqlite3, json, time, hashlib, re, unicodedata, csv
from datetime import datetime

DB_PATH_DEFAULT = "unstructured_search.sqlite"

# ----------------- Utilities -----------------
def new_id(prefix="id")->str:
    raw = f"{prefix}-{time.time_ns()}".encode("utf-8")
    return hashlib.sha1(raw).hexdigest()

def open_db(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute("PRAGMA case_sensitive_like=OFF;")
    return conn

def normalize_text(s: str) -> str:
    s = unicodedata.normalize("NFC", s)
    s = re.sub(r"-\s*\n\s*", "", s)                 # join hyphenation across line breaks
    s = s.replace("\r", " ").replace("\n", " ")
    s = re.sub(r"[ \t\f\v]+", " ", s).strip()
    return s

def tokenize_basic(s: str):
    tokens, positions = [], []
    pos = 0
    word=[]
    for ch in s:
        if re.match(r"[0-9A-Za-zÀ-ỹ_\-]", ch):
            word.append(ch)
        else:
            if word:
                tokens.append("".join(word).lower())
                pos += 1; positions.append(pos)
                word=[]
    if word:
        tokens.append("".join(word).lower()); pos += 1; positions.append(pos)
    return tokens, positions

def print_rows(title, rows):
    print(f"\n=== {title} ===")
    if not rows:
        print("(no rows)")
        return
    cols = rows[0].keys()
    widths = {c: max(len(c), max(len(str(r[c])) for r in rows)) for c in cols}
    print(" | ".join(c.ljust(widths[c]) for c in cols))
    print("-+-".join("-"*widths[c] for c in cols))
    for r in rows:
        print(" | ".join(str(r[c]).ljust(widths[c]) for c in cols))

# ----------------- Schema -----------------
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS files (
  file_id       TEXT PRIMARY KEY,
  source_path   TEXT NOT NULL,
  filename      TEXT,
  mime_type     TEXT,
  created_at    TEXT,
  meta_json     TEXT
);

CREATE TABLE IF NOT EXISTS documents (
  doc_id          TEXT PRIMARY KEY,
  file_id         TEXT NOT NULL REFERENCES files(file_id),
  page_no         INTEGER,
  thumb_path      TEXT,
  lang            TEXT,
  doc_len_tokens  INTEGER,
  clean_text_path TEXT,
  meta_json       TEXT,
  deleted         INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS ocr_runs (
  ocr_run_id     TEXT PRIMARY KEY,
  engine         TEXT,
  engine_version TEXT,
  params_json    TEXT,
  started_at     TEXT,
  finished_at    TEXT,
  notes          TEXT
);

CREATE TABLE IF NOT EXISTS texts (
  text_id         TEXT PRIMARY KEY,
  doc_id          TEXT NOT NULL REFERENCES documents(doc_id),
  ocr_run_id      TEXT NOT NULL REFERENCES ocr_runs(ocr_run_id),
  raw_text_path   TEXT NOT NULL,
  clean_text_path TEXT,
  avg_conf        REAL,
  token_count     INTEGER,
  is_current      INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS ocr_tokens (
  text_id    TEXT NOT NULL REFERENCES texts(text_id),
  token_idx  INTEGER,
  char_start INTEGER,
  char_end   INTEGER,
  conf       REAL,
  bbox_x REAL, bbox_y REAL, bbox_w REAL, bbox_h REAL,
  PRIMARY KEY (text_id, token_idx)
);

CREATE VIRTUAL TABLE IF NOT EXISTS fts_docs USING fts5(
  doc_id UNINDEXED,
  filename,
  body,
  content='',
  tokenize='unicode61 remove_diacritics 0'
);
"""

# ----------------- Commands -----------------
def cmd_init(args):
    conn = open_db(args.db)
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()
    print(f"Initialized DB at {args.db}")

def cmd_register_file(args):
    conn = open_db(args.db)
    file_id = new_id("file")
    created_at = datetime.utcnow().isoformat()
    source_path = os.path.abspath(args.image)

    conn.execute(
        "INSERT INTO files(file_id, source_path, filename, mime_type, created_at, meta_json) VALUES (?,?,?,?,?,?)",
        (file_id, source_path, args.filename, args.mime, created_at, json.dumps({}))
    )

    doc_id = new_id("doc")
    thumb_path = os.path.abspath(args.thumb) if args.thumb else None
    conn.execute(
        """INSERT INTO documents(doc_id, file_id, page_no, thumb_path, lang, doc_len_tokens, clean_text_path, meta_json, deleted)
           VALUES (?,?,?,?,?,?,?,?,0)""",
        (doc_id, file_id, args.page_no, thumb_path, args.lang, None, None, json.dumps({}))
    )
    conn.commit(); conn.close()
    # Print only doc_id for easy capture
    print(doc_id)

def load_boxes_tsv(path:str):
    if not path or not os.path.exists(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        idx = 0
        for row in reader:
            text = (row.get("text") or "").strip()
            conf = row.get("conf")
            try:
                conf = float(conf) if conf not in (None, "", "-1") else -1.0
            except:
                conf = -1.0
            if text and conf >= 0:
                left = float(row.get("left",0) or 0)
                top  = float(row.get("top",0) or 0)
                w    = float(row.get("width",0) or 0)
                h    = float(row.get("height",0) or 0)
                out.append((idx, text, conf, left, top, w, h)); idx += 1
    return out

def cmd_attach_ocr(args):
    if not os.path.exists(args.txt):
        print(f"Missing --txt: {args.txt}", file=sys.stderr); sys.exit(2)

    raw_text = open(args.txt, "r", encoding="utf-8").read()
    clean = normalize_text(raw_text)
    tokens, _ = tokenize_basic(clean)
    dlen = len(tokens)

    conn = open_db(args.db)
    # ensure doc exists
    row = conn.execute("SELECT doc_id FROM documents WHERE doc_id=? AND deleted=0", (args.doc_id,)).fetchone()
    if not row:
        print(f"doc_id not found or deleted: {args.doc_id}", file=sys.stderr); sys.exit(2)

    # create ocr_run
    ocr_run_id = new_id("ocr")
    now = datetime.utcnow().isoformat()
    params = {"lang": args.lang, "psm": args.psm, "oem": args.oem}
    conn.execute(
        "INSERT INTO ocr_runs(ocr_run_id, engine, engine_version, params_json, started_at, finished_at, notes) VALUES (?,?,?,?,?,?,?)",
        (ocr_run_id, args.engine, args.engine_version, json.dumps(params), now, now, args.notes)
    )
    # flip previous current to 0
    conn.execute("UPDATE texts SET is_current=0 WHERE doc_id=?", (args.doc_id,))
    # insert text version (store actual path to your OCR txt)
    text_id = new_id("text")
    raw_path = os.path.abspath(args.txt)
    clean_path = raw_path  # if later you store a normalized file, change this
    conn.execute(
        """INSERT INTO texts(text_id, doc_id, ocr_run_id, raw_text_path, clean_text_path, avg_conf, token_count, is_current)
           VALUES (?,?,?,?,?,?,?,1)""",
        (text_id, args.doc_id, ocr_run_id, raw_path, clean_path, None, dlen)
    )
    conn.execute("UPDATE documents SET doc_len_tokens=?, clean_text_path=? WHERE doc_id=?",
                 (dlen, clean_path, args.doc_id))

    # optional boxes
    boxes = load_boxes_tsv(args.boxes)
    if boxes:
        conn.executemany(
            "INSERT INTO ocr_tokens(text_id, token_idx, char_start, char_end, conf, bbox_x, bbox_y, bbox_w, bbox_h) VALUES (?,?,?,?,?,?,?,?,?)",
            [(text_id, idx, None, None, conf, left, top, w, h) for (idx, txt, conf, left, top, w, h) in boxes]
        )

    conn.commit(); conn.close()
    print(f"text_id={text_id} ocr_run_id={ocr_run_id}")

def cmd_build_index(args):
    conn = open_db(args.db)
    conn.execute("DELETE FROM fts_docs;")

    rows = conn.execute("""
        SELECT d.doc_id, f.filename, t.clean_text_path
        FROM documents d
        JOIN files f ON f.file_id = d.file_id
        JOIN texts t ON t.doc_id = d.doc_id AND t.is_current = 1
        WHERE d.deleted = 0
    """).fetchall()

    added = 0
    for r in rows:
        doc_id, filename, path = r["doc_id"], r["filename"], r["clean_text_path"]
        if not path or not os.path.exists(path):
            continue
        body = open(path, "r", encoding="utf-8").read()
        conn.execute("INSERT INTO fts_docs(doc_id, filename, body) VALUES (?,?,?)",
                     (doc_id, filename or "", body))
        added += 1
    conn.commit(); conn.close()
    print(f"FTS rebuilt. Indexed {added} document(s).")

def cmd_search(args):
    conn = open_db(args.db)
    sql = """
    SELECT
      d.doc_id,
      f.filename,
      snippet(fts_docs, 2, '[', ']', ' … ', 15) AS snippet,
      highlight(fts_docs, 1, '[', ']') AS filename_hl,
      bm25(fts_docs, 1.2, 0.75) AS score
    FROM fts_docs
    JOIN documents d ON d.doc_id = fts_docs.doc_id
    JOIN files f ON f.file_id = d.file_id
    WHERE fts_docs MATCH ?
    ORDER BY score
    LIMIT ?;
    """
    rows = conn.execute(sql, (args.q, args.limit)).fetchall()
    conn.close()
    print_rows(f"FTS results for: {args.q}", rows)

# -------- Inspect helpers (all in one) --------
def insp_tables(conn):
    return conn.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table','view') ORDER BY type, name").fetchall()

def insp_schema(conn, table=None):
    if table:
        row = conn.execute("SELECT sql FROM sqlite_master WHERE name=? AND type IN ('table','view')", (table,)).fetchone()
        return [dict(sql=row["sql"] if row and row["sql"] else "(none)")]
    return conn.execute("SELECT name, type, sql FROM sqlite_master WHERE type IN ('table','view') ORDER BY type, name").fetchall()

def insp_counts(conn):
    tables = [r["name"] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()]
    out=[]
    for t in tables:
        c = conn.execute(f"SELECT COUNT(*) AS c FROM {t}").fetchone()["c"]
        out.append({"table": t, "count": c})
    return [sqlite3.Row(dict(zip(["table","count"], [o["table"], o["count"]]))) for o in out]

def insp_head(conn, table, n):
    return conn.execute(f"SELECT * FROM {table} LIMIT ?", (n,)).fetchall()

def insp_current(conn):
    return conn.execute("""
        SELECT d.doc_id, f.filename, f.source_path, d.page_no, d.lang,
               d.doc_len_tokens, t.clean_text_path, t.text_id, t.ocr_run_id
        FROM documents d
        JOIN files f ON f.file_id = d.file_id
        JOIN texts t ON t.doc_id = d.doc_id AND t.is_current = 1
        WHERE d.deleted = 0
        ORDER BY f.filename, d.page_no
    """).fetchall()

def insp_doc(conn, doc_id):
    doc = conn.execute("""
        SELECT d.*, f.filename, f.source_path
        FROM documents d JOIN files f ON f.file_id = d.file_id
        WHERE d.doc_id=?
    """,(doc_id,)).fetchall()
    texts = conn.execute("""
        SELECT * FROM texts WHERE doc_id=? ORDER BY is_current DESC, rowid
    """,(doc_id,)).fetchall()
    runs = conn.execute("""
        SELECT * FROM ocr_runs WHERE ocr_run_id IN (SELECT ocr_run_id FROM texts WHERE doc_id=?)
        ORDER BY started_at DESC
    """,(doc_id,)).fetchall()
    return doc, texts, runs

def insp_fts(conn, q):
    return conn.execute("""
        SELECT d.doc_id, f.filename,
               snippet(fts_docs, 2, '[', ']', ' … ', 15) AS snippet,
               bm25(fts_docs, 1.2, 0.75) AS score
        FROM fts_docs
        JOIN documents d ON d.doc_id = fts_docs.doc_id
        JOIN files f ON f.file_id = d.file_id
        WHERE fts_docs MATCH ?
        ORDER BY score
        LIMIT 30
    """, (q,)).fetchall()

def insp_integrity(conn):
    problems = []
    orphans_docs = conn.execute("""
      SELECT d.doc_id FROM documents d
      LEFT JOIN files f ON f.file_id=d.file_id
      WHERE f.file_id IS NULL
    """).fetchall()
    if orphans_docs: problems.append(("Orphan documents", [r["doc_id"] for r in orphans_docs]))

    no_current = conn.execute("""
      SELECT d.doc_id FROM documents d
      LEFT JOIN texts t ON t.doc_id=d.doc_id AND t.is_current=1
      WHERE d.deleted=0 AND t.text_id IS NULL
    """).fetchall()
    if no_current: problems.append(("Docs without current text", [r["doc_id"] for r in no_current]))

    fts_orphans = conn.execute("""
      SELECT fts_docs.doc_id FROM fts_docs
      LEFT JOIN documents d ON d.doc_id = fts_docs.doc_id
      WHERE d.doc_id IS NULL
    """).fetchall()
    if fts_orphans: problems.append(("FTS rows without document", [r["doc_id"] for r in fts_orphans]))

    return problems

def cmd_inspect(args):
    conn = open_db(args.db)
    if args.mode == "tables":
        rows = insp_tables(conn); print_rows("Tables/Views", rows)
    elif args.mode == "schema":
        if args.table:
            rows = insp_schema(conn, args.table)
            print(f"\n=== Schema: {args.table} ===\n{rows[0]['sql'] if rows else '(none)'}")
        else:
            rows = insp_schema(conn); print_rows("Schema", rows)
    elif args.mode == "counts":
        rows = insp_counts(conn); print_rows("Row counts", rows)
    elif args.mode == "head":
        rows = insp_head(conn, args.table, args.n); print_rows(f"Head {args.n} of {args.table}", rows)
    elif args.mode == "current":
        rows = insp_current(conn); print_rows("Current texts", rows)
    elif args.mode == "doc":
        doc, texts, runs = insp_doc(conn, args.doc_id)
        print_rows("Document", doc); print_rows("Texts (versions)", texts); print_rows("OCR runs", runs)
    elif args.mode == "fts":
        rows = insp_fts(conn, args.q); print_rows(f"FTS results for: {args.q}", rows)
    elif args.mode == "integrity":
        probs = insp_integrity(conn)
        if not probs:
            print("\n=== Integrity ===\nOK")
        else:
            print("\n=== Integrity issues ===")
            for title, ids in probs: print(f"- {title}: {ids}")
    elif args.mode == "sql":
        rows = conn.execute(args.query).fetchall()
        print_rows("SQL", rows)
    conn.close()

# ----------------- CLI -----------------
def build_parser():
    p = argparse.ArgumentParser(description="Compact CLI for unstructured-search pipeline (SQLite + FTS5)")
    p.add_argument("--db", default=DB_PATH_DEFAULT, help=f"SQLite DB path (default: {DB_PATH_DEFAULT})")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init")

    s = sub.add_parser("register-file")
    s.add_argument("--image", required=True)
    s.add_argument("--filename", required=True)
    s.add_argument("--mime", default="image/jpeg")
    s.add_argument("--page-no", type=int, default=1)
    s.add_argument("--thumb", default=None)
    s.add_argument("--lang", default=None)

    s = sub.add_parser("attach-ocr")
    s.add_argument("--doc-id", required=True)
    s.add_argument("--txt", required=True, help="OCR .txt from ocr_test.py")
    s.add_argument("--boxes", default=None, help="Optional TSV from image_to_data")
    s.add_argument("--engine", default="tesseract")
    s.add_argument("--engine-version", default="5.x")
    s.add_argument("--lang", default="vie+eng")
    s.add_argument("--psm", default="6")
    s.add_argument("--oem", default="1")
    s.add_argument("--notes", default="")

    s = sub.add_parser("build-index")

    s = sub.add_parser("search")
    s.add_argument("--q", required=True)
    s.add_argument("--limit", type=int, default=20)

    s = sub.add_parser("inspect")
    s.add_argument("mode", choices=["tables","schema","counts","head","current","doc","fts","integrity","sql"])
    s.add_argument("--table")
    s.add_argument("--n", type=int, default=10)
    s.add_argument("--doc-id")
    s.add_argument("--q")
    s.add_argument("--query")

    return p

def main():
    args = build_parser().parse_args()

    if args.cmd == "init":
        cmd_init(args)
    elif args.cmd == "register-file":
        cmd_register_file(args)
    elif args.cmd == "attach-ocr":
        cmd_attach_ocr(args)
    elif args.cmd == "build-index":
        cmd_build_index(args)
    elif args.cmd == "search":
        cmd_search(args)
    elif args.cmd == "inspect":
        cmd_inspect(args)
    else:
        print("Unknown command", file=sys.stderr); sys.exit(1)

if __name__ == "__main__":
    main()
