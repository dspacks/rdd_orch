import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('ADE-Verify')

try:
    print("Testing imports...")
    from ade import (
        API_CONFIG,
        DatabaseManager,
        EnhancedDatabaseManager,
        Orchestrator,
        ReviewQueueManager
    )

    
    # Check SDK presence
    try:
        from google import genai
        print(f"✓ google-genai SDK found")
    except ImportError:
        print("⚠ google-genai SDK not found (optional for structural verification)")

    print("✓ Imports successful")

    print("\nTesting Database Initialization...")
    db = EnhancedDatabaseManager("test_verify.db")
    db.connect()
    db.initialize_schema()
    print("✓ Database initialized")

    print("\nTesting Orchestrator Initialization...")
    orch = Orchestrator(db)
    print(f"✓ Orchestrator initialized with agents: {orch.data_parser.name}, {orch.technical_analyzer.name}")

    print("\nTesting UI Components Initialization...")
    try:
        from ade.ui import (
            HITLReviewDashboard,
            DocumentUploader,
            BatchOperationsWidget,
            ClarificationWidget,
            ExportWidget
        )
        queue = ReviewQueueManager(db)
        dashboard = HITLReviewDashboard(queue)
        uploader = DocumentUploader()
        batch = BatchOperationsWidget(queue)
        print("✓ UI components initialized")
    except ImportError as e:
        print(f"⚠ UI components validation skipped (missing dependency: {e})")
        print("  (This is expected if running in a non-Jupyter environment)")

    print("\nVerification Complete: All systems nominal.")
    
    # Cleanup
    db.close()
    if os.path.exists("test_verify.db"):
        os.remove("test_verify.db")

except Exception as e:
    print(f"\n❌ Verification Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
