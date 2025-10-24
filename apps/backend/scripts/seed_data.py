"""Seed data script for development and testing."""

import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.db import SessionLocal, create_tables
from app.core.security import get_password_hash
from app.models.user import User
from app.models.rag_document import RagDocument
from app.services.rag import RagService


def create_sample_users(db: Session):
    """Create sample users for testing."""
    
    users = [
        {
            "email": "demo@example.com",
            "name": "Demo User",
            "password": "password123"
        },
        {
            "email": "john@example.com",
            "name": "John Doe",
            "password": "password123"
        },
        {
            "email": "jane@example.com",
            "name": "Jane Smith",
            "password": "password123"
        }
    ]
    
    for user_data in users:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data["email"]).first()
        if existing_user:
            print(f"User {user_data['email']} already exists, skipping...")
            continue
        
        # Create new user
        user = User(
            email=user_data["email"],
            name=user_data["name"],
            hashed_password=get_password_hash(user_data["password"]),
            is_active=True,
            is_verified=True
        )
        
        db.add(user)
        print(f"Created user: {user_data['email']}")
    
    db.commit()


def create_sample_rag_documents(db: Session):
    """Create sample RAG documents for policy sections."""
    
    rag_service = RagService()
    
    documents = [
        {
            "title": "Comprehensive Travel Insurance Policy",
            "insurer_name": "Demo Insurer",
            "product_code": "COMP_TRAVEL",
            "section_id": "1.1",
            "heading": "Coverage Overview",
            "text": "This comprehensive travel insurance policy provides coverage for medical expenses, trip cancellation, baggage protection, and emergency assistance. The policy is designed to protect travelers against unforeseen circumstances during their trip.",
            "citations": {"section": "1.1", "page": 1}
        },
        {
            "title": "Comprehensive Travel Insurance Policy",
            "insurer_name": "Demo Insurer",
            "product_code": "COMP_TRAVEL",
            "section_id": "2.1",
            "heading": "Medical Coverage",
            "text": "Medical expenses are covered up to $100,000 for emergency treatment during your trip. This includes hospital stays, emergency medical procedures, and prescription medications. Pre-existing conditions are covered if they are stable for 90 days before departure.",
            "citations": {"section": "2.1", "page": 5}
        },
        {
            "title": "Comprehensive Travel Insurance Policy",
            "insurer_name": "Demo Insurer",
            "product_code": "COMP_TRAVEL",
            "section_id": "2.2",
            "heading": "Emergency Medical Evacuation",
            "text": "Emergency medical evacuation coverage up to $250,000 is included. This covers transportation to the nearest appropriate medical facility if you cannot receive adequate treatment at your current location.",
            "citations": {"section": "2.2", "page": 7}
        },
        {
            "title": "Comprehensive Travel Insurance Policy",
            "insurer_name": "Demo Insurer",
            "product_code": "COMP_TRAVEL",
            "section_id": "3.1",
            "heading": "Trip Cancellation",
            "text": "Trip cancellation coverage applies when you need to cancel your trip due to covered reasons such as illness, death of a family member, or natural disasters. Coverage is up to $5,000 per person for non-refundable trip costs.",
            "citations": {"section": "3.1", "page": 10}
        },
        {
            "title": "Comprehensive Travel Insurance Policy",
            "insurer_name": "Demo Insurer",
            "product_code": "COMP_TRAVEL",
            "section_id": "3.2",
            "heading": "Trip Interruption",
            "text": "Trip interruption coverage provides reimbursement for unused, non-refundable portions of your trip if you must return home early due to covered reasons. Coverage is up to $5,000 per person.",
            "citations": {"section": "3.2", "page": 12}
        },
        {
            "title": "Comprehensive Travel Insurance Policy",
            "insurer_name": "Demo Insurer",
            "product_code": "COMP_TRAVEL",
            "section_id": "4.1",
            "heading": "Baggage Coverage",
            "text": "Baggage coverage provides protection for lost, stolen, or damaged luggage and personal belongings. Coverage is up to $2,500 per person with a $100 deductible per claim.",
            "citations": {"section": "4.1", "page": 15}
        },
        {
            "title": "Comprehensive Travel Insurance Policy",
            "insurer_name": "Demo Insurer",
            "product_code": "COMP_TRAVEL",
            "section_id": "4.2",
            "heading": "Baggage Delay",
            "text": "Baggage delay coverage provides reimbursement for essential items if your baggage is delayed for more than 12 hours. Coverage is up to $500 per person with receipts required.",
            "citations": {"section": "4.2", "page": 16}
        },
        {
            "title": "Comprehensive Travel Insurance Policy",
            "insurer_name": "Demo Insurer",
            "product_code": "COMP_TRAVEL",
            "section_id": "5.1",
            "heading": "Travel Delay",
            "text": "Travel delay coverage provides reimbursement for additional expenses if you are delayed for more than 6 hours due to covered reasons. Coverage is up to $500 per person with receipts required.",
            "citations": {"section": "5.1", "page": 18}
        },
        {
            "title": "Comprehensive Travel Insurance Policy",
            "insurer_name": "Demo Insurer",
            "product_code": "COMP_TRAVEL",
            "section_id": "6.1",
            "heading": "Emergency Assistance",
            "text": "24/7 emergency assistance is available worldwide. This includes medical referrals, emergency message relay, and assistance with lost documents. Services are provided by our global assistance network.",
            "citations": {"section": "6.1", "page": 20}
        },
        {
            "title": "Comprehensive Travel Insurance Policy",
            "insurer_name": "Demo Insurer",
            "product_code": "COMP_TRAVEL",
            "section_id": "7.1",
            "heading": "Exclusions",
            "text": "This policy does not cover losses due to war, terrorism, pre-existing conditions (unless stable for 90 days), alcohol or drug-related incidents, or participation in extreme sports without additional coverage.",
            "citations": {"section": "7.1", "page": 22}
        }
    ]
    
    for doc_data in documents:
        # Check if document already exists
        existing_doc = db.query(RagDocument).filter(
            RagDocument.title == doc_data["title"],
            RagDocument.section_id == doc_data["section_id"]
        ).first()
        
        if existing_doc:
            print(f"Document {doc_data['title']} section {doc_data['section_id']} already exists, skipping...")
            continue
        
        # Generate embedding
        embedding = rag_service.embed_text(doc_data["text"])
        
        # Create document
        document = RagDocument(
            title=doc_data["title"],
            insurer_name=doc_data["insurer_name"],
            product_code=doc_data["product_code"],
            section_id=doc_data["section_id"],
            heading=doc_data["heading"],
            text=doc_data["text"],
            citations=doc_data["citations"],
            embedding=embedding
        )
        
        db.add(document)
        print(f"Created document: {doc_data['title']} - {doc_data['section_id']}")
    
    db.commit()


def main():
    """Main seed data function."""
    
    print("🌱 Starting seed data creation...")
    
    # Create database tables
    create_tables()
    print("✅ Database tables created")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Create sample users
        print("\n👥 Creating sample users...")
        create_sample_users(db)
        print("✅ Sample users created")
        
        # Create sample RAG documents
        print("\n📄 Creating sample RAG documents...")
        create_sample_rag_documents(db)
        print("✅ Sample RAG documents created")
        
        print("\n🎉 Seed data creation completed successfully!")
        
    except Exception as e:
        print(f"❌ Error creating seed data: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
