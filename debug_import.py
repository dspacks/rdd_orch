import sys
import os

print(f"Python executable: {sys.executable}")
print(f"CWD: {os.getcwd()}")
print(f"Path: {sys.path}")

try:
    print("Attempting to import ade.database...")
    import ade.database
    print(f"ade.database imported from: {ade.database.__file__}")
    print(f"ade.database dir: {dir(ade.database)}")
    
    print("Attempting to import EnhancedDatabaseManager from ade.database...")
    from ade.database import EnhancedDatabaseManager
    print("Success!")
except Exception as e:
    print(f"Error: {e}")
except ImportError as e:
    print(f"ImportError: {e}")
