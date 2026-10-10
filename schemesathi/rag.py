"""The scheme library (RAG): official scheme text, cut into passages, searchable by meaning.

  index()   cut every data/schemes/*.md into passages by section, embed them with
            nomic-embed-text (Ollama, on this Mac) and store them in ChromaDB
  search()  find the passages closest to a question, re-ranked with keyword overlap,
            each returned with a citation tag such as [PM-KISAN · Eligibility]
"""
import hashlib
import re

import chromadb
import ollama

from . import config
from .rules import BY_SLUG

_STOP = set("a an and are as at be by can do does for from get how i if in is it me my of on or the to what when "
            "which who will with you your scheme schemes yojana".split())


def _client():
    return chromadb.PersistentClient(path=str(config.CHROMA_DIR))


def collection():
    return _client().get_or_create_collection("schemes", metadata={"hnsw:space": "cosine"})


def embed(texts, kind="document"):
    prefix = "search_document: " if kind == "document" else "search_query: "
    client = ollama.Client(host=config.OLLAMA_BASE_URL)
    out = []
    for i in range(0, len(texts), 32):
        out.extend(client.embed(model=config.EMBED_MODEL, input=[prefix + t for t in texts[i:i + 32]])["embeddings"])
    return out


def sections(md: str) -> list[tuple[str, str]]:
    """Split a scheme file into (section, text) using its '## ' headings."""
    parts = re.split(r"^## (.+)$", md, flags=re.M)
    return [(parts[i].strip(), parts[i + 1].strip()) for i in range(1, len(parts) - 1, 2) if parts[i + 1].strip()]


def _pieces(paragraph: str, size: int) -> list[str]:
    """A paragraph longer than one chunk is cut at sentence ends (a very long sentence, between words)."""
    if len(paragraph) <= size:
        return [paragraph]
    parts = [w for sent in re.split(r"(?<=[.;!?])\s+", paragraph)
             for w in ([sent] if len(sent) <= size else sent.split(" "))]
    out, cur = [], ""
    for part in parts:
        if cur and len(cur) + len(part) + 1 > size:
            out.append(cur)
            cur = part
        else:
            cur = f"{cur} {part}".strip()
    return out + ([cur] if cur else [])


def chunks(text: str, size=config.CHUNK_CHARS, overlap=config.OVERLAP_CHARS) -> list[str]:
    paras = [x for p in text.split("\n") if p.strip() for x in _pieces(p.strip(), size - overlap)]
    out, cur = [], ""
    for p in paras:
        if cur and len(cur) + len(p) > size:
            out.append(cur)
            tail = cur[-overlap:]
            cur = tail[tail.find(" ") + 1:] + "\n" + p
        else:
            cur = (cur + "\n" + p).strip()
    if cur:
        out.append(cur)
    return out


def plain(text: str) -> str:
    """Markdown emphasis, headings and quote marks removed, for display as plain text."""
    text = re.sub(r"^\s*(#{1,6}|>)\s*", "", text, flags=re.M)
    return re.sub(r"\*\*|__", "", text)


def tag(short: str, section: str) -> str:
    return f"[{short} · {section}]"


def index(force: bool = False) -> dict:
    col = collection()
    if col.count() and not force:
        return {"status": "already indexed", "passages": col.count()}
    if force:
        _client().delete_collection("schemes")
        col = collection()
    ids, docs, metas, headed = [], [], [], []
    for path in sorted(config.SCHEMES_DIR.glob("*.md")):
        slug = path.stem
        s = BY_SLUG.get(slug)
        if not s:
            continue
        for section, body in sections(path.read_text()):
            for i, ch in enumerate(chunks(body)):
                ids.append(hashlib.md5(f"{slug}|{section}|{i}".encode()).hexdigest())
                docs.append(ch)
                metas.append({"slug": slug, "short": s.short, "name": s.name, "section": section, "part": i,
                              "url": f"https://www.myscheme.gov.in/schemes/{slug}"})
                headed.append(f"{s.name} ({s.short}) · {section}\n{ch}")   # context header helps retrieval
    col.add(ids=ids, documents=docs, metadatas=metas, embeddings=embed(headed))
    return {"status": "indexed", "passages": len(ids), "schemes": len({m['slug'] for m in metas})}


def _keywords(text: str) -> set:
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in _STOP and len(w) > 2}


