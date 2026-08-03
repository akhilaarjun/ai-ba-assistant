import json
import os
import pandas as pd
from google import genai
from google.genai import types

class BAEngine:
    def __init__(self, api_key: str):
        """Initialize the Gemini client with the user-provided API key."""
        self.client = genai.Client(api_key=api_key)
        self.model = 'gemini-flash-latest'

    def generate_requirements(self, raw_input: str) -> dict:
        """
        Processes raw meeting notes or text and returns structured BA deliverables.
        Outputs JSON containing User Stories, Gherkin Criteria, and Data Notes.
        """
        system_instruction = """
        You are a Principal Technical Business Analyst AI Agent. 
        Analyze the input text and extract structured project requirements.

        You MUST respond in strict JSON format with the following keys:
        {
          "user_stories": [
            {
              "id": "US-001",
              "role": "User role",
              "action": "Action to perform",
              "benefit": "Business benefit/value",
              "full_story": "As a [role], I want to [action], so that [benefit]."
            }
          ],
          "acceptance_criteria": [
            {
              "story_id": "US-001",
              "gherkin": "Given [context], When [action], Then [expected outcome]."
            }
          ],
          "data_and_tech_notes": [
            "Note on data attributes, reporting, integrations, or security risks"
          ]
        }
        """

        prompt = f"Analyze the following business notes and extract requirements:\n\n{raw_input}"

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2,
                response_mime_type="application/json"
            )
        )
        
        return json.loads(response.text)

    def audit_requirements(self, requirements_json: dict) -> dict:
        """
        Self-audits the generated requirements against the Agile INVEST framework.
        Outputs a score out of 100 and actionable feedback.
        """
        system_instruction = """
        You are an Agile Quality Assurance Auditor.
        Evaluate the provided User Stories against the INVEST framework:
        - Independent
        - Negotiable
        - Valuable
        - Estimable
        - Small
        - Testable

        Respond in strict JSON with:
        {
          "invest_score": 85,
          "strengths": ["List of strong points"],
          "areas_for_improvement": ["List of specific recommendations to improve stories"]
        }
        """

        prompt = f"Audit these requirements:\n{json.dumps(requirements_json, indent=2)}"

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2,
                response_mime_type="application/json"
            )
        )

        return json.loads(response.text)

    def to_pandas_df(self, requirements_json: dict) -> pd.DataFrame:
        """
        Converts generated user stories and criteria into a clean DataFrame for Jira CSV export.
        Handles mapping multiple Gherkin scenarios to a single story ID cleanly.
        """
        stories = requirements_json.get("user_stories", [])
        
        # Group criteria by story_id in case a story has multiple acceptance criteria
        criteria_map = {}
        for c in requirements_json.get("acceptance_criteria", []):
            s_id = c.get("story_id")
            gherkin_text = c.get("gherkin", "")
            if s_id in criteria_map:
                criteria_map[s_id] += f"\n\n{gherkin_text}"
            else:
                criteria_map[s_id] = gherkin_text

        data = []
        for s in stories:
            s_id = s.get("id")
            data.append({
                "Issue ID": s_id,
                "Issue Type": "Story",
                "Summary": f"{s.get('role')} - {s.get('action')}",
                "User Story": s.get("full_story"),
                "Acceptance Criteria (Gherkin)": criteria_map.get(s_id, "N/A"),
                "Status": "To Do"
            })
            
        return pd.DataFrame(data)


if __name__ == "__main__":
    # Safe dummy key for local CLI test (reads from environment variable if set)
    TEST_KEY = os.getenv("GEMINI_API_KEY", "YOUR_API_KEY_HERE")
    
    if TEST_KEY != "YOUR_API_KEY_HERE":
        engine = BAEngine(TEST_KEY)
        sample_text = "Tenants keep calling about repair status. We need a Power BI dashboard for repair teams and SMS notifications for tenants."
        
        print("Generating requirements...")
        res = engine.generate_requirements(sample_text)
        print(json.dumps(res, indent=2))
    else:
        print("BA Engine loaded successfully. Pass an API key to execute standalone tests.")