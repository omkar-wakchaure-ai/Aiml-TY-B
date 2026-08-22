from rag_utils import store_new_insight, is_duplicate_insight, get_historical_context

# Test 1: Save news into memory
print("Saving news...")
store_new_insight(
    summary="Competitor X launched a solid-state battery with 500Wh/kg density.",
    source="News",
    category="Product Launch",
    impact_score=9
)

# Test 2: Check duplicate detection
is_dup = is_duplicate_insight("Competitor X released new solid-state battery tech.")
print("Is duplicate?:", is_dup)

# Test 3: Search past context
context = get_historical_context("solid state battery")
print("Retrieved Context:\n", context)