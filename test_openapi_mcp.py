"""
Test script for the new OpenAPI MCP tools
Tests the in-memory caching functionality without requiring database
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.mcp.server_redesign import APIDocumentationMCPServer


async def test_openapi_tools():
    """Test the new OpenAPI MCP tools"""

    print("=" * 60)
    print("Testing OpenAPI MCP Tools")
    print("=" * 60)

    server = APIDocumentationMCPServer()

    # Test 1: Load OpenAPI spec
    print("\n[Test 1] Loading OpenAPI spec from Kubernetes...")
    k8s_url = "https://raw.githubusercontent.com/kubernetes/kubernetes/release-1.28/api/openapi-spec/swagger.json"

    result = await server.load_openapi(
        provider="kubernetes-test",
        url=k8s_url
    )

    print(f"Status: {result['status']}")
    if result['status'] == 'success':
        print(f"✓ Loaded {result['total_endpoints']} endpoints")
        print(f"  Sample endpoints:")
        for ep in result.get('sample_endpoints', [])[:3]:
            print(f"    - {ep['method']} {ep['path']}")
    else:
        print(f"✗ Error: {result.get('error')}")
        return False

    # Test 2: Search loaded OpenAPI
    print("\n[Test 2] Searching for 'pods' in loaded OpenAPI...")

    search_result = await server.search_openapi(
        provider="kubernetes-test",
        query="pods",
        limit=5
    )

    print(f"Status: {search_result['status']}")
    if search_result['status'] == 'success':
        print(f"✓ Found {search_result['total_found']} matching endpoints")
        print(f"  Showing top {search_result['showing']} results:")
        for result in search_result.get('results', []):
            print(f"    - {result['method']} {result['path']}")
            print(f"      {result['title']}")
            print(f"      Relevance: {result['relevance_score']}")
    else:
        print(f"✗ Error: {search_result.get('error')}")
        return False

    # Test 3: Get endpoint details
    print("\n[Test 3] Getting details for first endpoint...")

    if search_result.get('results'):
        first_endpoint = search_result['results'][0]
        details_result = await server.get_openapi_endpoint_details(
            provider="kubernetes-test",
            id=first_endpoint['id']
        )

        print(f"Status: {details_result['status']}")
        if details_result['status'] == 'success':
            endpoint = details_result['endpoint']
            print(f"✓ Retrieved details for: {endpoint['method']} {endpoint['path']}")
            print(f"  Title: {endpoint['title']}")
            print(f"  Description: {endpoint['description'][:100] if endpoint['description'] else 'N/A'}...")
            print(f"  Parameters: {len(endpoint['parameters']) if endpoint['parameters'] else 0}")
            print(f"  Tags: {', '.join(endpoint['tags']) if endpoint['tags'] else 'None'}")
        else:
            print(f"✗ Error: {details_result.get('error')}")
            return False

    # Test 4: List providers (should show cached provider)
    print("\n[Test 4] Listing all providers...")

    providers_result = await server.list_providers()

    print(f"Total providers: {providers_result['total_providers']}")
    for provider in providers_result['providers']:
        print(f"  - {provider['name']} ({provider['source']})")
        print(f"    Endpoints: {provider['endpoint_count']}")
        if provider['source'] == 'in-memory cache':
            print(f"    OpenAPI URL: {provider.get('openapi_url', 'N/A')}")

    # Test 5: Search non-existent provider (error handling)
    print("\n[Test 5] Testing error handling (non-existent provider)...")

    error_result = await server.search_openapi(
        provider="non-existent",
        query="test"
    )

    print(f"Status: {error_result['status']}")
    if error_result['status'] == 'error':
        print(f"✓ Error handled correctly: {error_result['error']}")
        print(f"  Suggestion: {error_result.get('suggestion')}")
    else:
        print(f"✗ Expected error but got success")
        return False

    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)

    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_openapi_tools())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
