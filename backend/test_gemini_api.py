#!/usr/bin/env python3
"""
Diagnostic script to test Gemini API configuration and available models
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# Setup logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "gemini_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    logger.info("=" * 80)
    logger.info("GEMINI API DIAGNOSTIC TEST")
    logger.info("=" * 80)
    
    # Load environment variables
    load_dotenv()
    
    # Check API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("❌ GEMINI_API_KEY not found in .env file")
        return False
    
    logger.info(f"✅ API Key found: {api_key[:15]}...{api_key[-5:]}")
    
    # Configure API
    try:
        genai.configure(api_key=api_key)
        logger.info("✅ API configured successfully")
    except Exception as e:
        logger.error(f"❌ Failed to configure API: {e}")
        return False
    
    # List available models
    logger.info("\n" + "=" * 80)
    logger.info("AVAILABLE MODELS:")
    logger.info("=" * 80)
    
    try:
        models = genai.list_models()
        for model in models:
            model_name = model.name.replace("models/", "")
            supported_methods = [method.lower() for method in model.supported_generation_methods]
            logger.info(f"  • {model_name}")
            logger.info(f"    Display Name: {model.display_name}")
            logger.info(f"    Supported Methods: {', '.join(supported_methods)}")
            logger.info("")
    except Exception as e:
        logger.error(f"❌ Failed to list models: {e}")
        return False
    
    # Test with gemini-1.5-pro
    logger.info("=" * 80)
    logger.info("TESTING GEMINI-1.5-PRO MODEL:")
    logger.info("=" * 80)
    
    model_name = "gemini-2.5-flash"
    try:
        model = genai.GenerativeModel(model_name)
        logger.info(f"✅ Successfully created model: {model_name}")
        
        # Test a simple prompt
        test_prompt = "Hello! Can you confirm you are working properly? Reply with 'Working' if successful."
        logger.info(f"\n📝 Test prompt: {test_prompt}")
        
        response = model.generate_content(test_prompt)
        logger.info(f"✅ API Response received:")
        logger.info(f"   {response.text}")
        logger.info(f"\n✅ GEMINI API IS WORKING CORRECTLY!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing model {model_name}: {e}")
        logger.error(f"   Error Type: {type(e).__name__}")
        logger.error(f"   Full Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    logger.info("\n" + "=" * 80)
    if success:
        logger.info("✅ ALL TESTS PASSED - Your API is configured correctly!")
        sys.exit(0)
    else:
        logger.error("❌ TESTS FAILED - Please check the logs above for details")
        sys.exit(1)
