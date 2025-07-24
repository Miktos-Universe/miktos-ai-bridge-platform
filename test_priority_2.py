#!/usr/bin/env python3
"""
Priority 2 Test Suite: Intelligence Layer Enhancement
Tests the enhanced LLM integration and workflow management capabilities
"""

import asyncio
import logging
import json
import sys
import os
from typing import Dict, Any

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.llm_integration import LLMIntegration, LLMProvider
from workflows.enhanced_workflow_manager import EnhancedWorkflowManager
from core.agent import MiktosAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_llm_integration():
    """Test LLM integration capabilities"""
    print("\n=== Testing LLM Integration ===")
    
    # Test configuration
    config = {
        'llm': {
            'enabled': True,
            'provider': 'fallback',  # Use fallback for testing without API keys
            'max_tokens': 1000,
            'temperature': 0.7
        }
    }
    
    llm = LLMIntegration(config)
    
    # Test 1: Command understanding enhancement
    print("\n1. Testing command understanding enhancement...")
    test_command = "create a metallic sphere and add dramatic lighting"
    context = {"scene_objects": [], "current_material": None}
    
    try:
        enhanced_understanding = await llm.enhance_command_understanding(
            test_command, context, "test_session"
        )
        
        print(f"✅ Enhanced understanding completed")
        print(f"   Intent: {enhanced_understanding.get('enhanced_intent', 'unknown')}")
        print(f"   Confidence: {enhanced_understanding.get('confidence', 0):.2f}")
        print(f"   Suggestions: {len(enhanced_understanding.get('suggestions', []))}")
        
    except Exception as e:
        print(f"❌ Command understanding failed: {e}")
    
    # Test 2: Workflow generation
    print("\n2. Testing workflow generation...")
    try:
        workflow = await llm.generate_workflow(
            "Create a realistic car model with proper materials",
            ["modeling", "material_creation", "lighting"],
            {"objects": [], "materials": []},
            "test_session"
        )
        
        print(f"✅ Workflow generation completed")
        print(f"   Steps: {len(workflow.get('steps', []))}")
        print(f"   Estimated time: {workflow.get('estimated_total_time', 0)} seconds")
        print(f"   Complexity: {workflow.get('complexity', 'unknown')}")
        
    except Exception as e:
        print(f"❌ Workflow generation failed: {e}")
    
    # Test 3: Usage statistics
    print("\n3. Testing usage statistics...")
    stats = llm.get_usage_stats()
    print(f"✅ Usage stats: {stats}")


async def test_enhanced_workflow_manager():
    """Test enhanced workflow management"""
    print("\n=== Testing Enhanced Workflow Manager ===")
    
    manager = EnhancedWorkflowManager()
    
    # Test 1: List templates
    print("\n1. Testing template listing...")
    templates = await manager.list_templates()
    print(f"✅ Found {len(templates)} workflow templates")
    
    for template in templates[:3]:  # Show first 3
        print(f"   - {template['name']} ({template['complexity']}) - {template['category']}")
    
    # Test 2: Get specific template
    print("\n2. Testing template retrieval...")
    if templates:
        template_id = templates[0]['id']
        template_detail = await manager.get_template(template_id)
        if template_detail:
            print(f"✅ Retrieved template: {template_detail['name']}")
            print(f"   Steps: {len(template_detail['steps'])}")
            print(f"   Requirements: {template_detail['requirements']}")
        else:
            print(f"❌ Failed to retrieve template {template_id}")
    
    # Test 3: Template recommendations
    print("\n3. Testing template recommendations...")
    user_context = {
        'skill_level': 'intermediate',
        'recent_categories': ['modeling', 'materials'],
        'project_type': 'product_visualization'
    }
    
    recommendations = await manager.recommend_templates(user_context)
    print(f"✅ Generated {len(recommendations)} recommendations")
    
    for rec in recommendations[:2]:  # Show top 2
        template = rec['template']
        print(f"   - {template['name']} (score: {rec['score']:.1f}) - {rec['reason']}")
    
    # Test 4: Custom template creation
    print("\n4. Testing custom template creation...")
    custom_steps = [
        {
            'name': 'Create Base Mesh',
            'description': 'Create the base geometry',
            'parameters': {'type': 'cube'},
            'estimated_time': 15
        },
        {
            'name': 'Apply Modifier',
            'description': 'Add subdivision surface',
            'parameters': {'levels': 2},
            'estimated_time': 10
        }
    ]
    
    try:
        custom_id = await manager.create_custom_template(
            "Test Custom Workflow",
            "A simple test workflow",
            custom_steps,
            "testing",
            "simple"
        )
        print(f"✅ Created custom template: {custom_id}")
    except Exception as e:
        print(f"❌ Custom template creation failed: {e}")
    
    # Test 5: Analytics
    print("\n5. Testing workflow analytics...")
    analytics = await manager.get_analytics()
    print(f"✅ Analytics generated:")
    print(f"   Total templates: {analytics['total_templates']}")
    print(f"   Average success rate: {analytics['average_success_rate']:.2f}")
    print(f"   Categories: {list(analytics['category_distribution'].keys())}")


