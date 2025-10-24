"""
Quick test script to verify budget planner API endpoints
"""

import sys
import io
from pathlib import Path

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "brain" / "tools"))

from budget_planner import (
    add_budget_item,
    get_items_by_month,
    calculate_dashboard
)

print("=" * 60)
print("Budget Planner API Test")
print("=" * 60)

# Test 1: Add a test item
print("\n[Test 1] Adding a test item...")
test_item = {
    "name": "Test Salary",
    "scope": "Permanent",
    "time_type": "Monthly",
    "category": "Income",
    "amount": 5000
}

try:
    result = add_budget_item("admin", test_item)
    print(f"Success: {result.get('success', False)}")
    print(f"Message: {result.get('message', 'N/A')}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: Get items
print("\n[Test 2] Getting items for year 2025...")
try:
    items = get_items_by_month("admin", 2025, None)
    print(f"Income items: {len(items['income_items'])}")
    print(f"Expense items: {len(items['expense_items'])}")
    if items['income_items']:
        sample = items['income_items'][0]
        print(f"Sample item: {sample['name']} - ${sample['amount']}")
except Exception as e:
    print(f"Error: {e}")

# Test 3: Calculate dashboard
print("\n[Test 3] Calculating dashboard for 2025...")
try:
    dashboard = calculate_dashboard("admin", 2025)
    print(f"Total Income: ${dashboard['total_income']:.2f}")
    print(f"Total Expense: ${dashboard['total_expense']:.2f}")
    print(f"Total Surplus: ${dashboard['total_surplus']:.2f}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("Test completed!")
print("=" * 60)
