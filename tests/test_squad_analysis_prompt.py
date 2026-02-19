import os
import re
import sys


def test_via_exec():
    """Test the prompt content by executing the file content directly, bypassing imports."""
    file_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../src/prompts/squad_analysis.py")
    )

    with open(file_path) as f:
        content = f.read()

    # Remove the relative import that causes issues in isolation
    content = re.sub(r"from \.\.tools import mcp", "", content)
    # Remove the decorator
    content = re.sub(r"@mcp\.prompt\(\)", "", content)

    # Execute in isolated scope
    local_env = {}
    try:
        exec(content, {}, local_env)
    except Exception as e:
        print(f"Failed to exec file: {e}")
        sys.exit(1)

    if "analyze_squad_performance" not in local_env:
        print("Function analyze_squad_performance not found in executed code")
        sys.exit(1)

    analyze_func = local_env["analyze_squad_performance"]

    # Test generation
    team_id = 999999
    prompt = analyze_func(team_id=team_id, num_gameweeks=5)

    print("Prompt Preview:")
    print("-" * 20)
    print(prompt[:300] + "...")
    print("-" * 20)

    # Assertions
    checks = [
        f"team ID {team_id}",
        "PRO-LEVEL transfer strategy",
        "Strategic Context",
        "Financial Health",
        "Chip Status",
        "fpl_get_manager_chips",
        "fpl_find_fixture_opportunities",
        "Scenario A: The Surgery",
        "Scenario B: The Luxury Move",
        "xGI Regression Model",
    ]

    failed = []
    for check in checks:
        if check not in prompt:
            failed.append(check)

    if failed:
        print(f"❌ Verification Failed. Missing phrases: {failed}")
        sys.exit(1)
    else:
        print("✅ Verification Passed! All Pro features present.")


if __name__ == "__main__":
    test_via_exec()
