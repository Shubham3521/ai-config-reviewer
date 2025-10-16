import os, json, yaml
from github import Github
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

class AutoApproveAnalyzer:
    def __init__(self):
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.repo_name = os.getenv("GITHUB_REPOSITORY")
        
        if not all([self.github_token, self.openai_api_key, self.repo_name]):
            raise ValueError("Missing required environment variables")
        
        self.github = Github(self.github_token)
        self.repo = self.github.get_repo(self.repo_name)
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    def analyze_changes(self, pr_number):
        """Analyze PR changes to determine if auto-approval is safe"""
        pr = self.repo.get_pull(pr_number)
        
        # Get changed files
        changed_files = []
        for file in pr.get_files():
            if file.filename.endswith(('.yaml', '.yml')):
                changed_files.append({
                    'filename': file.filename,
                    'patch': file.patch,
                    'status': file.status
                })
        
        if not changed_files:
            print("ℹ️  No YAML files changed")
            return False
        
        # Analyze each changed file
        for file_info in changed_files:
            if not self.is_safe_change(file_info):
                return False
        
        return True
    
    def is_safe_change(self, file_info):
        """Determine if a specific file change is safe for auto-approval"""
        prompt = PromptTemplate(
            input_variables=["filename", "patch"],
            template="""You are a Kubernetes security expert. Analyze this git patch to determine if it's safe to auto-approve.

File: {filename}
Patch:
{patch}

Consider these criteria for auto-approval:
1. Only security fixes (removing hardcoded secrets, adding resource limits, etc.)
2. No breaking changes to functionality
3. No removal of critical security features
4. Only adds or improves security configurations
5. No changes to image tags or versions
6. No changes to environment variables (except security-related)

Respond with ONLY JSON:
{{"safe": true/false, "reason": "explanation"}}"""
        )
        
        chain = prompt | self.llm
        response = chain.invoke({
            "filename": file_info['filename'],
            "patch": file_info['patch']
        })
        
        try:
            result = json.loads(response.content if hasattr(response, 'content') else response)
            print(f"📋 {file_info['filename']}: {result.get('reason', 'No reason provided')}")
            return result.get('safe', False)
        except:
            print(f"⚠️  Could not analyze {file_info['filename']} - defaulting to manual review")
            return False
    
    def check_pr_metadata(self, pr_number):
        """Check PR metadata for auto-approval indicators"""
        pr = self.repo.get_pull(pr_number)
        
        # Check if PR title indicates security fix
        title_lower = pr.title.lower()
        security_indicators = [
            'security fix', 'security', '🔒', 'fix', 'patch',
            'hardcoded', 'secret', 'resource', 'limit', 'probe'
        ]
        
        has_security_indicator = any(indicator in title_lower for indicator in security_indicators)
        
        # Check if PR body indicates auto-generated
        body_lower = pr.body.lower() if pr.body else ""
        is_auto_generated = 'auto-generated' in body_lower or '🤖' in body_lower
        
        # Check if it's a small change (fewer than 50 lines changed)
        total_changes = sum(file.changes for file in pr.get_files())
        is_small_change = total_changes < 50
        
        print(f"📊 PR Analysis:")
        print(f"  - Security indicator: {has_security_indicator}")
        print(f"  - Auto-generated: {is_auto_generated}")
        print(f"  - Small change: {is_small_change} ({total_changes} lines)")
        
        return has_security_indicator and is_auto_generated and is_small_change
    
    def analyze_pr(self, pr_number):
        """Main analysis function"""
        print(f"🔍 Analyzing PR #{pr_number} for auto-approval...")
        
        # Check metadata first
        if not self.check_pr_metadata(pr_number):
            print("❌ PR does not meet metadata criteria for auto-approval")
            return False
        
        # Analyze actual changes
        if not self.analyze_changes(pr_number):
            print("❌ PR changes are not safe for auto-approval")
            return False
        
        print("✅ PR is safe for auto-approval")
        return True

if __name__ == "__main__":
    pr_number = os.getenv("GITHUB_EVENT_NUMBER")
    
    # Test mode - if no PR number, run in test mode
    if not pr_number:
        print("🧪 Running in test mode (no PR number found)")
        print("This script is designed to run in GitHub Actions workflow context.")
        print("To test locally, you can:")
        print("1. Set GITHUB_EVENT_NUMBER environment variable")
        print("2. Or run the auto_pr_generator.py instead")
        print("\nExample usage in GitHub Actions:")
        print("  - Triggered on pull_request events")
        print("  - Analyzes PR changes for auto-approval safety")
        print("  - Sets AUTO_APPROVE environment variable")
        exit(0)
    
    try:
        analyzer = AutoApproveAnalyzer()
        is_safe = analyzer.analyze_pr(int(pr_number))
        
        # Set environment variable for next step (only in GitHub Actions)
        if 'GITHUB_ENV' in os.environ:
            print(f"AUTO_APPROVE={'true' if is_safe else 'false'}")
            with open(os.environ['GITHUB_ENV'], 'a') as f:
                f.write(f"AUTO_APPROVE={'true' if is_safe else 'false'}\n")
        else:
            print(f"Local test result: AUTO_APPROVE={'true' if is_safe else 'false'}")
        
        if is_safe:
            print("🤖 This PR will be auto-approved")
        else:
            print("👤 This PR requires manual review")
            
    except Exception as e:
        print(f"❌ Error analyzing PR: {e}")
        # Default to manual review on error
        if 'GITHUB_ENV' in os.environ:
            with open(os.environ['GITHUB_ENV'], 'a') as f:
                f.write("AUTO_APPROVE=false\n")
        exit(1)
