import os, json, yaml, subprocess
from datetime import datetime
from github import Github
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

class AutoPRGenerator:
    def __init__(self):
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.repo_name = os.getenv("GITHUB_REPOSITORY")
        
        if not all([self.github_token, self.openai_api_key, self.repo_name]):
            raise ValueError("Missing required environment variables")
        
        self.github = Github(self.github_token)
        self.repo = self.github.get_repo(self.repo_name)
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    def analyze_yaml_file(self, file_path, content):
        """Analyze YAML file for issues using LangChain"""
        prompt = PromptTemplate(
            input_variables=["yaml_content"],
            template="""You are a Kubernetes security expert. Analyze this YAML for security issues.

YAML Content:
{yaml_content}

Return ONLY valid JSON in this format:
[
  {{"severity": "HIGH|MEDIUM|LOW", "issue": "description", "recommendation": "fix", "line": number}}
]

If no issues, return: []"""
        )
        
        chain = prompt | self.llm
        response = chain.invoke({"yaml_content": content})
        
        try:
            issues = json.loads(response.content if hasattr(response, 'content') else response)
            return issues
        except:
            return []
    
    def generate_fix(self, file_path, content, issues):
        """Generate fixed YAML using LangChain"""
        if not issues:
            return content
        
        prompt = PromptTemplate(
            input_variables=["yaml_content", "issues"],
            template="""You are a Kubernetes expert. Fix the security issues in this YAML.

Original YAML:
{yaml_content}

Issues to fix:
{issues}

Return ONLY the corrected YAML. No explanations or markdown."""
        )
        
        chain = prompt | self.llm
        response = chain.invoke({
            "yaml_content": content,
            "issues": json.dumps(issues, indent=2)
        })
        
        return response.content if hasattr(response, 'content') else response
    
    def create_pr(self, file_path, original_content, fixed_content, issues):
        """Create a pull request with the fixes"""
        # Create branch name
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        branch_name = f"security-fix-{os.path.basename(file_path)}-{timestamp}"
        
        # Get default branch
        default_branch = self.repo.default_branch
        
        # Create new branch
        ref = self.repo.get_git_ref(f"heads/{default_branch}")
        new_ref = self.repo.create_git_ref(
            ref=f"refs/heads/{branch_name}",
            sha=ref.object.sha
        )
        
        # Update file content
        file_blob = self.repo.create_git_blob(fixed_content, "utf-8")
        file_tree = self.repo.get_git_tree(sha=default_branch)
        
        # Create new tree with updated file
        new_tree = self.repo.create_git_tree(
            tree=[{
                "path": file_path,
                "mode": "100644",
                "type": "blob",
                "sha": file_blob.sha
            }],
            base_tree=file_tree.sha
        )
        
        # Create commit
        commit = self.repo.create_git_commit(
            message=f"🔒 Security fixes for {file_path}",
            tree=new_tree,
            parents=[self.repo.get_git_commit(sha=default_branch)]
        )
        
        # Update branch reference
        new_ref.edit(sha=commit.sha)
        
        # Create PR
        pr_title = f"🔒 Security fixes for {os.path.basename(file_path)}"
        pr_body = self.generate_pr_description(issues, file_path)
        
        pr = self.repo.create_pull(
            title=pr_title,
            body=pr_body,
            head=branch_name,
            base=default_branch
        )
        
        return pr
    
    def generate_pr_description(self, issues, file_path):
        """Generate PR description with issue details"""
        high_issues = [i for i in issues if i.get("severity") == "HIGH"]
        medium_issues = [i for i in issues if i.get("severity") == "MEDIUM"]
        low_issues = [i for i in issues if i.get("severity") == "LOW"]
        
        description = f"""## 🔒 Security Fixes for `{file_path}`

This PR contains automated security fixes for Kubernetes configuration issues.

### 📊 Issues Found
- **HIGH**: {len(high_issues)} issues
- **MEDIUM**: {len(medium_issues)} issues  
- **LOW**: {len(low_issues)} issues

### 🔧 Fixes Applied
"""
        
        for issue in issues:
            description += f"- **{issue.get('severity', 'UNKNOWN')}**: {issue.get('issue', 'Unknown issue')}\n"
            description += f"  - *Fix*: {issue.get('recommendation', 'No recommendation')}\n"
        
        description += f"""
### 🤖 Auto-Generated
This PR was automatically generated by the AI Security Review system.

**Review Status**: ⏳ Pending manual review
**Auto-approve**: {'✅ Yes' if len(high_issues) == 0 else '❌ No - Contains HIGH severity issues'}
"""
        
        return description
    
    def should_auto_approve(self, issues):
        """Determine if PR should be auto-approved based on issue severity"""
        high_issues = [i for i in issues if i.get("severity") == "HIGH"]
        return len(high_issues) == 0
    
    def process_repository(self):
        """Main function to process all YAML files and create PRs"""
        print("🔍 Scanning repository for Kubernetes YAML files...")
        
        # Get all YAML files (excluding workflows)
        yaml_files = []
        for root, _, files in os.walk("."):
            for file in files:
                if file.endswith((".yaml", ".yml")):
                    file_path = os.path.join(root, file)
                    if ".github/workflows/" not in file_path and "workflow" not in file.lower():
                        yaml_files.append(file_path)
        
        print(f"📁 Found {len(yaml_files)} Kubernetes YAML files")
        
        prs_created = []
        
        for file_path in yaml_files:
            print(f"\n🔍 Analyzing {file_path}...")
            
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Analyze for issues
                issues = self.analyze_yaml_file(file_path, content)
                
                if not issues:
                    print(f"✅ No issues found in {file_path}")
                    continue
                
                print(f"⚠️  Found {len(issues)} issues in {file_path}")
                
                # Generate fix
                fixed_content = self.generate_fix(file_path, content, issues)
                
                # Create PR
                pr = self.create_pr(file_path, content, fixed_content, issues)
                prs_created.append(pr)
                
                auto_approve = self.should_auto_approve(issues)
                print(f"🔗 Created PR: {pr.html_url}")
                print(f"🤖 Auto-approve: {'Yes' if auto_approve else 'No'}")
                
            except Exception as e:
                print(f"❌ Error processing {file_path}: {e}")
                continue
        
        print(f"\n🎉 Created {len(prs_created)} pull requests")
        return prs_created

if __name__ == "__main__":
    try:
        generator = AutoPRGenerator()
        prs = generator.process_repository()
        
        if prs:
            print("\n📋 Summary of created PRs:")
            for pr in prs:
                print(f"- {pr.title}: {pr.html_url}")
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)
