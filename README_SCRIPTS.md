# TractionBuild Scripts Guide

## 🚀 Quick Start

### 1. Start the Server
```powershell
.\start_tractionbuild.ps1
```

### 2. Test Salem AI Integration
```powershell
.\test_tractionbuild.ps1 -SalemTest
```

### 3. Check Results
```powershell
.\test_tractionbuild.ps1 -List
```

---

## 📋 Available Scripts

### `start_tractionbuild.ps1`
**Purpose:** Start TractionBuild server with Salem AI integration

**Usage:**
```powershell
# Normal start
.\start_tractionbuild.ps1

# Force restart (kills existing processes)
.\start_tractionbuild.ps1 -Force

# Start in background
.\start_tractionbuild.ps1 -Background
```

**Features:**
- ✅ Auto-detects if server is running
- 🔄 Force restart option
- 🎯 Background/foreground modes
- 📦 Virtual environment activation
- 🌐 Server status verification

---

### `test_tractionbuild.ps1`
**Purpose:** Test TractionBuild functionality and Salem AI integration

**Usage:**
```powershell
# Health check
.\test_tractionbuild.ps1 -Health

# Create test project
.\test_tractionbuild.ps1 -CreateNew

# Test Salem AI marketing generation
.\test_tractionbuild.ps1 -SalemTest

# Test complete workflow
.\test_tractionbuild.ps1 -WorkflowTest

# Get project status
.\test_tractionbuild.ps1 -ProjectId <project_id> -Status

# Get full project details
.\test_tractionbuild.ps1 -ProjectId <project_id>

# List runs directory
.\test_tractionbuild.ps1 -List
```

**Salem AI Testing:**
- `SalemTest`: Creates project and monitors Salem marketing asset generation
- `WorkflowTest`: Tests full workflow including Salem MARKETING_PREPARATION phase

---

## 🎯 Workflow Overview

```
IDEA_VALIDATION → TASK_EXECUTION → MARKETING_PREPARATION → FEEDBACK_COLLECTION
     ↓                ↓                ↓                        ↓
 ValidatorCrew    BuilderCrew     MarketingCrew            FeedbackCrew
   (Market)       (Code Gen)     (Salem Assets)           (Analysis)
```

**Salem Integration:** MarketingCrew uses Salem AI to generate:
- 🎯 Brand positioning and messaging
- 📝 Landing page copy and CTAs
- 🐦 Twitter/X content threads
- 💼 LinkedIn professional content
- 📧 Email nurture sequences
- 🎥 YouTube video scripts

---

## 🔧 Troubleshooting

### Connection Refused Error
```powershell
# Kill existing processes
Stop-Process -Name "python" -Force

# Restart server
.\start_tractionbuild.ps1 -Force
```

### Virtual Environment Issues
```powershell
# Manual activation
& C:\Users\jthri\Dev\MySauce\TractionBuild\.venv\Scripts\Activate.ps1
python app_v1_real_integration.py
```

### Check Server Status
```powershell
# Health endpoint
Invoke-RestMethod -Uri "http://localhost:8000/health"

# Test API
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/projects"
```

---

## 📊 Project Monitoring

### Real-time Status
```powershell
# Get project status
.\test_tractionbuild.ps1 -ProjectId <project_id> -Status

# Monitor workflow progress
.\test_tractionbuild.ps1 -WorkflowTest
```

### Check Artifacts
```powershell
# View runs directory
.\test_tractionbuild.ps1 -List

# Manual check
ls runs\
```

---

## 🤖 Salem AI Features

### Marketing Assets Generated
- **Positioning**: Brand messaging and market positioning
- **Landing Copy**: Hero copy, value propositions, CTAs
- **Social Media**: Twitter/X threads, LinkedIn posts
- **Email**: Nurture sequences and conversion funnels
- **Video**: YouTube script intros and positioning videos
- **Performance**: Content performance tracking

### Workflow Integration
- Automatically triggered in MARKETING_PREPARATION phase
- Uses Salem Marketing Specialist agent
- Generates assets based on project validation data
- Saves artifacts to project runs directory

---

## 🎉 Success Indicators

### Server Started Successfully
```
✅ Server already running on port 8000
🌐 Server will be available at: http://localhost:8000
🤖 Salem AI marketing automation ready!
```

### Salem Test Passed
```
🤖 Salem Marketing Test Project Created!
🎯 Salem Marketing Phase Reached!
🤖 Salem AI is generating marketing assets...
```

### Workflow Completed
```
🎉 Full workflow completed successfully!
📊 Final status: 100% complete
```

---

## 📞 Support

If you encounter issues:
1. Run `.\start_tractionbuild.ps1 -Force`
2. Check `.\test_tractionbuild.ps1 -Health`
3. Verify virtual environment activation
4. Check Windows Firewall settings

**Your TractionBuild system with Salem AI is now fully operational! 🚀✨**
