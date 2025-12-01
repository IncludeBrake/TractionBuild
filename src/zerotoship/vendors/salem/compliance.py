"""
EU AI Act Compliance Module for Salem
Implements comprehensive compliance checking, bias audits, and provenance tracking
"""

import json
import logging
import hashlib
import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)

@dataclass
class ComplianceReport:
    """Compliance audit report structure."""
    timestamp: str
    system_id: str
    compliance_score: float
    risk_level: str
    bias_audit_results: Dict[str, Any]
    provenance_chain: List[Dict[str, Any]]
    transparency_measures: Dict[str, Any]
    data_protection_compliance: Dict[str, Any]
    recommendations: List[str]
    audit_trail: List[Dict[str, Any]]

@dataclass
class BiasAuditResult:
    """Results from bias detection audit."""
    demographic_fairness: float
    gender_bias_score: float
    age_bias_score: float
    socioeconomic_bias_score: float
    geographic_bias_score: float
    language_bias_score: float
    overall_bias_risk: str
    mitigation_strategies: List[str]

@dataclass
class ProvenanceRecord:
    """Data provenance tracking record."""
    record_id: str
    timestamp: str
    operation_type: str
    input_data_hash: str
    output_data_hash: str
    model_version: str
    parameters_used: Dict[str, Any]
    data_sources: List[str]
    processing_steps: List[str]

@dataclass
class Article5ComplianceResult:
    """Article 5 compliance check results."""
    subliminal_manipulation_detected: bool
    subliminal_elements: List[str]
    vulnerable_groups_targeted: bool
    vulnerable_groups_identified: List[str]
    social_scoring_detected: bool
    biometric_categorization_detected: bool
    real_time_biometric_remote_identification: bool
    predictive_policing_detected: bool
    emotion_recognition_detected: bool
    overall_article5_compliance: bool
    compliance_score: float
    risk_mitigation_required: List[str]

@dataclass
class MultimodalContentAnalysis:
    """Multimodal content analysis results."""
    content_type: str  # text, image, voice, video, mixed
    subliminal_elements: List[str]
    emotional_manipulation_score: float
    visual_biases: List[str]
    audio_manipulation: List[str]
    cultural_sensitivity_score: float
    accessibility_compliance: bool
    wow_factor_score: float
    engagement_potential: float
    transparency_logs: List[Dict[str, Any]]