# Question intent -> the section that usually holds the answer (a small boost, not a filter).
INTENT = [("Exclusions", r"\b(who cannot|excluded|exclusions?|not eligible)\b"),
          ("Eligibility", r"\b(eligib\w*|who can|qualif\w*|criteria)\b"),
          ("Documents Required", r"\b(documents?|papers?|proofs?|certificates?)\b"),
          ("Application Process", r"\b(apply|application|register|registration|enrol|enroll|where to|how do i get)\b"),
          ("Benefits", r"\b(how much|amount|benefits?|cover|premium|interest|rupees|₹|rs\.?|cash|money|pension of|subsidy|incentive)\b")]
INTENT_BOOST = 0.05


def intent(question: str) -> str | None:
    q = question.lower()
    return next((section for section, pattern in INTENT if re.search(pattern, q)), None)


def search(question: str, k: int = 5, slug: str | None = None, boost: float | None = None) -> list[dict]:
    col = collection()
    where = {"slug": slug} if slug else None
    res = col.query(query_embeddings=embed([question], "query"), n_results=min(25, col.count()), where=where)
    q = _keywords(question)
    want = intent(question)
    boost = INTENT_BOOST if boost is None else boost
    hits = []
    for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        meaning = 1 - dist
        overlap = len(q & _keywords(doc + " " + meta["name"] + " " + meta["short"])) / (len(q) or 1)
        score = config.ALPHA * meaning + (1 - config.ALPHA) * overlap + (boost if meta["section"] == want else 0)
        hits.append({**meta, "text": doc, "score": round(score, 4),
                     "citation": tag(meta["short"], meta["section"])})
    hits.sort(key=lambda h: -h["score"])
    return hits[:k]


def section_text(slug: str, section: str) -> str:
    path = config.SCHEMES_DIR / f"{slug}.md"
    for name, body in sections(path.read_text()) if path.exists() else []:
        if name.lower().startswith(section.lower()):
            return body
    return ""


# Common documents, matched by keywords, so "Aadhaar Card" and "Copy of Aadhaar" count as one item.
CANON = [("Aadhaar card", ("aadhaar", "aadhar")), ("Bank passbook / account details", ("bank", "passbook")),
         ("Passport-size photograph", ("photo",)), ("Land records", ("landholding", "land holding", "land record", "land ownership", "land document", "khasra", "khatauni")),
         ("Income certificate", ("income",)), ("Caste certificate (SC/ST/OBC)", ("caste", "community certificate")),
         ("Ration card / BPL card", ("ration", "bpl")), ("Disability certificate", ("disab",)),
         ("Age proof / birth certificate", ("age proof", "birth certificate", "date of birth")),
         ("Address proof", ("address", "residence", "domicile")), ("Mobile number", ("mobile",)),
         ("Identity proof (Voter ID, PAN, driving licence)", ("identity", "voter", "pan card", "id proof")),
         ("Job card (MGNREGA)", ("job card",)), ("Mark sheets / admission proof", ("mark", "admission", "fee"))]


def _canon(item: str) -> str | None:
    low = item.lower()
    return next((label for label, keys in CANON if any(k in low for k in keys)), None)


def documents(slugs: list[str]) -> list[dict]:
    """One merged document list across schemes: [{"document", "for": [short names], "wording": [official lines]}]."""
    docs = {}
    for slug in slugs:
        for line in section_text(slug, "Documents Required").split("\n"):
            raw = line.strip()
            if raw.startswith(("#", ">")) or re.fullmatch(r"\*\*.*\*\*:?", raw) or raw.endswith(":"):
                continue                          # sub-headings such as "For Shishu loan", not documents
            item = plain(re.sub(r"^[\s\-\*\d\.\)]+", "", raw)).strip(" *:")
            if not (3 < len(item) < 200) or item.lower().startswith(("note", "indicative", "the following")):
                continue
            label = _canon(item) or item.rstrip(".")
            d = docs.setdefault(label.lower(), {"document": label, "for": [], "wording": []})
            if BY_SLUG[slug].short not in d["for"]:
                d["for"].append(BY_SLUG[slug].short)
            if item not in d["wording"]:
                d["wording"].append(item)
    return sorted(docs.values(), key=lambda d: (-len(d["for"]), d["document"]))
