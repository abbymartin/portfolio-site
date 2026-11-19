"""Writes books.json for ascii_world from your Hardcover account.

    HARDCOVER_TOKEN=... python3 scripts/hardcover.py <output.json>

Shows, in order (anything missing is left out):
  - currently reading: the most recently started one, tagged or not
  - recently read: the latest finished book on your "Fiction" list and on your
    "Nonfiction" list, each only if finished in the last 6 months. With both, they
    are labelled (fiction) / (nonfiction); with one, just "recently read".
    If neither is that recent, the more recent of the two is shown anyway.
"""
import json
import os
import sys
import urllib.request
from datetime import date, timedelta

USER_ID = 203936                       # your Hardcover user id
CATEGORIES = ["fiction", "nonfiction"]  # list slugs on Hardcover
READING, READ = 2, 3                   # Hardcover status ids
READ_WITHIN = timedelta(days=183)      # ~6 months

QUERY = """
query ($user: Int!, $lists: [String!]) {
  lists(where: {user_id: {_eq: $user}, slug: {_in: $lists}}) { slug list_books { book_id } }
  user_books(where: {user_id: {_eq: $user}, status_id: {_in: [2, 3]}}) {
    status_id date_added last_read_date
    user_book_reads { started_at finished_at }
    book { id title slug image { url } contributions { author { name } } }
  }
}"""


def fetch():
    token = os.environ["HARDCOVER_TOKEN"].strip().removeprefix("Bearer ").strip()
    req = urllib.request.Request(
        "https://api.hardcover.app/v1/graphql",
        data=json.dumps({"query": QUERY, "variables": {"user": USER_ID, "lists": CATEGORIES}}).encode(),
        headers={"content-type": "application/json", "authorization": f"Bearer {token}",
                 "user-agent": "portfolio-site-build"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.load(r)
    if "data" not in body:
        raise SystemExit(f"Hardcover error: {body}")
    return body["data"]


def latest(*dates):
    return max((d for d in dates if d), default="")  # ISO dates sort as strings


def book(b):
    authors = [c["author"]["name"] for c in b.get("contributions") or [] if c.get("author")]
    return {
        "title": b["title"],
        "author": authors[0] if authors else "",
        "cover": (b.get("image") or {}).get("url") or "",
    }


def main(out):
    data = fetch()
    shelf_of = {}
    for lst in data["lists"]:
        for lb in lst["list_books"]:
            shelf_of.setdefault(lb["book_id"], lst["slug"])

    cutoff = (date.today() - READ_WITHIN).isoformat()
    reading, read = None, {}  # read: category -> (date, book)
    for ub in data["user_books"]:
        reads = ub["user_book_reads"] or []
        if ub["status_id"] == READING:
            when = latest(*(r["started_at"] for r in reads)) or ub["date_added"] or ""
            if not reading or when > reading[0]:
                reading = (when, ub["book"])
            continue
        key = shelf_of.get(ub["book"]["id"])
        when = latest(ub["last_read_date"], *(r["finished_at"] for r in reads))
        if key and (key not in read or when > read[key][0]):
            read[key] = (when, ub["book"])

    books = []
    if reading:
        books.append({"label": "currently reading", **book(reading[1])})
    recent = [key for key in CATEGORIES if key in read and read[key][0] >= cutoff]
    if not recent and read:
        recent = [max(read, key=lambda k: read[k][0])]
    for key in recent:
        label = f"recently read ({key})" if len(recent) > 1 else "recently read"
        books.append({"label": label, **book(read[key][1])})

    result = {"books": books}
    with open(out, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1])
