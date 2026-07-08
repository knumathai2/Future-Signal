import json

def process_samples():
    with open("gamma_response_sample.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    samples = []
    missing_unstable = set()
    
    for item in data[:10]:
        # active binary market check:
        # Polymarket events usually contain "markets", and binary ones have outcomes ["Yes", "No"]
        
        markets = item.get("markets", [])
        if not markets:
            continue
            
        market = markets[0] # taking the first market as representative
        outcomes = json.loads(market.get("outcomes", "[]"))
        if outcomes != ["Yes", "No"]:
            continue
            
        sample = {
            "id": item.get("id"),
            "market_id": market.get("id"),
            "title": item.get("title") or market.get("question"),
            "description": item.get("description"),
            "category_tag": item.get("tags") or [], # Check if tags are available
            "current_value": json.loads(market.get("outcomePrices", "[]"))[0] if market.get("outcomePrices") else None,
            "resolution_source": item.get("resolutionSource") or market.get("resolutionSource"),
            "volume": item.get("volume"),
            "liquidity": item.get("liquidity"),
            "created_at": item.get("createdAt"),
            "updated_at": item.get("updatedAt"),
            "end_date": item.get("endDate")
        }
        
        # Check for missing/unstable fields
        if not sample["category_tag"]:
            missing_unstable.add("tags (often empty or missing)")
        if not sample["resolution_source"]:
            missing_unstable.add("resolutionSource (often empty or missing in both event and market)")
            
        samples.append(sample)
        
    with open("polymarket_samples.json", "w", encoding="utf-8") as f:
        json.dump(samples, f, indent=2)
        
    print("Samples extracted:", len(samples))
    print("Missing/Unstable fields identified:", list(missing_unstable))

if __name__ == "__main__":
    process_samples()
