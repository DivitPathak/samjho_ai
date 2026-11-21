"""Pure-Python logic: mask personal data, detect document type, apply rules.
No web, OCR or AI imports here, so it is easy to test."""
import re

# ---------- mask personal data ----------
ACCOUNT = re.compile(r"(?i)((?:a/c|acct?\.?|account)\s*(?:no\.?|number|#)?\s*[:\-]?\s*)\d{9,18}\b")
PII = [(r"\b\d{4}\s?\d{4}\s?\d{4}\b", "[AADHAAR]"),
       (r"\b[A-Z]{5}\d{4}[A-Z]\b", "[PAN]"),
       (r"(?:\+91[\s-]?)?\b[6-9]\d{9}\b", "[PHONE]"),
       (r"[\w.+-]+@[\w-]+\.[\w.]+", "[EMAIL]")]

def mask(t: str) -> str:
    t = ACCOUNT.sub(lambda m: m.group(1) + "[ACCOUNT]", t)  # only numbers labelled as accounts
    for p, r in PII:
        t = re.sub(p, r, t)
    return t

# ---------- detect document type ----------
KW = {"rent": "tenant landlord lessor lessee rent deposit lock-in",
      "loan": "loan borrower emi interest prepayment foreclosure lender",
      "insurance": "insured premium sum-assured nominee policy exclusion claim"}

def doc_type(t: str) -> str:
    t = t.lower().replace("sum assured", "sum-assured")
    score = {k: sum(len(re.findall(r"\b" + re.escape(w) + r"(?:s|es)?\b", t)) for w in ws.split())
             for k, ws in KW.items()}
    best = max(score, key=score.get)
    return best if score[best] >= 3 else "unknown"   # FIX: no more silent "rent" default

# ---------- rules engine (rules decide the verdict, not the AI) ----------
# Thresholds are guidelines. Have a CA / lawyer verify them before launch.
AMT = r"(?:(?!deposit)[^.\d]){0,40}(?:\brs\.?|\binr\b|₹)\s*(\d[\d,]*)"

def check(kind: str, text: str, inc: int, emi: int):
    F = []
    has = lambda p: re.search(p, text, re.S | re.I)          # FIX: search original text, not .lower()
    n = lambda m: int(m.group(1).replace(",", ""))

    def snip(m):                                              # FIX: cut on word boundaries
        a, b = max(0, m.start() - 60), min(len(text), m.end() + 100)
        if a > 0:
            sp = text.find(" ", a, m.start()); a = sp + 1 if sp != -1 else a
        if b < len(text):
            sp = text.rfind(" ", m.end(), b); b = sp if sp != -1 else b
        return " ".join(text[a:b].split())

    def add(i, lv, title, why, ask, m=None):
        F.append(dict(id=i, level=lv, title=title, why=why, ask=ask, quote=snip(m) if m else ""))

    if kind == "rent":
        r, d = has(r"\brent\b" + AMT), has(r"\bdeposit\b" + AMT)
        if r and inc and n(r) / inc > .3:
            add("rent_high", "red" if n(r) / inc > .4 else "amber", "Rent is high for your income",
                f"Rent is {n(r)/inc:.0%} of your income. About 30% is comfortable.", "Can the rent be lowered?", r)
        if r and d and n(d) > 2 * n(r):
            add("deposit_high", "red", "Deposit is more than 2 months' rent",
                "The Model Tenancy Act 2021 suggests a home deposit of at most 2 months' rent. Your state's law may differ.",
                "Ask to reduce the deposit.", d)
        if not has(r"refund[^.]{0,80}(?:\d+|one|two|three|fifteen|thirty|sixty)\s*(?:\(\d+\)\s*)?(?:days?|months?)"):
            add("no_refund", "red", "No deadline to return your deposit", "The owner can delay giving your money back.",
                "Ask to add: deposit returned within 15 days of leaving.")
        if has(r"lock-?in") and not has(r"notice[^.]{0,60}(?:month|days)|early termination"):
            add("lockin", "amber", "Lock-in with no way out", "You may lose money if you must leave early.",
                "Ask for a 1-month notice exit.")
        if has(r"(?:increase|enhance|hike|raise)[^.]{0,60}\brent\b") and not has(
                r"(?:increase|enhance|hike|raise|escalat\w+)[^.]{0,80}\d+\s*%|\d+\s*%[^.]{0,80}(?:increase|escalat\w+|hike)"):
            add("hike", "amber", "Rent can go up without a limit", "The owner can raise rent by any amount.",
                "Ask for a fixed yearly rise, like 5%.")

    elif kind == "loan":
        p = has(r"(?:prepayment|foreclosure|pre-closure)[^.]{0,120}\d+(?:\.\d+)?\s*%")
        if p: add("prepay", "amber", "Charge for paying the loan early", "Closing the loan early costs extra.",
                  "Ask for zero prepayment charges.", p)
        if has(r"\b(?:floating|variable|reset)\b"):
            add("floating", "amber", "Interest rate can change", "Your EMI or loan period can rise later.",
                "Ask how often the rate changes.")
        f = has(r"processing fee|administrative charge|documentation charge")
        if f: add("fees", "amber", "Extra fees at the start", "Fees are charged before you get the money.",
                  "Ask for all charges in writing.", f)
        e = has(r"\bemi\b" + AMT)
        if e and inc and (n(e) + emi) / inc > .4:
            add("emi_high", "red" if (n(e) + emi) / inc > .5 else "amber", "EMIs are heavy for your income",
                f"All EMIs would be {(n(e)+emi)/inc:.0%} of your income. Up to 40% is safer.",
                "Ask for a longer period or a smaller loan.", e)

    elif kind == "insurance":
        for i, p, t, w in (("excl", r"\bexclusions?\b", "Read the exclusions", "Some cases are not paid by the insurer."),
                           ("wait", r"waiting period", "Waiting period", "Claims may not be paid in the first months or years."),
                           ("copay", r"co-?pay|sub-?limit|room rent", "You pay part of the bill",
                            "Limits or co-pay reduce what you get back.")):
            if has(p): add(i, "amber", t, w, "Ask the agent to explain this in writing.")
        s = has(r"(?:sum assured|sum insured|\bcover(?:age)?\b)" + AMT)
        if s and inc and has(r"\bterm (?:life|plan|insurance)|\blife insurance|sum assured") and n(s) < 10 * inc * 12:
            add("cover_low", "red", "Cover may be too low",
                f"Cover is {n(s)/(inc*12):.0f}x your yearly income. 10-15x is advised for term life.",
                "Ask for a higher cover.", s)
    return F

def verdict(F) -> str:
    lv = {f["level"] for f in F}
    return "RED" if "red" in lv else "AMBER" if "amber" in lv else "GREEN"