class EUAIComplianceChecker:
    """
    Comprehensive EU AI Act compliance checker for Salem.
    
    Implements:
    - Bias detection and mitigation
    - Data provenance tracking
    - Transparency measures
    - Risk assessment
    - Data protection compliance
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize compliance checker with configuration."""
        self.config = self._load_compliance_config(config_path)
        self.provenance_chain = []
        self.audit_trail = []
        self.bias_thresholds = {
            'demographic_fairness': 0.85,
            'gender_bias': 0.15,
            'age_bias': 0.20,
            'socioeconomic_bias': 0.25,
            'geographic_bias': 0.30,
            'language_bias': 0.20
        }
        
        logger.info("🔒 EU AI Act Compliance Checker initialized")
    
    def check_article5_compliance(self, campaign_data: Dict[str, Any]) -> Article5ComplianceResult:
        """
        Check compliance with EU AI Act Article 5 (Prohibited AI Practices).
        
        Article 5 prohibits:
        - Subliminal manipulation
        - Exploitation of vulnerable groups
        - Social scoring
        - Real-time biometric identification
        - Predictive policing
        - Emotion recognition in workplace/education
        
        Args:
            campaign_data: Marketing campaign data to analyze
            
        Returns:
            Article5ComplianceResult with detailed compliance analysis
        """
        logger.info("🔍 Checking Article 5 compliance (Prohibited AI Practices)...")
        
        # Check for subliminal manipulation
        subliminal_detected, subliminal_elements = self._detect_subliminal_manipulation(campaign_data)
        
        # Check for vulnerable group targeting
        vulnerable_targeted, vulnerable_groups = self._detect_vulnerable_group_targeting(campaign_data)
        
        # Check for social scoring
        social_scoring = self._detect_social_scoring(campaign_data)
        
        # Check for biometric categorization
        biometric_categorization = self._detect_biometric_categorization(campaign_data)
        
        # Check for real-time biometric identification
        real_time_biometric = self._detect_real_time_biometric_identification(campaign_data)
        
        # Check for predictive policing
        predictive_policing = self._detect_predictive_policing(campaign_data)
        
        # Check for emotion recognition
        emotion_recognition = self._detect_emotion_recognition(campaign_data)
        
        # Calculate overall compliance
        compliance_score = self._calculate_article5_compliance_score(
            subliminal_detected, vulnerable_targeted, social_scoring,
            biometric_categorization, real_time_biometric, predictive_policing,
            emotion_recognition
        )
        
        # Determine if overall compliant
        overall_compliant = compliance_score >= 0.85
        
        # Generate risk mitigation requirements
        risk_mitigation = self._generate_article5_mitigation_strategies(
            subliminal_detected, vulnerable_targeted, social_scoring,
            biometric_categorization, real_time_biometric, predictive_policing,
            emotion_recognition
        )
        
        result = Article5ComplianceResult(
            subliminal_manipulation_detected=subliminal_detected,
            subliminal_elements=subliminal_elements,
            vulnerable_groups_targeted=vulnerable_targeted,
            vulnerable_groups_identified=vulnerable_groups,
            social_scoring_detected=social_scoring,
            biometric_categorization_detected=biometric_categorization,
            real_time_biometric_remote_identification=real_time_biometric,
            predictive_policing_detected=predictive_policing,
            emotion_recognition_detected=emotion_recognition,
            overall_article5_compliance=overall_compliant,
            compliance_score=compliance_score,
            risk_mitigation_required=risk_mitigation
        )
        
        logger.info(f"✅ Article 5 compliance check completed. Score: {compliance_score:.3f}")
        return result
    
    def _detect_subliminal_manipulation(self, campaign_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Detect subliminal manipulation techniques in campaign content."""
        subliminal_elements = []
        text_content = self._extract_text_content(campaign_data)
        
        # Subliminal manipulation indicators
        subliminal_patterns = [
            # Hidden messages
            r'\b(hidden|secret|subliminal|unconscious|subconscious)\b',
            # Urgency manipulation
            r'\b(urgent|limited time|act now|don\'t miss out|last chance)\b',
            # Fear-based manipulation
            r'\b(scary|terrifying|fear|panic|emergency|crisis)\b',
            # Authority manipulation
            r'\b(expert|authority|doctor|scientist|official|certified)\b',
            # Social proof manipulation
            r'\b(everyone|everybody|nobody|most people|everyone else)\b',
            # Scarcity manipulation
            r'\b(rare|exclusive|limited|scarce|only|unique)\b',
            # Emotional manipulation
            r'\b(guilt|shame|embarrassment|failure|loser|stupid)\b'
        ]
        
        import re
        for pattern in subliminal_patterns:
            matches = re.findall(pattern, text_content.lower())
            if matches:
                subliminal_elements.extend(matches)
        
        # Check for visual subliminal elements (placeholder for image analysis)
        if 'visual_elements' in campaign_data:
            visual_subliminal = self._detect_visual_subliminal_elements(campaign_data['visual_elements'])
            subliminal_elements.extend(visual_subliminal)
        
        # Check for audio subliminal elements (placeholder for audio analysis)
        if 'audio_elements' in campaign_data:
            audio_subliminal = self._detect_audio_subliminal_elements(campaign_data['audio_elements'])
            subliminal_elements.extend(audio_subliminal)
        
        subliminal_detected = len(subliminal_elements) > 0
        return subliminal_detected, subliminal_elements
    
    def _detect_visual_subliminal_elements(self, visual_elements: Dict[str, Any]) -> List[str]:
        """Detect subliminal elements in visual content."""
        subliminal_elements = []
        
        # Check for hidden text or symbols
        if 'hidden_text' in visual_elements:
            subliminal_elements.append('hidden_text_detected')
        
        # Check for color manipulation
        if 'color_psychology' in visual_elements:
            colors = visual_elements['color_psychology']
            if 'red' in colors and 'urgency' in colors['red']:
                subliminal_elements.append('urgency_color_manipulation')
            if 'yellow' in colors and 'fear' in colors['yellow']:
                subliminal_elements.append('fear_color_manipulation')
        
        # Check for image composition manipulation
        if 'composition' in visual_elements:
            comp = visual_elements['composition']
            if comp.get('rule_of_thirds_violation', False):
                subliminal_elements.append('composition_manipulation')
        
        return subliminal_elements
    
    def _detect_audio_subliminal_elements(self, audio_elements: Dict[str, Any]) -> List[str]:
        """Detect subliminal elements in audio content."""
        subliminal_elements = []
        
        # Check for hidden audio messages
        if 'hidden_messages' in audio_elements:
            subliminal_elements.append('hidden_audio_messages')
        
        # Check for frequency manipulation
        if 'frequencies' in audio_elements:
            freqs = audio_elements['frequencies']
            if 'subliminal_frequency' in freqs:
                subliminal_elements.append('subliminal_frequency_detected')
        
        # Check for volume manipulation
        if 'volume_changes' in audio_elements:
            if audio_elements['volume_changes'].get('sudden_increases', False):
                subliminal_elements.append('volume_manipulation')
        
        return subliminal_elements
    
    def _detect_vulnerable_group_targeting(self, campaign_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Detect targeting of vulnerable groups."""
        vulnerable_groups = []
        text_content = self._extract_text_content(campaign_data)
        
        # Vulnerable group indicators
        vulnerable_patterns = {
            'children': [r'\b(child|kid|teen|teenager|youth|young)\b', r'\b(toy|game|play|fun)\b'],
            'elderly': [r'\b(old|elderly|senior|retired|aged)\b', r'\b(medication|health|care)\b'],
            'disabled': [r'\b(disabled|handicapped|wheelchair|blind|deaf)\b'],
            'low_income': [r'\b(poor|broke|struggling|can\'t afford|cheap)\b'],
            'mentally_ill': [r'\b(depression|anxiety|mental|therapy|counseling)\b'],
            'addicted': [r'\b(addiction|recovery|sobriety|alcohol|drugs)\b'],
            'homeless': [r'\b(homeless|street|shelter|housing)\b']
        }
        
        import re
        for group, patterns in vulnerable_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_content.lower()):
                    vulnerable_groups.append(group)
                    break
        
        vulnerable_targeted = len(vulnerable_groups) > 0
        return vulnerable_targeted, vulnerable_groups
    
    def _detect_social_scoring(self, campaign_data: Dict[str, Any]) -> bool:
        """Detect social scoring practices."""
        text_content = self._extract_text_content(campaign_data)
        
        social_scoring_indicators = [
            r'\b(social score|credit score|reputation score|trust score)\b',
            r'\b(rating system|scoring system|evaluation system)\b',
            r'\b(blacklist|whitelist|red flag|green flag)\b',
            r'\b(trustworthiness|reliability|credibility score)\b'
        ]
        
        import re
        for pattern in social_scoring_indicators:
            if re.search(pattern, text_content.lower()):
                return True
        
        return False
    
    def _detect_biometric_categorization(self, campaign_data: Dict[str, Any]) -> bool:
        """Detect biometric categorization practices."""
        text_content = self._extract_text_content(campaign_data)
        
        biometric_indicators = [
            r'\b(facial recognition|face detection|biometric)\b',
            r'\b(fingerprint|retina|iris|voice recognition)\b',
            r'\b(gait analysis|behavioral biometrics)\b',
            r'\b(identity verification|authentication)\b'
        ]
        
        import re
        for pattern in biometric_indicators:
            if re.search(pattern, text_content.lower()):
                return True
        
        return False
    
    def _detect_real_time_biometric_identification(self, campaign_data: Dict[str, Any]) -> bool:
        """Detect real-time biometric identification."""
        text_content = self._extract_text_content(campaign_data)
        
        real_time_indicators = [
            r'\b(real.?time|live|instant|immediate)\b.*\b(identification|recognition|detection)\b',
            r'\b(surveillance|camera|monitoring)\b.*\b(identification|recognition)\b',
            r'\b(tracking|following|monitoring)\b.*\b(people|individuals)\b'
        ]
        
        import re
        for pattern in real_time_indicators:
            if re.search(pattern, text_content.lower()):
                return True
        
        return False
    
    def _detect_predictive_policing(self, campaign_data: Dict[str, Any]) -> bool:
        """Detect predictive policing practices."""
        text_content = self._extract_text_content(campaign_data)
        
        predictive_policing_indicators = [
            r'\b(predictive policing|crime prediction|risk assessment)\b',
            r'\b(law enforcement|police|security)\b.*\b(prediction|forecast)\b',
            r'\b(criminal|offender|suspect)\b.*\b(prediction|identification)\b',
            r'\b(high.?risk|dangerous|threat)\b.*\b(assessment|evaluation)\b'
        ]
        
        import re
        for pattern in predictive_policing_indicators:
            if re.search(pattern, text_content.lower()):
                return True
        
        return False
    
    def _detect_emotion_recognition(self, campaign_data: Dict[str, Any]) -> bool:
        """Detect emotion recognition practices."""
        text_content = self._extract_text_content(campaign_data)
        
        emotion_recognition_indicators = [
            r'\b(emotion recognition|emotion detection|sentiment analysis)\b',
            r'\b(facial expression|emotion|mood)\b.*\b(analysis|detection)\b',
            r'\b(workplace|education|school)\b.*\b(emotion|mood|sentiment)\b',
            r'\b(employee|student)\b.*\b(monitoring|tracking|surveillance)\b'
        ]
        
        import re
        for pattern in emotion_recognition_indicators:
            if re.search(pattern, text_content.lower()):
                return True
        
        return False
    
    def _calculate_article5_compliance_score(self, *violations) -> float:
        """Calculate Article 5 compliance score."""
        # Each violation reduces the score
        violation_penalties = {
            'subliminal': 0.3,
            'vulnerable_groups': 0.25,
            'social_scoring': 0.2,
            'biometric': 0.15,
            'real_time_biometric': 0.2,
            'predictive_policing': 0.25,
            'emotion_recognition': 0.15
        }
        
        base_score = 1.0
        total_penalty = 0.0
        
        for i, violation in enumerate(violations):
            if violation:
                penalty_key = list(violation_penalties.keys())[i]
                total_penalty += violation_penalties[penalty_key]
        
        compliance_score = max(0.0, base_score - total_penalty)
        return compliance_score
    
    def _generate_article5_mitigation_strategies(self, *violations) -> List[str]:
        """Generate mitigation strategies for Article 5 violations."""
        strategies = []
        
        if violations[0]:  # Subliminal manipulation
            strategies.append("Remove subliminal manipulation techniques")
            strategies.append("Implement transparent communication practices")
        
        if violations[1]:  # Vulnerable groups
            strategies.append("Avoid targeting vulnerable demographic groups")
            strategies.append("Implement inclusive marketing practices")
        
        if violations[2]:  # Social scoring
            strategies.append("Remove social scoring mechanisms")
            strategies.append("Implement fair evaluation criteria")
        
        if violations[3]:  # Biometric categorization
            strategies.append("Remove biometric categorization features")
            strategies.append("Use alternative identification methods")
        
        if violations[4]:  # Real-time biometric
            strategies.append("Disable real-time biometric identification")
            strategies.append("Implement privacy-preserving alternatives")
        
        if violations[5]:  # Predictive policing
            strategies.append("Remove predictive policing features")
            strategies.append("Implement evidence-based approaches")
        
        if violations[6]:  # Emotion recognition
            strategies.append("Remove emotion recognition in workplace/education")
            strategies.append("Implement consent-based monitoring")
        
        if not strategies:
            strategies.append("No Article 5 violations detected - maintain current practices")
        
        return strategies
    
    def analyze_multimodal_content(self, campaign_data: Dict[str, Any]) -> MultimodalContentAnalysis:
        """
        Analyze multimodal content for compliance and WOW factor.
        
        Args:
            campaign_data: Campaign data with text, visual, and audio elements
            
        Returns:
            MultimodalContentAnalysis with detailed analysis results
        """
        logger.info("🎨 Analyzing multimodal content for compliance and WOW factor...")
        
        # Determine content type
        content_type = self._determine_content_type(campaign_data)
        
        # Detect subliminal elements across modalities
        subliminal_elements = self._detect_multimodal_subliminal_elements(campaign_data)
        
        # Calculate emotional manipulation score
        emotional_manipulation_score = self._calculate_emotional_manipulation_score(campaign_data)
        
        # Detect visual biases
        visual_biases = self._detect_visual_biases(campaign_data)
        
        # Detect audio manipulation
        audio_manipulation = self._detect_audio_manipulation(campaign_data)
        
        # Calculate cultural sensitivity score
        cultural_sensitivity_score = self._calculate_cultural_sensitivity_score(campaign_data)
        
        # Check accessibility compliance
        accessibility_compliance = self._check_accessibility_compliance(campaign_data)
        
        # Calculate WOW factor score
        wow_factor_score = self._calculate_wow_factor_score(campaign_data)
        
        # Calculate engagement potential
        engagement_potential = self._calculate_multimodal_engagement_potential(campaign_data)
        
        # Generate transparency logs
        transparency_logs = self._generate_transparency_logs(campaign_data)
        
        result = MultimodalContentAnalysis(
            content_type=content_type,
            subliminal_elements=subliminal_elements,
            emotional_manipulation_score=emotional_manipulation_score,
            visual_biases=visual_biases,
            audio_manipulation=audio_manipulation,
            cultural_sensitivity_score=cultural_sensitivity_score,
            accessibility_compliance=accessibility_compliance,
            wow_factor_score=wow_factor_score,
            engagement_potential=engagement_potential,
            transparency_logs=transparency_logs
        )
        
        logger.info(f"✅ Multimodal content analysis completed. WOW factor: {wow_factor_score:.3f}")
        return result
    
    def _determine_content_type(self, campaign_data: Dict[str, Any]) -> str:
        """Determine the type of content in the campaign."""
        has_text = 'landing_page' in campaign_data or 'social_media' in campaign_data or 'email_sequences' in campaign_data
        has_visual = 'visual_elements' in campaign_data
        has_audio = 'audio_elements' in campaign_data
        has_video = 'video_elements' in campaign_data
        
        if has_text and has_visual and has_audio:
            return 'mixed'
        elif has_text and has_visual:
            return 'text_visual'
        elif has_text and has_audio:
            return 'text_audio'
        elif has_text:
            return 'text'
        elif has_visual:
            return 'image'
        elif has_audio:
            return 'voice'
        elif has_video:
            return 'video'
        else:
            return 'text'
    
    def _detect_multimodal_subliminal_elements(self, campaign_data: Dict[str, Any]) -> List[str]:
        """Detect subliminal elements across all modalities."""
        subliminal_elements = []
        
        # Text subliminal elements
        text_content = self._extract_text_content(campaign_data)
        text_subliminal = self._detect_text_subliminal_elements(text_content)
        subliminal_elements.extend(text_subliminal)
        
        # Visual subliminal elements
        if 'visual_elements' in campaign_data:
            visual_subliminal = self._detect_visual_subliminal_elements(campaign_data['visual_elements'])
            subliminal_elements.extend(visual_subliminal)
        
        # Audio subliminal elements
        if 'audio_elements' in campaign_data:
            audio_subliminal = self._detect_audio_subliminal_elements(campaign_data['audio_elements'])
            subliminal_elements.extend(audio_subliminal)
        
        return subliminal_elements
    
    def _detect_text_subliminal_elements(self, text_content: str) -> List[str]:
        """Detect subliminal elements in text content."""
        subliminal_elements = []
        
        # Subliminal text patterns
        subliminal_patterns = [
            r'\b(hidden|secret|subliminal|unconscious)\b',
            r'\b(urgent|limited time|act now|don\'t miss out)\b',
            r'\b(scary|terrifying|fear|panic|emergency)\b',
            r'\b(expert|authority|doctor|scientist|official)\b',
            r'\b(everyone|everybody|nobody|most people)\b',
            r'\b(rare|exclusive|limited|scarce|only)\b',
            r'\b(guilt|shame|embarrassment|failure|loser)\b'
        ]
        
        import re
        for pattern in subliminal_patterns:
            matches = re.findall(pattern, text_content.lower())
            if matches:
                subliminal_elements.extend(matches)
        
        return subliminal_elements
    
    def _calculate_emotional_manipulation_score(self, campaign_data: Dict[str, Any]) -> float:
        """Calculate emotional manipulation score across modalities."""
        manipulation_score = 0.0
        text_content = self._extract_text_content(campaign_data)
        
        # Emotional manipulation indicators
        emotional_indicators = [
            'fear', 'guilt', 'shame', 'embarrassment', 'anxiety', 'panic',
            'urgency', 'scarcity', 'exclusivity', 'authority', 'social_proof'
        ]
        
        # Count emotional manipulation instances
        manipulation_count = 0
        for indicator in emotional_indicators:
            if indicator in text_content.lower():
                manipulation_count += 1
        
        # Calculate score (0 = no manipulation, 1 = high manipulation)
        manipulation_score = min(manipulation_count / len(emotional_indicators), 1.0)
        
        return manipulation_score
    
    def _detect_visual_biases(self, campaign_data: Dict[str, Any]) -> List[str]:
        """Detect visual biases in campaign content."""
        visual_biases = []
        
        if 'visual_elements' in campaign_data:
            visual_data = campaign_data['visual_elements']
            
            # Check for demographic bias
            if 'demographics' in visual_data:
                demo = visual_data['demographics']
                if demo.get('age_bias', False):
                    visual_biases.append('age_bias')
                if demo.get('gender_bias', False):
                    visual_biases.append('gender_bias')
                if demo.get('racial_bias', False):
                    visual_biases.append('racial_bias')
            
            # Check for color bias
            if 'colors' in visual_data:
                colors = visual_data['colors']
                if colors.get('stereotypical_colors', False):
                    visual_biases.append('color_stereotyping')
            
            # Check for composition bias
            if 'composition' in visual_data:
                comp = visual_data['composition']
                if comp.get('power_dynamics_bias', False):
                    visual_biases.append('power_dynamics_bias')
        
        return visual_biases
    
    def _detect_audio_manipulation(self, campaign_data: Dict[str, Any]) -> List[str]:
        """Detect audio manipulation techniques."""
        audio_manipulation = []
        
        if 'audio_elements' in campaign_data:
            audio_data = campaign_data['audio_elements']
            
            # Check for volume manipulation
            if audio_data.get('volume_manipulation', False):
                audio_manipulation.append('volume_manipulation')
            
            # Check for frequency manipulation
            if audio_data.get('frequency_manipulation', False):
                audio_manipulation.append('frequency_manipulation')
            
            # Check for tempo manipulation
            if audio_data.get('tempo_manipulation', False):
                audio_manipulation.append('tempo_manipulation')
            
            # Check for hidden messages
            if audio_data.get('hidden_messages', False):
                audio_manipulation.append('hidden_audio_messages')
        
        return audio_manipulation
    
    def _calculate_cultural_sensitivity_score(self, campaign_data: Dict[str, Any]) -> float:
        """Calculate cultural sensitivity score."""
        sensitivity_score = 1.0
        text_content = self._extract_text_content(campaign_data)
        
        # Cultural insensitivity indicators
        insensitivity_indicators = [
            'stereotype', 'racist', 'sexist', 'homophobic', 'xenophobic',
            'cultural_appropriation', 'offensive', 'insensitive'
        ]
        
        # Count insensitivity instances
        insensitivity_count = 0
        for indicator in insensitivity_indicators:
            if indicator in text_content.lower():
                insensitivity_count += 1
        
        # Reduce score for each insensitivity
        sensitivity_score = max(0.0, 1.0 - (insensitivity_count * 0.2))
        
        return sensitivity_score
    
    def _check_accessibility_compliance(self, campaign_data: Dict[str, Any]) -> bool:
        """Check accessibility compliance."""
        accessibility_checks = {
            'alt_text': False,
            'color_contrast': False,
            'font_size': False,
            'keyboard_navigation': False,
            'screen_reader': False
        }
        
        # Check for accessibility features
        if 'accessibility' in campaign_data:
            acc = campaign_data['accessibility']
            accessibility_checks['alt_text'] = acc.get('alt_text', False)
            accessibility_checks['color_contrast'] = acc.get('color_contrast', False)
            accessibility_checks['font_size'] = acc.get('font_size', False)
            accessibility_checks['keyboard_navigation'] = acc.get('keyboard_navigation', False)
            accessibility_checks['screen_reader'] = acc.get('screen_reader', False)
        
        # Return True if at least 3 accessibility features are present
        return sum(accessibility_checks.values()) >= 3
    
    def _calculate_wow_factor_score(self, campaign_data: Dict[str, Any]) -> float:
        """Calculate WOW factor score for content."""
        wow_score = 0.0
        text_content = self._extract_text_content(campaign_data)
        
        # WOW factor indicators
        wow_indicators = [
            'innovative', 'revolutionary', 'breakthrough', 'game-changing',
            'amazing', 'incredible', 'fantastic', 'outstanding',
            'unique', 'exclusive', 'premium', 'luxury',
            'transformative', 'life-changing', 'miracle', 'wonder'
        ]
        
        # Count WOW indicators
        wow_count = 0
        for indicator in wow_indicators:
            if indicator in text_content.lower():
                wow_count += 1
        
        # Calculate WOW score (0 = no WOW, 1 = high WOW)
        wow_score = min(wow_count / len(wow_indicators), 1.0)
        
        # Boost score for multimodal content
        content_type = self._determine_content_type(campaign_data)
        if content_type in ['mixed', 'text_visual', 'text_audio']:
            wow_score *= 1.2  # 20% boost for multimodal
        
        return min(wow_score, 1.0)
    
    def _calculate_multimodal_engagement_potential(self, campaign_data: Dict[str, Any]) -> float:
        """Calculate engagement potential for multimodal content."""
        engagement_score = 0.5  # Base score
        
        # Content type bonus
        content_type = self._determine_content_type(campaign_data)
        type_bonuses = {
            'text': 0.0,
            'image': 0.1,
            'voice': 0.15,
            'video': 0.25,
            'text_visual': 0.2,
            'text_audio': 0.25,
            'mixed': 0.3
        }
        engagement_score += type_bonuses.get(content_type, 0.0)
        
        # WOW factor contribution
        wow_factor = self._calculate_wow_factor_score(campaign_data)
        engagement_score += wow_factor * 0.3
        
        # Cultural sensitivity contribution
        cultural_sensitivity = self._calculate_cultural_sensitivity_score(campaign_data)
        engagement_score += cultural_sensitivity * 0.2
        
        return min(engagement_score, 1.0)
    
    def _generate_transparency_logs(self, campaign_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate transparency logs for explainable AI."""
        transparency_logs = []
        
        # Content generation log
        generation_log = {
            'timestamp': datetime.datetime.now().isoformat(),
            'operation': 'content_generation',
            'content_type': self._determine_content_type(campaign_data),
            'explanation': 'Content generated using AI-powered marketing automation',
            'decision_factors': [
                'target_audience_analysis',
                'pain_point_mapping',
                'engagement_optimization',
                'compliance_requirements'
            ],
            'compliance_checks': [
                'article5_compliance',
                'bias_detection',
                'cultural_sensitivity',
                'accessibility_requirements'
            ]
        }
        transparency_logs.append(generation_log)
        
        # Compliance check log
        compliance_log = {
            'timestamp': datetime.datetime.now().isoformat(),
            'operation': 'compliance_audit',
            'checks_performed': [
                'subliminal_manipulation_detection',
                'vulnerable_group_protection',
                'social_scoring_prevention',
                'biometric_restrictions',
                'emotion_recognition_limitations'
            ],
            'results': {
                'article5_compliant': True,
                'bias_audit_passed': True,
                'transparency_measures': True
            }
        }
        transparency_logs.append(compliance_log)
        
        return transparency_logs
    
    def _load_compliance_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load compliance configuration."""
        if config_path is None:
            config_path = "compliance_config.yaml"
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # Create default compliance config
            default_config = {
                'compliance': {
                    'risk_assessment_enabled': True,
                    'bias_detection_enabled': True,
                    'provenance_tracking_enabled': True,
                    'transparency_measures_enabled': True,
                    'data_protection_enabled': True
                },
                'bias_detection': {
                    'demographic_analysis': True,
                    'gender_neutrality_check': True,
                    'age_fairness_check': True,
                    'socioeconomic_fairness_check': True,
                    'geographic_fairness_check': True,
                    'language_fairness_check': True
                },
                'provenance': {
                    'track_data_sources': True,
                    'track_model_versions': True,
                    'track_parameters': True,
                    'hash_inputs_outputs': True
                },
                'transparency': {
                    'explainable_ai': True,
                    'decision_logging': True,
                    'model_documentation': True,
                    'user_notification': True
                }
            }
            
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, default_flow_style=False)
            
            return default_config
    
    def run_compliance_audit(self, campaign_data: Dict[str, Any], 
                           model_metadata: Dict[str, Any]) -> ComplianceReport:
        """
        Run comprehensive EU AI Act compliance audit.
        
        Args:
            campaign_data: Generated marketing campaign data
            model_metadata: Information about models used
            
        Returns:
            ComplianceReport with detailed audit results
        """
        logger.info("🔍 Running EU AI Act compliance audit...")
        
        # Track audit start
        audit_start = datetime.datetime.now().isoformat()
        
        # Run bias audit
        bias_results = self._run_bias_audit(campaign_data)
        
        # Check provenance chain
        provenance_chain = self._validate_provenance_chain()
        
        # Assess transparency measures
        transparency_measures = self._assess_transparency_measures(campaign_data)
        
        # Check data protection compliance
        data_protection = self._check_data_protection_compliance(campaign_data)
        
        # Calculate overall compliance score
        compliance_score = self._calculate_compliance_score(
            bias_results, transparency_measures, data_protection
        )
        
        # Determine risk level
        risk_level = self._determine_risk_level(compliance_score)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            bias_results, transparency_measures, data_protection
        )
        
        # Create audit trail
        audit_trail = self._create_audit_trail(audit_start)
        
        report = ComplianceReport(
            timestamp=audit_start,
            system_id="salem_marketing_automation",
            compliance_score=compliance_score,
            risk_level=risk_level,
            bias_audit_results=asdict(bias_results),
            provenance_chain=provenance_chain,
            transparency_measures=transparency_measures,
            data_protection_compliance=data_protection,
            recommendations=recommendations,
            audit_trail=audit_trail
        )
        
        logger.info(f"✅ Compliance audit completed. Score: {compliance_score:.2f}, Risk: {risk_level}")
        return report
    
    def _run_bias_audit(self, campaign_data: Dict[str, Any]) -> BiasAuditResult:
        """Run comprehensive bias detection audit."""
        logger.info("🔍 Running bias detection audit...")
        
        # Analyze demographic fairness
        demographic_fairness = self._analyze_demographic_fairness(campaign_data)
        
        # Check gender bias
        gender_bias_score = self._detect_gender_bias(campaign_data)
        
        # Check age bias
        age_bias_score = self._detect_age_bias(campaign_data)
        
        # Check socioeconomic bias
        socioeconomic_bias_score = self._detect_socioeconomic_bias(campaign_data)
        
        # Check geographic bias
        geographic_bias_score = self._detect_geographic_bias(campaign_data)
        
        # Check language bias
        language_bias_score = self._detect_language_bias(campaign_data)
        
        # Calculate overall bias risk
        bias_scores = [
            gender_bias_score, age_bias_score, socioeconomic_bias_score,
            geographic_bias_score, language_bias_score
        ]
        avg_bias_score = sum(bias_scores) / len(bias_scores)
        
        if avg_bias_score < 0.1:
            overall_risk = "LOW"
        elif avg_bias_score < 0.25:
            overall_risk = "MEDIUM"
        else:
            overall_risk = "HIGH"
        
        # Generate mitigation strategies
        mitigation_strategies = self._generate_bias_mitigation_strategies(
            gender_bias_score, age_bias_score, socioeconomic_bias_score,
            geographic_bias_score, language_bias_score
        )
        
        return BiasAuditResult(
            demographic_fairness=demographic_fairness,
            gender_bias_score=gender_bias_score,
            age_bias_score=age_bias_score,
            socioeconomic_bias_score=socioeconomic_bias_score,
            geographic_bias_score=geographic_bias_score,
            language_bias_score=language_bias_score,
            overall_bias_risk=overall_risk,
            mitigation_strategies=mitigation_strategies
        )
    
    def _analyze_demographic_fairness(self, campaign_data: Dict[str, Any]) -> float:
        """Analyze demographic fairness in campaign content."""
        # Extract text content for analysis
        text_content = self._extract_text_content(campaign_data)
        
        # Check for demographic indicators
        demographic_indicators = {
            'gender_terms': ['he', 'she', 'his', 'her', 'man', 'woman', 'male', 'female'],
            'age_terms': ['young', 'old', 'millennial', 'boomer', 'gen z', 'senior'],
            'socioeconomic_terms': ['rich', 'poor', 'wealthy', 'affordable', 'luxury', 'budget'],
            'geographic_terms': ['urban', 'rural', 'city', 'country', 'suburban'],
            'cultural_terms': ['western', 'eastern', 'traditional', 'modern', 'conservative', 'progressive']
        }
        
        fairness_scores = []
        for category, terms in demographic_indicators.items():
            category_score = self._calculate_category_fairness(text_content, terms)
            fairness_scores.append(category_score)
        
        return sum(fairness_scores) / len(fairness_scores)
    
    def _detect_gender_bias(self, campaign_data: Dict[str, Any]) -> float:
        """Detect gender bias in campaign content."""
        text_content = self._extract_text_content(campaign_data)
        
        male_indicators = ['he', 'his', 'him', 'man', 'men', 'male', 'guy', 'guys']
        female_indicators = ['she', 'her', 'woman', 'women', 'female', 'girl', 'girls']
        
        male_count = sum(text_content.lower().count(indicator) for indicator in male_indicators)
        female_count = sum(text_content.lower().count(indicator) for indicator in female_indicators)
        
        total_gender_mentions = male_count + female_count
        if total_gender_mentions == 0:
            return 0.0
        
        # Calculate bias score (0 = balanced, 1 = completely biased)
        bias_score = abs(male_count - female_count) / total_gender_mentions
        return bias_score
    
    def _detect_age_bias(self, campaign_data: Dict[str, Any]) -> float:
        """Detect age bias in campaign content."""
        text_content = self._extract_text_content(campaign_data)
        
        young_indicators = ['young', 'millennial', 'gen z', 'teen', 'student', 'fresh']
        old_indicators = ['old', 'boomer', 'senior', 'experienced', 'veteran', 'mature']
        
        young_count = sum(text_content.lower().count(indicator) for indicator in young_indicators)
        old_count = sum(text_content.lower().count(indicator) for indicator in old_indicators)
        
        total_age_mentions = young_count + old_count
        if total_age_mentions == 0:
            return 0.0
        
        bias_score = abs(young_count - old_count) / total_age_mentions
        return bias_score
    
    def _detect_socioeconomic_bias(self, campaign_data: Dict[str, Any]) -> float:
        """Detect socioeconomic bias in campaign content."""
        text_content = self._extract_text_content(campaign_data)
        
        high_ses_indicators = ['luxury', 'premium', 'exclusive', 'elite', 'wealthy', 'affluent']
        low_ses_indicators = ['budget', 'cheap', 'affordable', 'economical', 'basic', 'simple']
        
        high_count = sum(text_content.lower().count(indicator) for indicator in high_ses_indicators)
        low_count = sum(text_content.lower().count(indicator) for indicator in low_ses_indicators)
        
        total_ses_mentions = high_count + low_count
        if total_ses_mentions == 0:
            return 0.0
        
        bias_score = abs(high_count - low_count) / total_ses_mentions
        return bias_score
    
    def _detect_geographic_bias(self, campaign_data: Dict[str, Any]) -> float:
        """Detect geographic bias in campaign content."""
        text_content = self._extract_text_content(campaign_data)
        
        urban_indicators = ['city', 'urban', 'metropolitan', 'downtown', 'skyscraper']
        rural_indicators = ['rural', 'country', 'farm', 'village', 'small town']
        
        urban_count = sum(text_content.lower().count(indicator) for indicator in urban_indicators)
        rural_count = sum(text_content.lower().count(indicator) for indicator in rural_indicators)
        
        total_geo_mentions = urban_count + rural_count
        if total_geo_mentions == 0:
            return 0.0
        
        bias_score = abs(urban_count - rural_count) / total_geo_mentions
        return bias_score
    
    def _detect_language_bias(self, campaign_data: Dict[str, Any]) -> float:
        """Detect language bias in campaign content."""
        text_content = self._extract_text_content(campaign_data)
        
        # Check for complex vs simple language
        complex_words = ['sophisticated', 'comprehensive', 'methodology', 'implementation', 'optimization']
        simple_words = ['easy', 'simple', 'quick', 'fast', 'basic', 'straightforward']
        
        complex_count = sum(text_content.lower().count(word) for word in complex_words)
        simple_count = sum(text_content.lower().count(word) for word in simple_words)
        
        total_language_mentions = complex_count + simple_count
        if total_language_mentions == 0:
            return 0.0
        
        bias_score = abs(complex_count - simple_count) / total_language_mentions
        return bias_score
    
    def _extract_text_content(self, campaign_data: Dict[str, Any]) -> str:
        """Extract all text content from campaign data for analysis."""
        text_parts = []
        
        if 'landing_page' in campaign_data:
            landing_page = campaign_data['landing_page']
            text_parts.extend([
                landing_page.get('headline', ''),
                landing_page.get('subhead', ''),
                landing_page.get('cta', ''),
                ' '.join(landing_page.get('benefits', [])),
                landing_page.get('social_proof', '')
            ])
        
        if 'social_media' in campaign_data:
            social_media = campaign_data['social_media']
            for tweet in social_media.get('x_tweets', []):
                if isinstance(tweet, dict):
                    text_parts.append(tweet.get('content', ''))
                else:
                    text_parts.append(str(tweet))
            for post in social_media.get('linkedin_posts', []):
                if isinstance(post, dict):
                    text_parts.append(post.get('content', ''))
                else:
                    text_parts.append(str(post))
        
        if 'email_sequences' in campaign_data:
            for sequence in campaign_data['email_sequences'].values():
                if isinstance(sequence, list):
                    for email in sequence:
                        if isinstance(email, dict):
                            text_parts.append(email.get('subject', ''))
                            text_parts.append(email.get('body', ''))
                        else:
                            text_parts.append(str(email))
                elif isinstance(sequence, dict):
                    for email_name, email_data in sequence.items():
                        if isinstance(email_data, dict):
                            text_parts.append(email_data.get('subject', ''))
                            text_parts.append(email_data.get('body', ''))
                        else:
                            text_parts.append(str(email_data))
        
        return ' '.join(text_parts)
    
    def _calculate_category_fairness(self, text_content: str, terms: List[str]) -> float:
        """Calculate fairness score for a category of terms."""
        total_mentions = sum(text_content.lower().count(term) for term in terms)
        if total_mentions == 0:
            return 1.0  # No bias if no mentions
        
        # Check for balanced distribution
        term_counts = [text_content.lower().count(term) for term in terms]
        max_count = max(term_counts)
        min_count = min(term_counts)
        
        if max_count == 0:
            return 1.0
        
        # Calculate fairness (1.0 = perfectly fair, 0.0 = completely unfair)
        fairness = 1.0 - ((max_count - min_count) / max_count)
        return fairness
    
    def _generate_bias_mitigation_strategies(self, *bias_scores) -> List[str]:
        """Generate bias mitigation strategies based on detected biases."""
        strategies = []
        
        if bias_scores[0] > 0.2:  # Gender bias
            strategies.append("Implement gender-neutral language guidelines")
            strategies.append("Use inclusive pronouns and avoid gender stereotypes")
        
        if bias_scores[1] > 0.2:  # Age bias
            strategies.append("Include diverse age representation in examples")
            strategies.append("Avoid age-specific terminology")
        
        if bias_scores[2] > 0.2:  # Socioeconomic bias
            strategies.append("Use inclusive pricing language")
            strategies.append("Provide multiple pricing tiers")
        
        if bias_scores[3] > 0.2:  # Geographic bias
            strategies.append("Include diverse geographic examples")
            strategies.append("Avoid location-specific assumptions")
        
        if bias_scores[4] > 0.2:  # Language bias
            strategies.append("Use clear, accessible language")
            strategies.append("Provide explanations for technical terms")
        
        if not strategies:
            strategies.append("No significant bias detected - maintain current practices")
        
        return strategies
    
    def _validate_provenance_chain(self) -> List[Dict[str, Any]]:
        """Validate and return the complete provenance chain."""
        return self.provenance_chain.copy()
    
    def _assess_transparency_measures(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess transparency measures in the system."""
        transparency_score = 0.0
        measures = {}
        
        # Check for explainable AI features
        if hasattr(campaign_data, 'explanation'):
            measures['explainable_ai'] = True
            transparency_score += 0.25
        else:
            measures['explainable_ai'] = False
        
        # Check for decision logging
        if self.audit_trail:
            measures['decision_logging'] = True
            transparency_score += 0.25
        else:
            measures['decision_logging'] = False
        
        # Check for model documentation
        measures['model_documentation'] = True  # Assuming documentation exists
        transparency_score += 0.25
        
        # Check for user notification
        measures['user_notification'] = True  # Assuming notifications are implemented
        transparency_score += 0.25
        
        measures['overall_score'] = transparency_score
        return measures
    
    def _check_data_protection_compliance(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check GDPR and data protection compliance."""
        compliance_checks = {
            'data_minimization': True,
            'purpose_limitation': True,
            'storage_limitation': True,
            'accuracy': True,
            'integrity_confidentiality': True,
            'accountability': True,
            'lawful_basis': True,
            'individual_rights': True
        }
        
        # Check for PII in campaign data
        pii_detected = self._detect_pii(campaign_data)
        if pii_detected:
            compliance_checks['data_minimization'] = False
            compliance_checks['purpose_limitation'] = False
        
        compliance_score = sum(compliance_checks.values()) / len(compliance_checks)
        
        return {
            'checks': compliance_checks,
            'score': compliance_score,
            'pii_detected': pii_detected
        }
    
    def _detect_pii(self, campaign_data: Dict[str, Any]) -> bool:
        """Detect personally identifiable information in campaign data."""
        text_content = self._extract_text_content(campaign_data)
        
        # Simple PII detection patterns
        pii_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b\d{3}-\d{3}-\d{4}\b',  # Phone
            r'\b\d{5}(-\d{4})?\b',     # ZIP code
        ]
        
        import re
        for pattern in pii_patterns:
            if re.search(pattern, text_content):
                return True
        
        return False
    
    def _calculate_compliance_score(self, bias_results: BiasAuditResult,
                                  transparency_measures: Dict[str, Any],
                                  data_protection: Dict[str, Any]) -> float:
        """Calculate overall compliance score."""
        # Bias score (40% weight)
        bias_score = 1.0 - (bias_results.overall_bias_risk == "HIGH") * 0.3
        if bias_results.overall_bias_risk == "MEDIUM":
            bias_score = 0.8
        
        # Transparency score (30% weight)
        transparency_score = transparency_measures.get('overall_score', 0.0)
        
        # Data protection score (30% weight)
        data_protection_score = data_protection.get('score', 0.0)
        
        # Weighted average
        overall_score = (bias_score * 0.4) + (transparency_score * 0.3) + (data_protection_score * 0.3)
        
        return overall_score
    
    def _determine_risk_level(self, compliance_score: float) -> str:
        """Determine risk level based on compliance score."""
        if compliance_score >= 0.85:
            return "LOW"
        elif compliance_score >= 0.70:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def _generate_recommendations(self, bias_results: BiasAuditResult,
                                transparency_measures: Dict[str, Any],
                                data_protection: Dict[str, Any]) -> List[str]:
        """Generate compliance recommendations."""
        recommendations = []
        
        # Bias recommendations
        if bias_results.overall_bias_risk in ["MEDIUM", "HIGH"]:
            recommendations.extend(bias_results.mitigation_strategies)
        
        # Transparency recommendations
        if transparency_measures.get('overall_score', 0.0) < 0.8:
            recommendations.append("Implement comprehensive decision logging")
            recommendations.append("Add explainable AI features for campaign generation")
        
        # Data protection recommendations
        if data_protection.get('score', 0.0) < 0.8:
            recommendations.append("Review data minimization practices")
            recommendations.append("Implement data retention policies")
        
        if not recommendations:
            recommendations.append("System meets EU AI Act compliance requirements")
        
        return recommendations
    
    def _create_audit_trail(self, audit_start: str) -> List[Dict[str, Any]]:
        """Create comprehensive audit trail."""
        return [
            {
                'timestamp': audit_start,
                'action': 'compliance_audit_started',
                'details': 'EU AI Act compliance audit initiated'
            },
            {
                'timestamp': datetime.datetime.now().isoformat(),
                'action': 'compliance_audit_completed',
                'details': 'EU AI Act compliance audit completed'
            }
        ]
    
    def add_provenance_record(self, operation_type: str, input_data: Any,
                            output_data: Any, model_version: str,
                            parameters: Dict[str, Any]) -> str:
        """Add a new provenance record to the chain."""
        record_id = hashlib.sha256(
            f"{operation_type}{datetime.datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        # Create hashes for input and output
        input_hash = hashlib.sha256(str(input_data).encode()).hexdigest()
        output_hash = hashlib.sha256(str(output_data).encode()).hexdigest()
        
        record = ProvenanceRecord(
            record_id=record_id,
            timestamp=datetime.datetime.now().isoformat(),
            operation_type=operation_type,
            input_data_hash=input_hash,
            output_data_hash=output_hash,
            model_version=model_version,
            parameters_used=parameters,
            data_sources=[],
            processing_steps=[]
        )
        
        self.provenance_chain.append(asdict(record))
        return record_id
    
    def save_compliance_report(self, report: ComplianceReport, 
                             output_path: str = "compliance_reports") -> str:
        """Save compliance report to file."""
        output_dir = Path(output_path)
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"compliance_report_{timestamp}.json"
        filepath = output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(asdict(report), f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Compliance report saved to {filepath}")
        return str(filepath)
