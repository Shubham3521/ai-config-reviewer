# 🚀 Quick Start Guide - Auto PR Generator

## ✅ **System is Ready!**

Your auto-PR generation system with LangChain is now fully configured and ready to use.

## 🎯 **How It Works**

### **1. Automatic Daily Scanning** 📅
- **When**: Daily at 2 AM UTC
- **What**: Scans all Kubernetes YAML files
- **Result**: Creates PRs with security fixes

### **2. Smart Auto-Approval** 🤖
- **Safe fixes**: Auto-approved (no HIGH severity issues)
- **Risky changes**: Manual review required
- **AI analysis**: Evaluates each change for safety

### **3. Manual Triggering** 🔧
- Go to **Actions** tab in GitHub
- Run **"Auto PR Generator"** workflow manually
- Perfect for testing or immediate fixes

## 🛠️ **Setup (Already Done!)**

✅ **GitHub Secrets**: `OPENAI_API_KEY` (configured)  
✅ **Workflows**: Auto-PR and Auto-Approve workflows created  
✅ **Scripts**: All Python scripts ready  
✅ **Configuration**: `auto_pr_config.yaml` ready  

## 🧪 **Testing Locally**

```bash
# Test the system
python test_auto_pr.py

# Test auto-approve analyzer
python auto_approve_analyzer.py

# Test full PR generation (requires GitHub token)
export GITHUB_TOKEN="your-token"
export GITHUB_REPOSITORY="your-username/your-repo"
python auto_pr_generator.py
```

## 📊 **Example Workflow**

1. **Daily Scan** 🔍
   ```
   System finds: Hardcoded secrets, missing limits, etc.
   ```

2. **AI Fixes** 🧠
   ```
   LangChain generates: Secure YAML with fixes
   ```

3. **PR Creation** 📝
   ```
   Creates: "🔒 Security fixes for deployment.yaml"
   ```

4. **Auto-Approval** ✅
   ```
   Safe fixes: Auto-approved
   Risky changes: Manual review
   ```

## 🎉 **What Happens Next**

### **Immediate** (Next PR/Commit):
- Auto-approve workflow will analyze any new PRs
- Determines if changes are safe for auto-approval

### **Daily** (2 AM UTC):
- Auto-PR generator scans repository
- Creates PRs with security fixes
- Auto-approves safe changes

### **Manual** (Anytime):
- Trigger workflows manually from Actions tab
- Test system with `test_auto_pr.py`

## 🔧 **Customization**

Edit `auto_pr_config.yaml` to customize:
- **Schedule**: Change cron expression
- **Auto-approval rules**: Adjust severity thresholds
- **File patterns**: Include/exclude specific files
- **PR settings**: Branch names, titles, labels

## 📈 **Benefits You'll See**

- 🛡️ **Proactive Security**: Issues caught before production
- ⏰ **Time Saving**: Automated repetitive fixes
- 🎓 **Learning**: Team learns from AI improvements
- 🔄 **Consistency**: Uniform security practices

## 🚨 **Troubleshooting**

### **No PRs Created?**
- Check if YAML files have security issues
- Verify GitHub token permissions
- Check Actions logs for errors

### **Auto-Approval Not Working?**
- Review PR meets safety criteria
- Check severity levels in config
- Verify workflow permissions

### **Need Help?**
- Check `AUTO_PR_README.md` for detailed docs
- Review Actions tab for workflow logs
- Test with `test_auto_pr.py`

## 🎯 **Ready to Go!**

Your system is now live and will:
- ✅ **Scan daily** for security issues
- ✅ **Create PRs** with AI-generated fixes  
- ✅ **Auto-approve** safe changes
- ✅ **Require review** for risky changes

**Next Steps**: Wait for the next daily scan or trigger manually from the Actions tab! 🚀
