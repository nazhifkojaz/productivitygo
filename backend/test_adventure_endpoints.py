#!/usr/bin/env python3
"""
Test Script for Adventure Mode Endpoints

Tests all adventure endpoints in sequence. Requires a valid JWT token.

Usage:
    export TEST_TOKEN="your-jwt-token"
    python test_adventure_endpoints.py

Or:
    python test_adventure_endpoints.py your-jwt-token

Requirements:
    pip install requests python-dotenv
"""

import os
import sys
import requests
from datetime import date
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
TOKEN = os.getenv("TEST_TOKEN") or (sys.argv[1] if len(sys.argv) > 1 else None)

if not TOKEN:
    print("Error: No JWT token provided")
    print("Usage: export TEST_TOKEN=\"your-jwt-token\" && python test_adventure_endpoints.py")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Track state during tests
state = {
    "adventure_id": None,
    "monster_id": None,
    "refreshes_remaining": 0
}


def print_section(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_result(test_name, success, detail=None):
    status = "✓ PASS" if success else "✗ FAIL"
    print(f"  {status}: {test_name}")
    if detail:
        print(f"    → {detail}")


def test_get_monster_pool():
    """Test GET /adventures/monsters"""
    print_section("Test 1: Get Monster Pool")

    response = requests.get(f"{BASE_URL}/api/adventures/monsters", headers=HEADERS)

    if response.status_code == 200:
        data = response.json()
        monsters = data.get("monsters", [])
        state["refreshes_remaining"] = data.get("refreshes_remaining", 0)

        has_monsters = len(monsters) == 4
        has_refreshes = state["refreshes_remaining"] == 3
        has_tiers = "unlocked_tiers" in data
        has_rating = "current_rating" in data

        if has_monsters:
            # Save first monster ID for later tests
            state["monster_id"] = monsters[0]["id"]
            print(f"  Sample monster: {monsters[0]['emoji']} {monsters[0]['name']} ({monsters[0]['tier']})")

        print_result("Returns 4 monsters", has_monsters, f"Got {len(monsters)}")
        print_result("Refreshes = 3", has_refreshes, f"Got {state['refreshes_remaining']}")
        print_result("Has unlocked_tiers", has_tiers, f"Got {data.get('unlocked_tiers')}")
        print_result("Has current_rating", has_rating, f"Got {data.get('current_rating')}")

        return has_monsters and has_refreshes
    else:
        print_result("Request succeeded", False, f"Status {response.status_code}: {response.text}")
        return False


def test_refresh_monster_pool():
    """Test POST /adventures/monsters/refresh"""
    print_section("Test 2: Refresh Monster Pool")

    # First refresh
    response = requests.post(f"{BASE_URL}/api/adventures/monsters/refresh", headers=HEADERS)

    if response.status_code == 200:
        data = response.json()
        monsters = data.get("monsters", [])
        remaining = data.get("refreshes_remaining", 0)

        has_monsters = len(monsters) == 4
        decremented = remaining == 2

        print_result("Returns 4 monsters", has_monsters, f"Got {len(monsters)}")
        print_result("Refreshes decremented to 2", decremented, f"Got {remaining}")

        # Second refresh
        response2 = requests.post(f"{BASE_URL}/api/adventures/monsters/refresh", headers=HEADERS)
        if response2.status_code == 200:
            data2 = response2.json()
            remaining2 = data2.get("refreshes_remaining", 0)
            decremented2 = remaining2 == 1
            print_result("Second refresh decrements to 1", decremented2, f"Got {remaining2}")
            state["refreshes_remaining"] = remaining2
            return has_monsters and decremented and decremented2
        return has_monsters and decremented
    else:
        print_result("Request succeeded", False, f"Status {response.status_code}: {response.text}")
        return False


def test_start_adventure():
    """Test POST /adventures/start"""
    print_section("Test 3: Start Adventure")

    if not state.get("monster_id"):
        print_result("Start adventure", False, "No monster_id available from previous tests")
        return False

    payload = {"monster_id": state["monster_id"]}
    response = requests.post(
        f"{BASE_URL}/api/adventures/start",
        headers=HEADERS,
        json=payload
    )

    if response.status_code == 200:
        data = response.json()
        state["adventure_id"] = data.get("id")

        has_id = bool(state["adventure_id"])
        has_status = data.get("status") == "active"
        has_monster = data.get("monster") is not None
        has_hp = "monster_current_hp" in data and "monster_max_hp" in data
        hp_match = data.get("monster_current_hp") == data.get("monster_max_hp") if has_hp else False

        print_result("Adventure created with ID", has_id, f"ID: {state['adventure_id']}")
        print_result("Status is 'active'", has_status, f"Got {data.get('status')}")
        print_result("Has monster data", has_monster)
        print_result("HP initialized correctly", hp_match,
                    f"{data.get('monster_current_hp')}/{data.get('monster_max_hp')}")

        return has_id and has_status and has_monster
    else:
        print_result("Request succeeded", False, f"Status {response.status_code}: {response.text}")
        return False


def test_get_current_adventure():
    """Test GET /adventures/current"""
    print_section("Test 4: Get Current Adventure")

    response = requests.get(f"{BASE_URL}/api/adventures/current", headers=HEADERS)

    if response.status_code == 200:
        data = response.json()
        state["adventure_id"] = data.get("id")

        has_id = bool(state["adventure_id"])
        has_status = data.get("status") == "active"
        has_app_state = "app_state" in data
        has_days_remaining = "days_remaining" in data
        has_monster = data.get("monster") is not None

        # Check app_state is valid
        valid_states = ["PRE_ADVENTURE", "ACTIVE", "LAST_DAY", "ON_BREAK", "DEADLINE_PASSED"]
        valid_app_state = data.get("app_state") in valid_states

        print_result("Returns adventure ID", has_id, f"ID: {state['adventure_id']}")
        print_result("Status is 'active'", has_status)
        print_result("Has valid app_state", valid_app_state, f"Got {data.get('app_state')}")
        print_result("Has days_remaining", has_days_remaining, f"Got {data.get('days_remaining')} days")
        print_result("Has monster data", has_monster)

        return has_id and has_status and valid_app_state
    else:
        print_result("Request succeeded", False, f"Status {response.status_code}: {response.text}")
        return False


def test_get_adventure_details():
    """Test GET /adventures/{id}"""
    print_section("Test 5: Get Adventure Details")

    if not state.get("adventure_id"):
        print_result("Get adventure details", False, "No adventure_id available")
        return False

    response = requests.get(
        f"{BASE_URL}/api/adventures/{state['adventure_id']}",
        headers=HEADERS
    )

    if response.status_code == 200:
        data = response.json()

        has_id = data.get("id") == state["adventure_id"]
        has_monster = data.get("monster") is not None
        has_daily_breakdown = "daily_breakdown" in data
        breakdown_is_list = isinstance(data.get("daily_breakdown"), list)

        print_result("Returns correct adventure", has_id)
        print_result("Has monster data", has_monster)
        print_result("Has daily_breakdown", has_daily_breakdown)
        print_result("daily_breakdown is list", breakdown_is_list,
                    f"{len(data.get('daily_breakdown', []))} entries")

        return has_id and has_monster and breakdown_is_list
    else:
        print_result("Request succeeded", False, f"Status {response.status_code}: {response.text}")
        return False


def test_schedule_break():
    """Test POST /adventures/{id}/break"""
    print_section("Test 6: Schedule Break Day")

    if not state.get("adventure_id"):
        print_result("Schedule break", False, "No adventure_id available")
        return False

    response = requests.post(
        f"{BASE_URL}/api/adventures/{state['adventure_id']}/break",
        headers=HEADERS
    )

    if response.status_code == 200:
        data = response.json()

        status_ok = data.get("status") == "break_scheduled"
        has_break_date = "break_date" in data
        has_new_deadline = "new_deadline" in data
        has_breaks_remaining = "breaks_remaining" in data
        breaks_count = data.get("breaks_remaining", -1) == 1  # Used 1 of 2

        print_result("Status is 'break_scheduled'", status_ok)
        print_result("Has break_date", has_break_date, f"Got {data.get('break_date')}")
        print_result("Has new_deadline", has_new_deadline, f"Got {data.get('new_deadline')}")
        print_result("Breaks remaining = 1", breaks_count, f"Got {data.get('breaks_remaining')}")

        # Try to schedule another break (should work, we have 2 total)
        response2 = requests.post(
            f"{BASE_URL}/api/adventures/{state['adventure_id']}/break",
            headers=HEADERS
        )
        if response2.status_code == 200:
            data2 = response2.json()
            breaks_remaining2 = data2.get("breaks_remaining", -1)
            second_break_ok = breaks_remaining2 == 0
            print_result("Second break succeeds", second_break_ok, f"Remaining: {breaks_remaining2}")

            # Try a third time (should fail)
            response3 = requests.post(
                f"{BASE_URL}/api/adventures/{state['adventure_id']}/break",
                headers=HEADERS
            )
            third_fails = response3.status_code == 400
            print_result("Third break fails (no breaks left)", third_fails,
                        f"Status {response3.status_code}")

            return status_ok and second_break_ok and third_fails
        return status_ok
    else:
        print_result("Request succeeded", False, f"Status {response.status_code}: {response.text}")
        return False


def test_abandon_adventure():
    """Test POST /adventures/{id}/abandon"""
    print_section("Test 7: Abandon Adventure (50% XP)")

    if not state.get("adventure_id"):
        print_result("Abandon adventure", False, "No adventure_id available")
        return False

    response = requests.post(
        f"{BASE_URL}/api/adventures/{state['adventure_id']}/abandon",
        headers=HEADERS
    )

    if response.status_code == 200:
        data = response.json()

        status_ok = data.get("status") == "escaped"
        has_xp = "xp_earned" in data
        xp_is_int = isinstance(data.get("xp_earned"), int)
        xp_non_negative = (data.get("xp_earned") or 0) >= 0

        print_result("Status is 'escaped'", status_ok)
        print_result("Has xp_earned", has_xp, f"Got {data.get('xp_earned')} XP")
        print_result("XP is valid integer", xp_is_int and xp_non_negative)

        return status_ok and has_xp and xp_is_int
    else:
        print_result("Request succeeded", False, f"Status {response.status_code}: {response.text}")
        return False


def test_no_active_adventure():
    """Test that GET /current returns 404 after abandoning"""
    print_section("Test 8: No Active Adventure After Abandon")

    response = requests.get(f"{BASE_URL}/api/adventures/current", headers=HEADERS)

    if response.status_code == 404:
        print_result("Returns 404 (no active adventure)", True)
        return True
    else:
        print_result("Returns 404", False, f"Status {response.status_code}: {response.text}")
        return False


def test_monster_pool_after_adventure():
    """Test that refresh count resets after adventure ends"""
    print_section("Test 9: Monster Pool Resets After Adventure")

    response = requests.get(f"{BASE_URL}/api/adventures/monsters", headers=HEADERS)

    if response.status_code == 200:
        data = response.json()
        remaining = data.get("refreshes_remaining", 0)

        reset_ok = remaining == 3
        print_result("Refresh count reset to 3", reset_ok, f"Got {remaining}")

        return reset_ok
    else:
        print_result("Request succeeded", False, f"Status {response.status_code}: {response.text}")
        return False


def test_error_cases():
    """Test error handling"""
    print_section("Test 10: Error Cases")

    results = []

    # Test starting adventure without monster_id
    response = requests.post(
        f"{BASE_URL}/api/adventures/start",
        headers=HEADERS,
        json={}
    )
    results.append(("Start without monster_id fails", response.status_code == 400))

    # Test starting adventure with invalid monster_id
    response = requests.post(
        f"{BASE_URL}/api/adventures/start",
        headers=HEADERS,
        json={"monster_id": "00000000-0000-0000-0000-000000000000"}
    )
    results.append(("Start with invalid monster_id fails", response.status_code == 404))

    # Test getting non-existent adventure
    response = requests.get(
        f"{BASE_URL}/api/adventures/00000000-0000-0000-0000-000000000000",
        headers=HEADERS
    )
    results.append(("Get non-existent adventure fails", response.status_code == 404))

    for name, passed in results:
        print_result(name, passed)

    return all(r[1] for r in results)


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("  ADVENTURE MODE ENDPOINT TESTS")
    print("=" * 60)
    print(f"  Base URL: {BASE_URL}")
    print(f"  Token: {TOKEN[:20]}..." if len(TOKEN) > 20 else f"  Token: {TOKEN}")
    print("=" * 60)

    tests = [
        ("Get Monster Pool", test_get_monster_pool),
        ("Refresh Monster Pool", test_refresh_monster_pool),
        ("Start Adventure", test_start_adventure),
        ("Get Current Adventure", test_get_current_adventure),
        ("Get Adventure Details", test_get_adventure_details),
        ("Schedule Break", test_schedule_break),
        ("Abandon Adventure", test_abandon_adventure),
        ("No Active Adventure", test_no_active_adventure),
        ("Pool Resets After Adventure", test_monster_pool_after_adventure),
        ("Error Cases", test_error_cases),
    ]

    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print_result(f"{name} - Exception", False, str(e))
            results[name] = False

    # Summary
    print_section("SUMMARY")
    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✓" if result else "✗"
        print(f"  {status} {name}")

    print("\n" + "-" * 40)
    print(f"  Results: {passed}/{total} tests passed")
    print("-" * 40)

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
