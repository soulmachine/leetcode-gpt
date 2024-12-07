import os
from leetcode_gpt.claude import generate_code

# Check required environment variables
required_env_vars = [
    'LEETCODE_CSRF_TOKEN',
    'LEETCODE_SESSION_ID',
    'ANTHROPIC_API_KEY'
]

missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

if __name__ == "__main__":
    msg = generate_code("Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.")
    print(msg)
