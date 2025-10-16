#!/usr/bin/env python3
"""
Test script for the Auto PR Generator system
This demonstrates how the system works without requiring GitHub Actions
"""

import os
import json
from auto_pr_generator import AutoPRGenerator

def test_analysis():
    """Test the YAML analysis functionality"""
    print("🧪 Testing Auto PR Generator Analysis...")
    
    # Check if we have the required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not found in environment")
        print("Please set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        return False
    
    if not os.getenv("GITHUB_TOKEN"):
        print("⚠️  GITHUB_TOKEN not found - will test analysis only (no PR creation)")
        print("To test full functionality, set:")
        print("export GITHUB_TOKEN='your-github-token'")
        print("export GITHUB_REPOSITORY='your-username/your-repo'")
    
    try:
        # Test with a sample YAML file
        test_yaml = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: test
  template:
    metadata:
      labels:
        app: test
    spec:
      containers:
        - name: test
          image: nginx
          env:
            - name: SECRET
              value: "hardcoded-secret"
          securityContext:
            privileged: true
"""
        
        print("\n📋 Testing with sample YAML:")
        print(test_yaml.strip())
        
        # Initialize generator (this will work even without GitHub token for analysis)
        generator = AutoPRGenerator()
        
        # Test analysis
        print("\n🔍 Analyzing for security issues...")
        issues = generator.analyze_yaml_file("test-deployment.yaml", test_yaml)
        
        print(f"\n📊 Found {len(issues)} issues:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. [{issue.get('severity', 'UNKNOWN')}] {issue.get('issue', 'Unknown')}")
            print(f"     Fix: {issue.get('recommendation', 'No recommendation')}")
        
        if issues:
            print("\n🔧 Testing fix generation...")
            fixed_yaml = generator.generate_fix("test-deployment.yaml", test_yaml, issues)
            print("✅ Fix generated successfully!")
            print("\n📝 Generated fix:")
            print(fixed_yaml[:200] + "..." if len(fixed_yaml) > 200 else fixed_yaml)
            
            # Test auto-approval logic
            auto_approve = generator.should_auto_approve(issues)
            print(f"\n🤖 Auto-approve: {'Yes' if auto_approve else 'No'}")
            
        else:
            print("✅ No security issues found!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

def show_usage():
    """Show how to use the system"""
    print("\n📖 How to Use the Auto PR System:")
    print("\n1. 🚀 GitHub Actions (Automatic):")
    print("   - Workflows run automatically on schedule")
    print("   - Scans repository for security issues")
    print("   - Creates PRs with fixes")
    print("   - Auto-approves safe changes")
    
    print("\n2. 🧪 Local Testing:")
    print("   - Set environment variables:")
    print("     export OPENAI_API_KEY='your-key'")
    print("     export GITHUB_TOKEN='your-token'")
    print("     export GITHUB_REPOSITORY='user/repo'")
    print("   - Run: python auto_pr_generator.py")
    
    print("\n3. 🔧 Manual Trigger:")
    print("   - Go to Actions tab in GitHub")
    print("   - Run 'Auto PR Generator' workflow manually")
    
    print("\n4. 📋 Configuration:")
    print("   - Edit auto_pr_config.yaml for custom settings")
    print("   - Adjust severity levels and auto-approval rules")

if __name__ == "__main__":
    print("🤖 Auto PR Generator Test Suite")
    print("=" * 50)
    
    success = test_analysis()
    
    if success:
        print("\n✅ Test completed successfully!")
    else:
        print("\n❌ Test failed - check your configuration")
    
    show_usage()
