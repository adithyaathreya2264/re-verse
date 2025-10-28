"""
Enumeration types for RE-VERSE application.
Provides type safety and validation for job-related fields.
"""
from enum import Enum


class JobStatus(str, Enum):
    """
    Job processing status enumeration.
    Inherits from str for JSON serialization compatibility.
    """
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    
    def __str__(self):
        return self.value
    
    @classmethod
    def get_terminal_statuses(cls):
        """Return statuses that indicate job completion (success or failure)."""
        return [cls.COMPLETED, cls.FAILED]
    
    @classmethod
    def is_terminal(cls, status: str) -> bool:
        """Check if a status is terminal (job finished processing)."""
        return status in [cls.COMPLETED.value, cls.FAILED.value]


class StyleType(str, Enum):
    """
    Conversation style enumeration for audio generation.
    Defines the tone and format of the generated dialogue.
    """
    STUDENT_PROFESSOR = "Student-Professor"
    CRITIQUE = "Critique"
    DEBATE = "Debate"
    INTERVIEW = "Interview"
    STORY_TELLING = "Story-Telling"
    CASUAL_DISCUSSION = "Casual-Discussion"
    
    def __str__(self):
        return self.value
    
    def get_system_prompt_modifier(self) -> str:
        """
        Get the system prompt text that describes this style.
        Used in Gemini API prompts.
        """
        style_prompts = {
            self.STUDENT_PROFESSOR: "Create a dialogue between a curious student asking questions and a knowledgeable professor explaining concepts in detail.",
            self.CRITIQUE: "Create a critical analysis dialogue where two experts debate and critique the content from different perspectives.",
            self.DEBATE: "Create a formal debate between two speakers with opposing viewpoints, presenting arguments and counterarguments.",
            self.INTERVIEW: "Create an interview-style conversation where an interviewer asks insightful questions and an expert provides detailed answers.",
            self.STORY_TELLING: "Create a narrative storytelling conversation where speakers weave the content into an engaging story.",
            self.CASUAL_DISCUSSION: "Create a casual, friendly discussion between two speakers exploring the content in a relaxed manner."
        }
        return style_prompts.get(self, style_prompts[self.STUDENT_PROFESSOR])


class DurationType(str, Enum):
    """
    Duration preference enumeration for audio length control.
    Maps to token limits for LLM generation.
    """
    SHORTER = "SHORTER"
    MEDIUM = "MEDIUM"
    LONGER = "LONGER"
    
    def __str__(self):
        return self.value
    
    def get_token_limit(self) -> int:
        """
        Get the max_output_tokens value for this duration.
        These values are overridden by settings if configured.
        """
        token_map = {
            self.SHORTER: 2000,
            self.MEDIUM: 4000,
            self.LONGER: 8000
        }
        return token_map.get(self, 4000)
    
    def get_estimated_minutes(self) -> str:
        """Get estimated audio duration in minutes."""
        duration_map = {
            self.SHORTER: "5-8 minutes",
            self.MEDIUM: "10-15 minutes",
            self.LONGER: "20-30 minutes"
        }
        return duration_map.get(self, "10-15 minutes")


class FileType(str, Enum):
    """Supported file types for upload."""
    PDF = "application/pdf"
    
    def __str__(self):
        return self.value
