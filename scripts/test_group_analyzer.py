
from backend.database import get_claim_groups
from backend.intelligence.group_analyzer import analyze_group

groups = get_claim_groups()

for group in groups[:5]:
    result = analyze_group(group["group_id"])

    if result:
        print("\n------------------------------")
        for key, value in result.items():
            print(f"{key}: {value}")
