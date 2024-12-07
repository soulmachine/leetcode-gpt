import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry


class LeetCode:
    def __init__(self, csrf_token: str, session_id: str):
        """
        Initialize LeetCode API client with authentication.

        Args:
            csrf_token (str): CSRF token for authentication
            session_id (str): Session ID for authentication
        """
        if not csrf_token or not session_id:
            raise ValueError("Both csrf_token and session_id must be provided")

        self.base_url = "https://leetcode.com"
        self.session = requests.Session()

        # Retry strategy for transient errors
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)

        # Set authentication headers and cookies
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
            "Referer": self.base_url,
            "X-Csrftoken": csrf_token,
        }
        self.session.cookies.set("csrftoken", csrf_token)
        self.session.cookies.set("LEETCODE_SESSION", session_id)

        # Validate authentication
        self._validate_authentication()

    def _validate_authentication(self):
        """Check if the CSRF token and session ID are valid."""
        endpoint = f"{self.base_url}/graphql"
        payload = {
            "query": "{ user { username } }"
        }
        try:
            response = self.session.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise ValueError("Invalid csrf_token or session_id") from e


    def _get_question_id(self, problem_slug: str) -> int:
        """Retrieve the question ID from the problem slug using GraphQL."""
        endpoint = f"{self.base_url}/graphql"
        query = {
            "query": """
                query getQuestionId($titleSlug: String!) {
                    question(titleSlug: $titleSlug) {
                        questionId
                    }
                }
            """,
            "variables": {"titleSlug": problem_slug},
        }
        try:
            response = self.session.post(endpoint, json=query, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            question_id = data.get("data", {}).get("question", {}).get("questionId")
            if not question_id:
                raise ValueError(f"Invalid problem slug '{problem_slug}'.")
            return int(question_id)
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get question ID: {str(e)}")

    def submit(self, problem_slug: str, code: str, language: str = "python3") -> dict:
        """Submit a solution to a LeetCode problem."""
        question_id = self._get_question_id(problem_slug)
        endpoint = f"{self.base_url}/problems/{problem_slug}/submit/"
        payload = {"question_id": question_id, "lang": language, "typed_code": code}
        try:
            response = self.session.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to submit solution: {str(e)}")