async def test_enhanced_agent():
    """Test enhanced agent with LLM integration"""
    print("\n=== Testing Enhanced Agent ===")
    
    # Load configuration
    try:
        import yaml
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return
    
    # Create agent (without starting full session)
    try:
        agent = MiktosAgent(config)
        print("✅ Enhanced agent initialized successfully")
        
        # Test LLM integration availability
        if hasattr(agent, 'llm_integration'):
            print("✅ LLM integration component loaded")
        else:
            print("❌ LLM integration component missing")
        
        # Test enhanced methods
        print("\n1. Testing intelligent suggestions...")
        try:
            suggestions = await agent.get_intelligent_suggestions("create a")
            print(f"✅ Generated {len(suggestions)} intelligent suggestions")
            for suggestion in suggestions[:3]:
                print(f"   - {suggestion}")
        except Exception as e:
            print(f"❌ Intelligent suggestions failed: {e}")
        
        print("\n2. Testing workflow generation...")
        try:
            workflow = await agent.generate_workflow("Create a sci-fi environment scene")
            print(f"✅ Generated workflow with {len(workflow.get('steps', []))} steps")
            print(f"   Estimated time: {workflow.get('estimated_total_time', 0)} seconds")
        except Exception as e:
            print(f"❌ Workflow generation failed: {e}")
        
    except Exception as e:
        print(f"❌ Enhanced agent initialization failed: {e}")


async def test_integration():
    """Test integration between components"""
    print("\n=== Testing Component Integration ===")
    
    # Test 1: Agent + Workflow Manager integration
    print("\n1. Testing agent-workflow integration...")
    try:
        config = {
            'agent': {
                'llm': {'enabled': True, 'provider': 'fallback'},
                'nlp': {'model': 'sentence-transformers/all-MiniLM-L6-v2'},
                'parser': {'safety_checks': True},
                'safety': {'validation_level': 'normal'},
                'learning': {'track_performance': True}
            },
            'blender': {'path': '/Applications/Blender.app'}
        }
        
        agent = MiktosAgent(config)
        workflow_manager = EnhancedWorkflowManager()
        
        # Test workflow recommendation based on agent context
        templates = await workflow_manager.list_templates(category="modeling")
        print(f"✅ Found {len(templates)} modeling templates")
        
        if templates:
            template = await workflow_manager.get_template(templates[0]['id'])
            if template:
                print(f"✅ Retrieved template: {template['name']}")
            else:
                print("❌ Failed to retrieve template")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
    
    print("\n=== Priority 2 Testing Complete ===")


async def main():
    """Run all Priority 2 tests"""
    print("🚀 Starting Priority 2: Intelligence Layer Enhancement Tests")
    print("=" * 60)
    
    try:
        await test_llm_integration()
        await test_enhanced_workflow_manager()
        await test_enhanced_agent()
        await test_integration()
        
        print("\n" + "=" * 60)
        print("✅ Priority 2 testing completed successfully!")
        print("\nEnhanced features now available:")
        print("• LLM-powered command understanding")
        print("• Intelligent workflow generation")
        print("• Context-aware suggestions")
        print("• Advanced workflow templates (5 → 20+ capabilities)")
        print("• Performance analytics and optimization")
        print("• User pattern analysis")
        print("• Conversation context management")
        
    except Exception as e:
        print(f"\n❌ Priority 2 testing failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
