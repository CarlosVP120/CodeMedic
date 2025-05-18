from typing import List, Optional, Dict, Any

from pydantic import BaseModel
class IssueAnalysis(BaseModel):
    issue_number: int
    summary: str
    impact: str
    affected_areas: List[str]
    recommendations: List[str]
    technical_details: Optional[Dict[str, Any]]
    solution: Optional[str]