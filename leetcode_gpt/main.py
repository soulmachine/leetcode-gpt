import os
import sys
import argparse
from typing import List
from leetcode_gpt.claude import translate_java_to_other_language
import glob
from pathlib import Path
from leetcode_gpt.leetcode import LeetCode

# Check required environment variables
required_env_vars = [
    'LEETCODE_CSRF_TOKEN',
    'LEETCODE_SESSION_ID',
    'ANTHROPIC_API_KEY'
]

missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

def add_code_to_file(file_path: str, target_language: str) -> None:
    target_language = target_language.lower()

    """Add translated code to markdown file for each Java code block."""
    with open(file_path, 'r', encoding='utf-8') as file:
        sections = file.read().split('<Tabs')

    problem_slug = Path(file_path).stem
    modified = False
    for i, section in enumerate(sections[1:], 1):  # Skip content before first Tabs
        # Skip if no proper Tabs structure
        if '</Tabs>' not in section:
            raise ValueError(f"No proper Tabs closure found in section {i}")

        # Skip if target language tab already exists
        if f'<TabItem value="{target_language}">' in section or f'<TabItem value="{target_language.upper()}">' in section or f'<TabItem value="{target_language.capitalize()}">' in section:
            sections[i] = f'<Tabs{section}' # Keep the original section
            continue

        tab_content, remainder = section.split('</Tabs>', 1)

        # Abort if no Java code
        if '<TabItem value="java">' not in tab_content:
            raise ValueError(f"No Java code found in section {i}")

        # Extract and translate Java code
        try:
            java_code = tab_content.split('```java')[1].split('```')[0].strip()
            translated_code = translate_java_to_other_language(java_code, target_language)
            validate_translated_code(translated_code, target_language, problem_slug)

            # Add new tab at the end of tab_content
            new_tab = f'\n<TabItem value="{target_language}">\n\n```{target_language}\n{translated_code}\n```\n\n</TabItem>\n'
            sections[i] = f'<Tabs{tab_content}{new_tab}</Tabs>{remainder}'
            modified = True
        except Exception as e:
            print(f"Error processing Tabs section {i}: {str(e)}")
            continue

    # check if defaultValue="python"
    if target_language == "python" and 'defaultValue="python"' not in sections[1]:
        modified = True
        sections[1] = sections[1].replace(f'defaultValue="java"', 'defaultValue="python"')
        sections[1] = sections[1].replace(f'defaultValue="cpp"', 'defaultValue="python"')

    if modified:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(''.join(sections))

def process_directory(directory: str, target_language: str) -> None:
    """Recursively process all markdown files in directory and its subdirectories."""
    pattern = str(Path(directory) / "**" / "*.md")
    for file_path in glob.glob(pattern, recursive=True):
        try:
            print(f"Processing {file_path}")
            add_code_to_file(file_path, target_language)
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")

def validate_translated_code(translated_code: str, language: str, problem_slug: str = None) -> bool:
    """Validate translated code by submitting it to LeetCode.

    Args:
        leetcode_client: LeetCode client
        translated_code: The code to validate
        language: Programming language of the code
        problem_slug: LeetCode problem slug (e.g., 'two-sum')

    Returns:
        bool: True if code passes all test cases, False otherwise
    """
    try:
        if language == "python":
            language = "python3"

        leetcode_client = LeetCode(
            csrf_token=os.getenv("LEETCODE_CSRF_TOKEN"),
            session_id=os.getenv("LEETCODE_SESSION_ID")
        )

        # Submit code to LeetCode
        submission_id = leetcode_client.submit(problem_slug, translated_code, language)
        response = leetcode_client.check_submission(submission_id)

        # Check submission status
        if response.get('state') == 'SUCCESS':
            print(f"✅ Code validation passed")
            return True
        else:
            error_msg = response.get('error_msg', 'Unknown error')
            print(f"❌ Code validation failed: {error_msg}")
            return False

    except Exception as e:
        print(f"❌ Validation error: {str(e)}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate code for a leetcode problem.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-d', '--dir', required=False, type=str, help='Input directory')
    group.add_argument('-f', '--file', required=False, type=str, help='Input file')
    parser.add_argument('-l', '--language', required=True, type=str, help='Language to translate to')
    args, unknown = parser.parse_known_args() # parser.parse_args()

    if args.dir:
        process_directory(args.dir, args.language)
    else:
        add_code_to_file(args.file, args.language)
