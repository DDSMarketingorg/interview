"""
Tests for Safety Detection
===========================
"""

import pytest
from src.ai.agent import SafetyDetector, EscalationLevel


@pytest.fixture
def detector():
    return SafetyDetector()


class TestEmergencyDetection:
    """Test emergency keyword detection."""
    
    def test_detects_breathing_difficulty(self, detector):
        result = detector.check_input("I can't breathe properly")
        
        assert result.needs_escalation == True
        assert result.level == EscalationLevel.EMERGENCY
        assert "can't breathe" in result.detected_keywords
    
    def test_detects_swelling(self, detector):
        result = detector.check_input("My face is swelling up")
        
        assert result.needs_escalation == True
        assert result.level == EscalationLevel.EMERGENCY
    
    def test_detects_trauma(self, detector):
        result = detector.check_input("I had an accident and knocked out tooth")
        
        assert result.needs_escalation == True
        assert result.level == EscalationLevel.EMERGENCY
        assert "knocked out tooth" in result.detected_keywords
    
    def test_detects_fever(self, detector):
        result = detector.check_input("I have a fever and my jaw is swollen")
        
        assert result.needs_escalation == True
        assert result.level == EscalationLevel.EMERGENCY


class TestHighPainDetection:
    """Test high pain level detection."""
    
    def test_detects_10_out_of_10(self, detector):
        result = detector.check_input("My pain is 10 out of 10")
        
        assert result.needs_escalation == True
        assert result.level == EscalationLevel.URGENT
        assert "10 out of 10" in result.detected_keywords
    
    def test_detects_9_out_of_10(self, detector):
        result = detector.check_input("It's a 9/10 pain")
        
        assert result.needs_escalation == True
        assert result.level == EscalationLevel.URGENT
    
    def test_detects_unbearable_pain(self, detector):
        result = detector.check_input("The pain is unbearable")
        
        assert result.needs_escalation == True
        assert result.level == EscalationLevel.URGENT
    
    def test_moderate_pain_no_escalation(self, detector):
        result = detector.check_input("My pain is about 5 out of 10")
        
        assert result.needs_escalation == False
        assert result.level == EscalationLevel.NONE


class TestTransferRequests:
    """Test explicit transfer request detection."""
    
    def test_detects_speak_to_human(self, detector):
        result = detector.check_input("Can I speak to a human please?")
        
        assert result.needs_escalation == True
        assert result.level == EscalationLevel.ROUTINE
    
    def test_detects_talk_to_dentist(self, detector):
        result = detector.check_input("I need to talk to the dentist")
        
        assert result.needs_escalation == True
        assert result.level == EscalationLevel.ROUTINE
    
    def test_detects_transfer_request(self, detector):
        result = detector.check_input("Please transfer me to a real person")
        
        assert result.needs_escalation == True
        assert result.level == EscalationLevel.ROUTINE


class TestNormalConversation:
    """Test that normal conversation doesn't trigger escalation."""
    
    def test_normal_pain_level(self, detector):
        result = detector.check_input("I have a mild toothache, maybe a 3 out of 10")
        
        assert result.needs_escalation == False
    
    def test_insurance_question(self, detector):
        result = detector.check_input("Yes, I have Sun Life insurance")
        
        assert result.needs_escalation == False
    
    def test_appointment_request(self, detector):
        result = detector.check_input("I'd like to schedule an appointment for next week")
        
        assert result.needs_escalation == False
    
    def test_greeting(self, detector):
        result = detector.check_input("Hi, I'm calling about a dental checkup")
        
        assert result.needs_escalation == False


class TestCombinedSymptoms:
    """Test dangerous symptom combination detection."""
    
    def test_swelling_with_fever(self, detector):
        result = detector.check_combined_symptoms(["swelling", "fever"])
        
        assert result.needs_escalation == True
        assert result.level == EscalationLevel.EMERGENCY
        assert "Potential dental infection" in result.reason
    
    def test_breathing_difficulty(self, detector):
        result = detector.check_combined_symptoms(["can't breathe"])
        
        assert result.needs_escalation == True
        assert result.level == EscalationLevel.EMERGENCY
    
    def test_single_symptom_no_escalation(self, detector):
        result = detector.check_combined_symptoms(["toothache"])
        
        assert result.needs_escalation == False
