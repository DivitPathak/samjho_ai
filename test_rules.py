from rules import mask, doc_type, check, verdict
RENT = """RENT AGREEMENT between landlord Mr. Sharma (PAN ABCDE1234F, phone 9876543210) and tenant Mr. Verma (Aadhaar 1234 5678 9012).
The monthly rent shall be Rs. 18,000, payable by the 5th. The tenant shall pay a security deposit of Rs. 90,000.
There is a lock-in period of 11 months. The landlord may increase the rent at his discretion every year."""
t = mask(RENT)
assert "ABCDE1234F" not in t and "9876543210" not in t and "1234 5678" not in t
assert doc_type(t) == "rent"
ids = {f["id"] for f in check("rent", t, 40000, 0)}
assert ids == {"rent_high", "deposit_high", "no_refund", "lockin", "hike"}, ids
assert verdict(check("rent", t, 40000, 0)) == "RED"
assert doc_type("Hello, this is a shopping list for the weekend.") == "unknown"
assert "[ACCOUNT]" in mask("Pay to A/C No. 123456789012")
assert "1500000" in mask("Loan amount Rs. 1500000")                      # amounts are no longer masked
good = "Rent is Rs. 10,000, deposit Rs. 20,000 refunded within 15 days. Landlord may increase rent by 5% yearly."
assert verdict(check("rent", good, 60000, 0)) == "GREEN"
for f in check("rent", t, 40000, 0):
    assert not f["quote"] or f["quote"][0].isalnum() or f["quote"][0] in "([“"
print("all tests passed")
