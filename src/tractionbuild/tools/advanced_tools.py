# src/tractionbuild/tools/advanced_tools.py
from .salem_marketing_tool import SalemMarketingTool

class ToolRegistry:
    def _register_domain_tools(self):
        self.tools["Salem Marketing Asset Generator"] = SalemMarketingTool()
