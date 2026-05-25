from typing import Dict, Any
from datetime import datetime

class TrustCalculator:
    @staticmethod
    def calculate_score(metadata: Dict[str, Any]) -> int:
        score = 0
        info = metadata.get("info", {})
        
        # 1. Package Age (approximate from first release)
        # 2. Download velocity (stubbed for now)
        # 3. Maintainer diversity
        maintainers = info.get("author", "")
        if maintainers:
            score += 10
        
        # 4. GitHub reputation (if home_page is github)
        home_page = info.get("home_page")
        if home_page and "github.com" in home_page:
            score += 15
        
        # 5. Documentation quality
        summary = info.get("summary")
        if summary and len(summary) > 20:
            score += 8
            
        # 6. Release freshness
        # Stub: if has recent releases
        
        # Cap at 100
        return min(max(score, 0), 100)
