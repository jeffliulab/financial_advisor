"""
Test script for Budget Planner Update API
Tests the new update_budget_item functionality
"""

import sys
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "brain" / "tools"))

from budget_planner import (
    add_budget_item,
    update_budget_item,
    get_user_budget_info,
    delete_budget_item
)


def test_update_functionality():
    """Test the update functionality"""
    username = "test_update_user"
    
    print("=" * 60)
    print("Testing Budget Planner Update Functionality")
    print("=" * 60)
    
    # Step 1: Add a test item
    print("\n1. Adding a test item...")
    item_data = {
        "name": "Test Salary",
        "scope": "永久",
        "time_type": "月度",
        "category": "收入",
        "amount": 5000.0
    }
    
    result = add_budget_item(username, item_data)
    print(f"   Result: {result['success']}")
    print(f"   Message: {result['message']}")
    
    if not result['success']:
        print("   ❌ Failed to add item")
        return
    
    item_id = result['item_id']
    print(f"   ✅ Item added with ID: {item_id}")
    
    # Step 2: Update the item
    print("\n2. Updating the item...")
    updates = {
        "name": "Updated Salary",
        "amount": 6000.0,
        "scope": "2025年"
    }
    
    result = update_budget_item(username, item_id, updates)
    print(f"   Result: {result['success']}")
    print(f"   Message: {result['message']}")
    
    if not result['success']:
        print("   ❌ Failed to update item")
        return
    
    print(f"   ✅ Item updated successfully")
    print(f"   Updated item: {result['item']}")
    
    # Step 3: Verify the update
    print("\n3. Verifying the update...")
    budget_info = get_user_budget_info(username)
    
    updated_item = None
    for item in budget_info['items']:
        if item['id'] == item_id:
            updated_item = item
            break
    
    if updated_item:
        print(f"   ✅ Item found in budget")
        print(f"   Name: {updated_item['name']}")
        print(f"   Amount: {updated_item['amount']}")
        print(f"   Scope: {updated_item['scope']}")
        
        # Verify changes
        assert updated_item['name'] == "Updated Salary", "Name not updated"
        assert updated_item['amount'] == 6000.0, "Amount not updated"
        assert updated_item['scope'] == "2025年", "Scope not updated"
        print(f"   ✅ All updates verified correctly")
    else:
        print(f"   ❌ Updated item not found in budget")
    
    # Step 4: Test partial update
    print("\n4. Testing partial update (only amount)...")
    partial_updates = {
        "amount": 7000.0
    }
    
    result = update_budget_item(username, item_id, partial_updates)
    print(f"   Result: {result['success']}")
    print(f"   Message: {result['message']}")
    
    if result['success']:
        print(f"   ✅ Partial update successful")
        print(f"   Updated amount: {result['item']['amount']}")
    else:
        print(f"   ❌ Partial update failed")
    
    # Step 5: Test invalid update
    print("\n5. Testing invalid update (negative amount)...")
    invalid_updates = {
        "amount": -100.0
    }
    
    result = update_budget_item(username, item_id, invalid_updates)
    print(f"   Result: {result['success']}")
    print(f"   Message: {result['message']}")
    
    if not result['success']:
        print(f"   ✅ Invalid update correctly rejected")
    else:
        print(f"   ❌ Invalid update should have been rejected")
    
    # Step 6: Test non-existent item update
    print("\n6. Testing update of non-existent item...")
    result = update_budget_item(username, "non_existent_id", {"amount": 100.0})
    print(f"   Result: {result['success']}")
    print(f"   Message: {result['message']}")
    
    if not result['success']:
        print(f"   ✅ Non-existent item update correctly rejected")
    else:
        print(f"   ❌ Should have failed for non-existent item")
    
    # Cleanup: Delete the test item
    print("\n7. Cleaning up...")
    result = delete_budget_item(username, item_id)
    print(f"   Result: {result['success']}")
    print(f"   Message: {result['message']}")
    
    if result['success']:
        print(f"   ✅ Test item deleted successfully")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    test_update_functionality()

