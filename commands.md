# TractionBuild Commands Reference

## 🚀 Quick Start Commands

### Start Server
```bash
# PowerShell (Recommended)
.\start_tractionbuild.ps1

# Batch file
run_tractionbuild.bat

# Manual
& .\.venv\Scripts\Activate.ps1
python app_v1_real_integration.py
```

### Test Salem AI
```bash
# Test Salem marketing generation
.\test_tractionbuild.ps1 -SalemTest

# Test complete workflow
.\test_tractionbuild.ps1 -WorkflowTest

# Health check
.\test_tractionbuild.ps1 -Health
```

---

## 📋 API Endpoints

### Health & Status
```bash
# Health check
Invoke-RestMethod -Uri "http://localhost:8000/health"

# List projects
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/projects"
```

### Project Management
```bash
# Create project
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/projects" -Method Post -ContentType "application/json" -Body '{"name":"Test","description":"Test project","workflow":"default_software_build"}'

# Get project
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/projects/{project_id}"

# Get project status
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/projects/{project_id}/status"
```

---

## 🔧 Troubleshooting

### Connection Issues
```bash
# Kill Python processes
Stop-Process -Name "python" -Force

# Force restart
.\start_tractionbuild.ps1 -Force

# Check port usage
netstat -ano | findstr :8000
```

### Virtual Environment
```bash
# Activate manually
& .\.venv\Scripts\Activate.ps1

# Check activation
(.venv) PS C:\Users\jthri\Dev\MySauce\TractionBuild>
```

---

## 📊 Monitoring

### Project Progress
```bash
# Monitor specific project
.\test_tractionbuild.ps1 -ProjectId {project_id} -Status

# List all runs
.\test_tractionbuild.ps1 -List
```

### Logs
```bash
# View server logs
type runs\{project_id}\events.jsonl

# Check runs directory
ls runs\
```

---

## 🎯 Salem AI Commands

### Marketing Asset Generation
```bash
# Test Salem specifically
.\test_tractionbuild.ps1 -SalemTest

# Create Salem marketing project
$body = '{"name":"Salem Test","description":"Salem marketing test","hypothesis":"Test Salem assets","target_avatars":["tech_founder"],"workflow":"default_software_build"}' | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/projects" -Method Post -ContentType "application/json" -Body $body
```

### Workflow Monitoring
```bash
# Monitor Salem phase
.\test_tractionbuild.ps1 -WorkflowTest

# Check when Salem activates
# Look for: MARKETING_PREPARATION state
```

---

## 📁 File Structure

```
TractionBuild/
├── start_tractionbuild.ps1     # 🚀 Server startup script
├── test_tractionbuild.ps1      # 🧪 Testing script
├── run_tractionbuild.bat       # ⚡ Quick batch starter
├── README_SCRIPTS.md           # 📖 Detailed documentation
├── commands.md                 # 📋 This reference
├── app_v1_real_integration.py  # 🌐 Main application
├── config/
│   ├── workflows.yaml          # 🔄 Workflow definitions
│   └── crew_config.yaml        # 👥 Crew configurations
├── runs/                       # 📊 Project artifacts
└── src/tractionbuild/          # 🏗️  Source code
```

---

## 🎉 Success Commands

### Verify Everything Works
```bash
# 1. Start server
.\start_tractionbuild.ps1

# 2. Test health
.\test_tractionbuild.ps1 -Health

# 3. Test Salem
.\test_tractionbuild.ps1 -SalemTest

# 4. Check results
.\test_tractionbuild.ps1 -List
```

### Full Workflow Test
```bash
# Complete end-to-end test
.\test_tractionbuild.ps1 -WorkflowTest

# Expected output:
# ✅ Project created
# 🔄 IDEA_VALIDATION → TASK_EXECUTION → MARKETING_PREPARATION → COMPLETED
# 🎉 Salem marketing assets generated
```

---

## 🚨 Emergency Commands

### If Server Won't Start
```bash
# Kill everything
Stop-Process -Name "python" -Force
Stop-Process -Name "uvicorn" -Force

# Clean restart
.\start_tractionbuild.ps1 -Force
```

### If Port 8000 is Blocked
```bash
# Check what's using port 8000
netstat -ano | findstr :8000

# Kill process using port
Stop-Process -Id {PID} -Force
```

---

## 🤖 Salem AI Integration

### Marketing Assets Generated
- 🎯 **Positioning**: Brand messaging and market positioning
- 📝 **Landing Copy**: Hero copy, value propositions, CTAs
- 🐦 **Twitter/X**: Engagement hooks, thread sequences
- 💼 **LinkedIn**: Professional content, thought leadership
- 📧 **Email**: Nurture campaigns, conversion funnels
- 🎥 **YouTube**: Video content, tutorials, positioning

### Workflow Integration
```
IDEA_VALIDATION → TASK_EXECUTION → MARKETING_PREPARATION → FEEDBACK_COLLECTION
     ↓                ↓                ↓                        ↓
 ValidatorCrew    BuilderCrew     MarketingCrew            FeedbackCrew
   (Market)       (Code Gen)     (Salem Assets)           (Analysis)
```

**Salem activates in MARKETING_PREPARATION phase using Salem Marketing Specialist agent**

---

## 📞 Quick Reference

| Command | Purpose | Status |
|---------|---------|--------|
| `.\start_tractionbuild.ps1` | Start server | ✅ Ready |
| `.\test_tractionbuild.ps1 -Health` | Check health | ✅ Ready |
| `.\test_tractionbuild.ps1 -SalemTest` | Test Salem AI | ✅ Ready |
| `.\test_tractionbuild.ps1 -WorkflowTest` | Full workflow | ✅ Ready |
| `run_tractionbuild.bat` | Quick start | ✅ Ready |

**🎯 Your TractionBuild system with Salem AI is fully operational!**
