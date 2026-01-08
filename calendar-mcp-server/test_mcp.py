#!/usr/bin/env python3
"""Test script for MCP Calendar Server."""

import json
import requests

BASE_URL = "http://localhost:3000"


def test_mcp_tool(tool_name: str, arguments: dict) -> dict:
    """Test an MCP tool."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments,
        },
    }
    response = requests.post(f"{BASE_URL}/mcp", json=payload)
    response.raise_for_status()
    return response.json()


def main():
    """Run tests."""
    print("Testing MCP Calendar Server...")
    print("=" * 60)

    # Test 1: Create booking
    print("\n1. Creating booking...")
    result = test_mcp_tool(
        "create_booking",
        {
            "customer_id": "customer-123",
            "customer_name": "Juan Pérez",
            "date_iso": "2025-01-08",
            "start_time_iso": "2025-01-08T18:00:00Z",
            "end_time_iso": "2025-01-08T19:00:00Z",
        },
    )
    booking_id = result["result"]["booking"]["booking_id"]
    print(f"✓ Booking created: {booking_id}")
    print(json.dumps(result, indent=2))

    # Test 2: Get booking
    print("\n2. Getting booking...")
    result = test_mcp_tool("get_booking", {"booking_id": booking_id})
    print(f"✓ Booking retrieved")
    print(json.dumps(result, indent=2))

    # Test 3: List bookings
    print("\n3. Listing bookings...")
    result = test_mcp_tool("list_bookings", {"customer_id": "customer-123"})
    print(f"✓ Found {len(result['result']['bookings'])} bookings")
    print(json.dumps(result, indent=2))

    # Test 4: Check availability
    print("\n4. Checking availability...")
    result = test_mcp_tool(
        "check_availability",
        {
            "date_iso": "2025-01-08",
            "start_time_iso": "2025-01-08T18:00:00Z",
            "end_time_iso": "2025-01-08T19:00:00Z",
        },
    )
    print(f"✓ Available: {result['result']['available']}")
    print(json.dumps(result, indent=2))

    # Test 5: Get available slots
    print("\n5. Getting available slots...")
    result = test_mcp_tool("get_available_slots", {"date_iso": "2025-01-08"})
    print(f"✓ Found {len(result['result']['slots'])} available slots")
    print(json.dumps(result, indent=2))

    # Test 6: Update booking
    print("\n6. Updating booking...")
    result = test_mcp_tool(
        "update_booking",
        {
            "booking_id": booking_id,
            "status": "cancelled",
        },
    )
    print(f"✓ Booking updated")
    print(json.dumps(result, indent=2))

    # Test 7: Delete booking
    print("\n7. Deleting booking...")
    result = test_mcp_tool("delete_booking", {"booking_id": booking_id})
    print(f"✓ Booking deleted: {result['result']['success']}")
    print(json.dumps(result, indent=2))

    print("\n" + "=" * 60)
    print("All tests completed!")


if __name__ == "__main__":
    main()

