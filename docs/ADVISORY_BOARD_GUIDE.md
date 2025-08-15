# 🚀 ZeroToShip Advisory Board Guide

## Overview

The **Advisory Board** is ZeroToShip's interactive AI-powered idea refinement system. It transforms vague user ideas into hyper-targeted, data-validated mission statements using real-time market insights and expert analysis.

## 🎯 What It Does

The Advisory Board consists of five specialized AI agents that work together to:

1. **Analyze** your initial idea using real-time market data

2. **Refine** it into a specific, actionable mission statement

3. **Validate** technical feasibility and market opportunity

4. **Enhance** with creative innovations and differentiation strategies

5. **Deliver** a comprehensive plan with next steps

## 👥 The Advisory Board Members

### 🎯 Chief Strategist & Orchestrator

- **Role**: Leads the discussion and synthesizes insights

- **Goal**: Transform vague ideas into hyper-targeted missions

- **Expertise**: Venture strategy, prioritization, clarity

### 📊 Real-Time Market Analyst

- **Role**: Provides data-driven market insights

- **Goal**: Deliver objective market data and trends

- **Tools**: Market Oracle Scanner (real-time data sources)

- **Expertise**: SEO trends, Reddit sentiment, market sizing

### ❤️ User Champion & Empathy Advocate

- **Role**: Ensures user-centric focus

- **Goal**: Validate user desirability and pain points

- **Expertise**: User research, empathy, customer validation

### 🔧 Tech Validator

- **Role**: Assesses technical feasibility

- **Goal**: Ensure ideas are technically viable

- **Expertise**: Technology assessment, architecture planning

### 💡 Wild Card Innovator

- **Role**: Introduces creative enhancements

- **Goal**: Push boundaries and add unique value

- **Expertise**: Innovation, differentiation, creative thinking

## 🚀 How to Use

### Option 1: Interactive Chat UI (Recommended)

1. **Start the Chat UI**:

   ```bash
   streamlit run chat_ui.py
   ```

2. **Open your browser** to `http://localhost:8501`

3. **Enter your idea** in the text area and click "🚀 Submit to Advisory Board"

4. **Wait for analysis** - the board will deliberate and provide insights

5. **Review results** - get your refined mission statement and recommendations

### Option 2: Programmatic Usage

```python
from zerotoship.crews import AdvisoryBoardCrew

# Initialize the crew

project_data = {
    "idea": "I want to build an app that helps people manage their daily tasks",
    "user_id": "user_123",
    "session_id": "session_456"
}

crew = AdvisoryBoardCrew(project_data)

# Execute the advisory session

result = await crew.run_async(project_data)

# Access the results

mission_statement = result.get("mission_statement")
insights = result.get("insights")
recommendations = result.get("recommendations")

```

### Option 3: API Integration

```bash
# Start the workflow

curl -X POST "http://localhost:8000/run-workflow/" \
  -H "Content-Type: application/json" \
  -d '{
    "idea": "I want to build a task management app",
    "workflow_name": "advisory_board_workflow"
  }'

# Check status

curl "http://localhost:8000/task-status/{task_id}"

```

## 📊 Output Format

The Advisory Board returns structured results:

```json
{
  "mission_statement": "Build a meal planning app for vegan diabetic athletes who travel frequently",
  "validation_status": "completed",
  "confidence_score": 0.85,
  "insights": [
    "High demand for specialized dietary apps",
    "Existing solutions lack travel-specific features",
    "Strong community in target demographic"
  ],
  "recommendations": [
    "Focus on mobile-first design",
    "Integrate with fitness tracking apps",
    "Build community features"
  ],
  "market_data": {
    "seo_trends": {...},
    "reddit_discussion": {...},
    "market_insights": {...}
  },
  "next_steps": [
    "Proceed to idea validation",
    "Begin market research",
    "Start technical planning"
  ]
}

```

## 🔧 Configuration

### AdvisoryBoardCrewConfig

```python
from zerotoship.crews.advisory_board_crew import AdvisoryBoardCrewConfig

config = AdvisoryBoardCrewConfig(
    enable_memory_learning=True,
    enable_interactive_refinement=True,
    max_refinement_iterations=3
)

```

### Environment Variables

```bash
# API Configuration

ZEROTOSHIP_API_URL=http://localhost:8000
ZEROTOSHIP_WORKFLOW_NAME=advisory_board_workflow

# Market Oracle Configuration

MARKET_ORACLE_ENABLED=true
MARKET_ORACLE_TIMEOUT=30

```

## 🛠️ Development

### Running Tests

```bash
# Test the Advisory Board Crew

python test_advisory_board.py

# Run all tests

pytest tests/

```

### Adding New Market Data Sources

1. **Extend MarketOracleTool** in `src/zerotoship/tools/market_oracle_tool.py`

2. **Add new API integrations** for additional data sources

3. **Update the tool's response format** to include new insights

### Customizing Agents

1. **Modify agent definitions** in `src/zerotoship/crews/advisory_board_crew.py`

2. **Add new tools** to specific agents

3. **Adjust goals and backstories** for different use cases

## 🔍 Troubleshooting

### Common Issues

1. **"AdvisoryBoardCrew not found"**
   - Ensure the crew is properly imported
   - Check that the file is in the correct location
   - Verify the class name ends with "Crew"

2. **"Market Oracle failed"**
   - Check network connectivity
   - Verify API keys are configured
   - Review timeout settings

3. **"Chat UI not responding"**
   - Ensure Streamlit is installed: `pip install streamlit streamlit-chat`
   - Check API URL configuration
   - Verify the API server is running

### Debug Mode

Enable verbose logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or in the crew configuration

crew = AdvisoryBoardCrew(project_data, verbose=True)

```

## 🚀 Next Steps

After getting your refined mission statement:

1. **Validate the idea** using the `ValidatorCrew`

2. **Build the MVP** with the `BuilderCrew`

3. **Launch and market** with the `LaunchCrew` and `MarketingCrew`

## 📚 Related Documentation

- [ZeroToShip Overview](../README.md)

- [Crew Architecture](CREW_ARCHITECTURE.md)

- [API Documentation](API_GUIDE.md)

- [Workflow Configuration](WORKFLOW_GUIDE.md)

## 🤝 Contributing

To contribute to the Advisory Board:

1. **Fork the repository**

2. **Create a feature branch**

3. **Make your changes**

4. **Add tests**

5. **Submit a pull request**

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/zerotoship/zerotoship/issues)

- **Discussions**: [GitHub Discussions](https://github.com/zerotoship/zerotoship/discussions)

- **Documentation**: [ZeroToShip Docs](https://zerotoship.dev)
