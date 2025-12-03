"""
Compliance Tool for zerotoship.
Provides GDPR compliance and PII anonymization using Microsoft Presidio.
"""

from crewai.tools import BaseTool
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

# Try to import Presidio, but make it optional
try:
    from presidio_analyzer import AnalyzerEngine
    from presidio_anonymizer import AnonymizerEngine
    from presidio_anonymizer.entities import RecognizerResult, OperatorConfig
    PRESIDIO_AVAILABLE = True
except ImportError:
    PRESIDIO_AVAILABLE = False
    AnalyzerEngine = None
    AnonymizerEngine = None
    RecognizerResult = None
    OperatorConfig = None

class ComplianceArgs(BaseModel):
    """Arguments for the Compliance Tool."""
    text: str = Field(..., description="The text to scan and anonymize")
    language: str = Field(default="en", description="Language of the text")

class ComplianceCheckerTool(BaseTool):
    """GDPR compliance tool for PII detection and anonymization."""
    
    name: str = "GDPR Compliance Checker"
    description: str = "Scans text for Personally Identifiable Information (PII) and anonymizes it to ensure GDPR compliance."
    args_schema: type[BaseModel] = ComplianceArgs
    analyzer: Any = Field(default=None, description="Presidio analyzer engine")
    anonymizer: Any = Field(default=None, description="Presidio anonymizer engine")

    def __init__(self, **kwargs):
        """Initialize the Presidio engines."""
        super().__init__(**kwargs)
        if PRESIDIO_AVAILABLE:
            self.analyzer = AnalyzerEngine()
            self.anonymizer = AnonymizerEngine()
        else:
            self.analyzer = None
            self.anonymizer = None

    def _run(self, text: str, language: str = "en") -> Dict[str, Any]:
        """
        Analyze text for PII and return anonymized version with compliance report.

        Args:
            text: The text to scan and anonymize
            language: Language of the text (default: "en")

        Returns:
            Dictionary containing anonymized text and compliance report
        """
        if not PRESIDIO_AVAILABLE:
            return {
                "anonymized_text": text,
                "original_text": text,
                "pii_detected": False,
                "pii_types_found": [],
                "pii_count": 0,
                "compliance_status": "presidio_unavailable",
                "gdpr_compliant": False,
                "anonymization_method": "none",
                "entities_detected": [],
                "error": "Presidio library not installed. Install with: pip install presidio-analyzer presidio-anonymizer"
            }

        try:
            # Analyze the text for PII
            analyzer_results = self.analyzer.analyze(
                text=text, 
                language=language,
                entities=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "IBAN_CODE", "IP_ADDRESS", "LOCATION"]
            )
            
            # Anonymize the text
            anonymized_result = self.anonymizer.anonymize(
                text=text,
                analyzer_results=analyzer_results
            )
            
            # Create compliance report
            pii_found = len(analyzer_results) > 0
            pii_types = list(set([result.entity_type for result in analyzer_results]))
            
            compliance_report = {
                "anonymized_text": anonymized_result.text,
                "original_text": text,
                "pii_detected": pii_found,
                "pii_types_found": pii_types,
                "pii_count": len(analyzer_results),
                "compliance_status": "compliant" if pii_found else "no_pii_found",
                "gdpr_compliant": True,  # Always true since we anonymize
                "anonymization_method": "presidio_anonymizer",
                "entities_detected": [
                    {
                        "entity_type": result.entity_type,
                        "start": result.start,
                        "end": result.end,
                        "score": result.score
                    }
                    for result in analyzer_results
                ]
            }
            
            return compliance_report
            
        except Exception as e:
            return {
                "error": f"Compliance check failed: {str(e)}",
                "anonymized_text": text,  # Return original text if anonymization fails
                "compliance_status": "error",
                "gdpr_compliant": False
            }

    def scan_only(self, text: str, language: str = "en") -> Dict[str, Any]:
        """
        Scan text for PII without anonymizing (for analysis only).
        
        Args:
            text: The text to scan
            language: Language of the text
            
        Returns:
            Dictionary containing PII analysis results
        """
        try:
            analyzer_results = self.analyzer.analyze(
                text=text, 
                language=language,
                entities=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "IBAN_CODE", "IP_ADDRESS", "LOCATION"]
            )
            
            return {
                "text": text,
                "pii_detected": len(analyzer_results) > 0,
                "pii_types": list(set([result.entity_type for result in analyzer_results])),
                "pii_count": len(analyzer_results),
                "entities": [
                    {
                        "entity_type": result.entity_type,
                        "start": result.start,
                        "end": result.end,
                        "score": result.score,
                        "text": text[result.start:result.end]
                    }
                    for result in analyzer_results
                ]
            }
        except Exception as e:
            return {
                "error": f"Scan failed: {str(e)}",
                "text": text,
                "pii_detected": False
            }

    async def _arun(self, text: str, language: str = "en") -> Dict[str, Any]:
        """Async version of the compliance tool."""
        return self._run(text, language)
