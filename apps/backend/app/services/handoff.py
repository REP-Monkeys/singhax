"""Human handoff service for customer service escalation."""

from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from uuid import UUID, uuid4

from app.models.user import User
from app.models.chat_history import ChatHistory


class HandoffService:
    """Service for managing human handoff requests."""
    
    def __init__(self):
        # TODO: Integrate with real customer service system
        self.handoff_queue = []  # Mock queue
    
    def create_handoff_request(
        self,
        db: Session,
        user_id: UUID,
        reason: str,
        conversation_summary: str,
        priority: str = "normal"
    ) -> Dict[str, Any]:
        """Create a human handoff request."""
        
        # Get user information
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Get recent chat history
        recent_chats = db.query(ChatHistory).filter(
            ChatHistory.user_id == user_id
        ).order_by(ChatHistory.created_at.desc()).limit(10).all()
        
        # Create handoff request
        handoff_request = {
            "id": str(uuid4()),
            "user_id": str(user_id),
            "user_email": user.email,
            "user_name": user.name,
            "reason": reason,
            "conversation_summary": conversation_summary,
            "priority": priority,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "chat_history": [
                {
                    "role": chat.role,
                    "message": chat.message,
                    "timestamp": chat.created_at.isoformat()
                }
                for chat in recent_chats
            ]
        }
        
        # Add to queue (mock implementation)
        self.handoff_queue.append(handoff_request)
        
        # TODO: Send notification to customer service team
        # TODO: Create ticket in external system
        
        return handoff_request
    
    def get_handoff_requests(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get handoff requests from the queue."""
        
        requests = self.handoff_queue
        
        if status:
            requests = [req for req in requests if req["status"] == status]
        
        if priority:
            requests = [req for req in requests if req["priority"] == priority]
        
        return requests
    
    def get_pending_handoffs(self, db: Session) -> List[Dict[str, Any]]:
        """Get pending handoff requests."""
        return self.get_handoff_requests(status="pending")
    
    def update_handoff_status(
        self,
        db: Session,
        request_id: str,
        status: str,
        assigned_to: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Update the status of a handoff request."""
        
        for request in self.handoff_queue:
            if request["id"] == request_id:
                request["status"] = status
                if assigned_to:
                    request["assigned_to"] = assigned_to
                if notes:
                    request["notes"] = notes
                request["updated_at"] = datetime.utcnow().isoformat()
                return request
        
        return None
    
    def generate_conversation_summary(
        self,
        db: Session,
        user_id: UUID,
        max_messages: int = 20
    ) -> str:
        """Generate a summary of the user's conversation."""
        
        # Get recent chat history
        recent_chats = db.query(ChatHistory).filter(
            ChatHistory.user_id == user_id
        ).order_by(ChatHistory.created_at.desc()).limit(max_messages).all()
        
        if not recent_chats:
            return "No conversation history available."
        
        # Build summary
        summary_parts = []
        
        # Get user messages
        user_messages = [chat for chat in recent_chats if chat.role == "user"]
        if user_messages:
            summary_parts.append(f"User asked {len(user_messages)} questions about:")
            topics = set()
            for msg in user_messages:
                if "quote" in msg.message.lower():
                    topics.add("insurance quotes")
                elif "policy" in msg.message.lower():
                    topics.add("policy coverage")
                elif "claim" in msg.message.lower():
                    topics.add("claims process")
                elif "price" in msg.message.lower():
                    topics.add("pricing")
            
            if topics:
                summary_parts.append(", ".join(topics))
        
        # Get assistant responses
        assistant_messages = [chat for chat in recent_chats if chat.role == "assistant"]
        if assistant_messages:
            summary_parts.append(f"Assistant provided {len(assistant_messages)} responses.")
        
        # Add context about user's current state
        summary_parts.append("User may need human assistance for complex queries or personalized support.")
        
        return " ".join(summary_parts)
    
    def get_handoff_reasons(self) -> List[Dict[str, str]]:
        """Get common reasons for human handoff."""
        
        return [
            {
                "code": "complex_query",
                "label": "Complex or technical question",
                "description": "User has a complex question that requires human expertise"
            },
            {
                "code": "pricing_issue",
                "label": "Pricing or payment issue",
                "description": "User is having trouble with pricing or payment processing"
            },
            {
                "code": "policy_confusion",
                "label": "Policy coverage confusion",
                "description": "User needs clarification on policy coverage details"
            },
            {
                "code": "claim_help",
                "label": "Claims assistance needed",
                "description": "User needs help with the claims process"
            },
            {
                "code": "technical_issue",
                "label": "Technical issue",
                "description": "User is experiencing technical problems with the system"
            },
            {
                "code": "general_inquiry",
                "label": "General inquiry",
                "description": "User has a general question or request"
            }
        ]
