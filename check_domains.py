"""
Keepa API domain codes verification
"""

# Keepa API domain codes reference
keepa_domains = {
    1: "amazon.com (US)",
    2: "amazon.co.uk (UK)", 
    3: "amazon.de (Germany)",
    4: "amazon.fr (France)",
    5: "amazon.co.jp (Japan)",
    6: "amazon.ca (Canada)",
    7: "amazon.cn (China)",
    8: "amazon.it (Italy)",
    9: "amazon.es (Spain)",
    10: "amazon.in (India)",
    11: "amazon.com.mx (Mexico)",
    12: "amazon.com.br (Brazil)",
    13: "amazon.com.au (Australia)",
}

print("🌍 Keepa API Domain Codes:")
print("=" * 40)
for code, marketplace in keepa_domains.items():
    print(f"Domain {code}: {marketplace}")

print("\n🚨 ISSUE FOUND!")
print("=" * 40)
print("Current code: Domain 8")
print(f"Current setting: {keepa_domains[8]}")
print(f"Should be: Domain 4 ({keepa_domains[4]})")

print("\n✅ SOLUTION:")
print("Change domain from 8 to 4 in keepa_api.py")
