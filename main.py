"""
Smart Image Studio — Main Entry Point
Run: python main.py
"""
import sys
import os
import logging

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(__file__))

# Setup logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)

# Create required directories
for d in ("uploads", "outputs", "database", "assets/icons", "assets/themes"):
    os.makedirs(d, exist_ok=True)

def main():
    try:
        from gui.app import SmartImageStudio
        logger.info("Starting Smart Image Studio")
        app = SmartImageStudio()
        app.mainloop()
    except ImportError as e:
        logger.critical(f"Import error: {e}")
        print(f"\n❌ Import error: {e}")
        print("Run:  pip install -r requirements.txt\n")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Startup error: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
