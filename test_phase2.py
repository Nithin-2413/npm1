#!/usr/bin/env python3
"""
Phase 2 Testing Script
Tests all LLM orchestration components
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, '/app/backend')

async def test_intent_parser():
    """Test intent parsing"""
    print("\n" + "="*60)
    print("TEST 1: Intent Parser")
    print("="*60)
    
    try:
        from core.llm.intent_parser import intent_parser
        from core.flow_registry import flow_registry
        
        # Load flows
        flow_registry.load_all_flows()
        flows = flow_registry.list_flows()
        
        # Test cases
        test_cases = [
            "Create an order for Dallas Office with 3 phone numbers",
            "Login to the system",
            "Cancel order 12345 because testing is done",
            "Create an order"  # Should trigger clarification
        ]
        
        for i, test_input in enumerate(test_cases, 1):
            print(f"\nTest Case {i}: \"{test_input}\"")
            print("-" * 60)
            
            result = await intent_parser.parse(test_input, flows)
            
            print(f"Flow ID: {result.get('flow_id')}")
            print(f"Confidence: {result.get('confidence')}")
            print(f"Extracted Variables: {result.get('extracted_variables')}")
            print(f"Missing Required: {result.get('missing_required')}")
            print(f"Clarification: {result.get('clarification_needed')}")
        
        print("\n✅ Intent Parser tests passed!")
        return True
    
    except Exception as e:
        print(f"\n❌ Intent Parser tests failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_flow_selector():
    """Test flow selector with semantic search"""
    print("\n" + "="*60)
    print("TEST 2: Flow Selector (Semantic Search)")
    print("="*60)
    
    try:
        from core.llm.flow_selector import flow_selector
        from core.flow_registry import flow_registry
        
        # Load and embed flows
        flow_registry.load_all_flows()
        flows = flow_registry.list_flows()
        
        print(f"\nEmbedding {len(flows)} flows into ChromaDB...")
        flow_selector.embed_flows(flows)
        print("✅ Flows embedded successfully")
        
        # Test cases
        test_queries = [
            "I need to cancel an existing order",
            "Create a new phone number order",
            "Log into the application"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\nQuery {i}: \"{query}\"")
            print("-" * 60)
            
            result = await flow_selector.select_flow(query, flows)
            
            print(f"Selected Flow: {result.get('flow_id')}")
            print(f"Confidence: {result.get('confidence'):.2f}")
            print(f"Reasoning: {result.get('reasoning')}")
            print(f"Top Matches:")
            for match in result.get('top_matches', [])[:3]:
                print(f"  - {match['flow_id']}: {match['name']} (similarity: {match['similarity']:.2f})")
        
        print("\n✅ Flow Selector tests passed!")
        return True
    
    except Exception as e:
        print(f"\n❌ Flow Selector tests failed: {e}")
        print("Note: This may fail if ChromaDB is not running. Start with: docker run -d -p 8000:8000 chromadb/chroma")
        import traceback
        traceback.print_exc()
        return False

def test_variable_resolver():
    """Test variable resolution and merging"""
    print("\n" + "="*60)
    print("TEST 3: Variable Resolver")
    print("="*60)
    
    try:
        from core.llm.variable_resolver import variable_resolver
        from core.flow_registry import flow_registry
        
        # Load flows
        flow_registry.load_all_flows()
        flow = flow_registry.get_flow('create_order_single_tn')
        
        # Test case 1: All sources
        print("\nTest Case 1: Priority Merging")
        print("-" * 60)
        
        form_overrides = {"quantity": 5}
        llm_extracted = {"service_location": "Dallas Office", "quantity": 3}
        
        result = variable_resolver.resolve(
            flow=flow,
            form_overrides=form_overrides,
            llm_extracted=llm_extracted
        )
        
        print(f"Form overrides: {form_overrides}")
        print(f"LLM extracted: {llm_extracted}")
        print(f"Flow defaults: {flow.get('defaults')}")
        print(f"\nResolved: {result['resolved']}")
        print(f"Missing Required: {result['missing_required']}")
        print(f"Auto-generated: {result['auto_generated']}")
        
        # Verify priority: form should override LLM
        assert result['resolved']['quantity'] == 5, "Form override should win"
        assert result['resolved']['service_location'] == "Dallas Office", "LLM extracted should be used"
        
        # Test case 2: Auto-generation
        print("\n\nTest Case 2: Auto-generation")
        print("-" * 60)
        
        # Mock flow with auto-gen fields
        mock_flow = {
            'required_params': ['user_name', 'mac_address'],
            'defaults': {}
        }
        
        result = variable_resolver.resolve(
            flow=mock_flow,
            form_overrides={},
            llm_extracted={}
        )
        
        print(f"Auto-generated user_name: {result['auto_generated'].get('user_name')}")
        print(f"Auto-generated mac_address: {result['auto_generated'].get('mac_address')}")
        
        print("\n✅ Variable Resolver tests passed!")
        return True
    
    except Exception as e:
        print(f"\n❌ Variable Resolver tests failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_step_builder():
    """Test step building from templates"""
    print("\n" + "="*60)
    print("TEST 4: Step Builder")
    print("="*60)
    
    try:
        from core.llm.step_builder import step_builder
        from core.flow_registry import flow_registry
        
        # Load flows
        flow_registry.load_all_flows()
        flow = flow_registry.get_flow('create_order_single_tn')
        
        # Resolved variables
        resolved_vars = {
            'service_location': 'Dallas Office',
            'quantity': 3,
            'order_type': 'Add New Phone Numbers',
            'user_type': 'existing'
        }
        
        print(f"\nTemplate Steps: {len(flow['steps'])}")
        print(f"Resolved Variables: {resolved_vars}")
        print("-" * 60)
        
        # Build concrete steps
        concrete_steps = step_builder.build_steps(flow, resolved_vars)
        
        print(f"Concrete Steps Built: {len(concrete_steps)}")
        
        # Show a few examples
        print("\nExample Steps:")
        for step in concrete_steps[:3]:
            print(f"\nStep {step['step']}: {step['description']}")
            print(f"  Action: {step['action']}")
            if 'value' in step:
                print(f"  Value: {step.get('value')}")
            if 'select_value' in step:
                print(f"  Select Value: {step.get('select_value')}")
        
        # Verify variable substitution worked
        assert '{{' not in str(concrete_steps), "All variables should be substituted"
        
        print("\n✅ Step Builder tests passed!")
        return True
    
    except Exception as e:
        print(f"\n❌ Step Builder tests failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("🧪 Phase 2 Component Testing")
    print("="*60)
    
    # Check GROQ_API_KEY
    groq_key = os.getenv('GROQ_API_KEY')
    if not groq_key or groq_key == 'your-groq-api-key-here':
        print("⚠️  WARNING: GROQ_API_KEY not configured!")
        print("   Some tests will fail. Set it in /app/backend/.env")
        print("   Continuing with other tests...\n")
    
    results = []
    
    # Run tests
    results.append(('Intent Parser', await test_intent_parser()))
    results.append(('Flow Selector', await test_flow_selector()))
    results.append(('Variable Resolver', test_variable_resolver()))
    results.append(('Step Builder', test_step_builder()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:.<40} {status}")
    
    total = len(results)
    passed_count = sum(1 for _, passed in results if passed)
    
    print(f"\nTotal: {passed_count}/{total} tests passed")
    
    if passed_count == total:
        print("\n🎉 All Phase 2 tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed_count} test(s) failed")
        return 1

if __name__ == "__main__":
    # Change to backend directory
    os.chdir('/app/backend')
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
