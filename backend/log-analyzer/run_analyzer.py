import os
from dotenv import load_dotenv
from log_analyzer import LogAnalyzer
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Load environment variables
    load_dotenv()
    
    # Get S3 bucket and key from environment
    bucket = os.getenv('TEST_S3_BUCKET')
    key = os.getenv('TEST_S3_KEY')
    
    if not bucket or not key:
        logger.error("Missing S3 bucket or key in environment variables")
        return
    
    logger.info(f"Starting log analysis for s3://{bucket}/{key}")
    
    # Initialize and run analyzer
    analyzer = LogAnalyzer(bucket, key)
    try:
        analyzer.run_analysis('custom')
        logger.info("Analysis completed successfully")
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")

if __name__ == '__main__':
    main()