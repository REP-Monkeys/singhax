"""
Policy Document Ingestion Script

Ingests PDF policy documents from ancileo-msig-reference/Policy_Wordings/ into RAG database.

Usage:
    python -m apps.backend.scripts.ingest_policies
    
Or to ingest specific file:
    python -m apps.backend.scripts.ingest_policies --file "Scootsurance QSR022206_updated.pdf"
    
Options:
    --clear: Clear existing documents before ingesting
    --dry-run: Show what would be done without making changes
"""

import sys
from pathlib import Path
import argparse
import logging
import os
from dotenv import load_dotenv

# Load environment variables from project root .env file
project_root = Path(__file__).parent.parent.parent.parent
env_path = project_root / '.env'
load_dotenv(env_path)

# Add apps/backend to path for absolute imports
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.services.rag import RAGService
from app.core.db import SessionLocal
from app.models.rag_document import RagDocument

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Policy document configurations
POLICY_DOCS = [
    {
        "filename": "Scootsurance QSR022206_updated.pdf",
        "title": "Scootsurance Travel Insurance",
        "insurer_name": "MSIG",
        "product_code": "QSR022206",
        "tier": None  # All tiers
    },
    {
        "filename": "TravelEasy Policy QTD032212.pdf",
        "title": "TravelEasy Travel Insurance",
        "insurer_name": "MSIG",
        "product_code": "QTD032212",
        "tier": None  # All tiers
    },
    {
        "filename": "TravelEasy Pre-Ex Policy QTD032212-PX.pdf",
        "title": "TravelEasy Pre-Ex Travel Insurance",
        "insurer_name": "MSIG",
        "product_code": "QTD032212-PX",
        "tier": "pre-ex"
    }
]


def clear_existing_documents(db, dry_run=False):
    """Clear existing RAG documents."""
    count = db.query(RagDocument).count()
    
    if count == 0:
        logger.info("No existing documents to clear")
        return 0
    
    if dry_run:
        logger.info(f"[DRY RUN] Would delete {count} existing documents")
        return 0
    
    response = input(f"Delete {count} existing documents? (yes/no): ")
    if response.lower() != 'yes':
        logger.info("Keeping existing documents")
        return 0
    
    deleted = db.query(RagDocument).delete()
    db.commit()
    logger.info(f"Deleted {deleted} existing documents")
    return deleted


def ingest_policy(rag_service, pdf_path: Path, config: dict):
    """Ingest a single policy document."""
    logger.info(f"\n{'='*60}")
    logger.info(f"Ingesting: {config['title']}")
    logger.info(f"File: {pdf_path.name}")
    logger.info(f"{'='*60}")
    
    try:
        result = rag_service.ingest_pdf(
            pdf_path=str(pdf_path),
            title=config['title'],
            insurer_name=config['insurer_name'],
            product_code=config['product_code'],
            tier=config.get('tier')
        )
        
        logger.info(f"✅ Success:")
        logger.info(f"   - Sections found: {result['sections_found']}")
        logger.info(f"   - Chunks created: {result['chunks_created']}")
        logger.info(f"   - Documents stored: {result['documents_stored']}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to ingest {pdf_path.name}: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(description="Ingest policy PDF documents")
    parser.add_argument(
        "--file",
        type=str,
        help="Ingest specific file only (filename from Policy_Wordings folder)"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing documents before ingesting"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    
    args = parser.parse_args()
    
    # Setup database session
    db = SessionLocal()
    rag_service = RAGService(db=db)
    
    try:
        # Clear existing documents if requested
        if args.clear:
            clear_existing_documents(db, dry_run=args.dry_run)
        
        # Get policy wordings directory
        policy_dir = project_root / "ancileo-msig-reference" / "Policy_Wordings"
        
        if not policy_dir.exists():
            logger.error(f"Policy directory not found: {policy_dir}")
            sys.exit(1)
        
        # Filter documents if specific file requested
        docs_to_ingest = POLICY_DOCS
        if args.file:
            docs_to_ingest = [d for d in POLICY_DOCS if d['filename'] == args.file]
            if not docs_to_ingest:
                logger.error(f"File not found in configuration: {args.file}")
                sys.exit(1)
        
        # Ingest documents
        total_results = {
            "sections_found": 0,
            "chunks_created": 0,
            "documents_stored": 0
        }
        
        for doc_config in docs_to_ingest:
            pdf_path = policy_dir / doc_config['filename']
            
            if not pdf_path.exists():
                logger.error(f"PDF file not found: {pdf_path}")
                continue
            
            if args.dry_run:
                logger.info(f"[DRY RUN] Would ingest: {pdf_path.name}")
                continue
            
            result = ingest_policy(rag_service, pdf_path, doc_config)
            
            total_results["sections_found"] += result["sections_found"]
            total_results["chunks_created"] += result["chunks_created"]
            total_results["documents_stored"] += result["documents_stored"]
        
        # Summary
        logger.info(f"\n{'='*60}")
        logger.info("📊 INGESTION SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Total sections found: {total_results['sections_found']}")
        logger.info(f"Total chunks created: {total_results['chunks_created']}")
        logger.info(f"Total documents stored: {total_results['documents_stored']}")
        logger.info(f"{'='*60}\n")
        
        if args.dry_run:
            logger.info("[DRY RUN] No changes made to database")
        else:
            logger.info("✅ Ingestion complete!")
        
    except Exception as e:
        logger.error(f"❌ Ingestion failed: {e}")
        db.rollback()
        raise
        
    finally:
        db.close()


if __name__ == "__main__":
    main()

