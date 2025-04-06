import os
from dotenv import load_dotenv
from log_analyzer import LogAnalyzer
import logging
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Run Log Analyzer")
    parser.add_argument('--verbose', action='store_true', help="Enable verbose output and intermediate step logging.")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled: showing intermediate steps during analysis")
    
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
        if args.verbose:
            logger.debug("Running analysis in verbose mode")
            analyzer.run_analysis('custom', verbose=True)
        else:
            analyzer.run_analysis('custom')
        logger.info("Analysis completed successfully")
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")

if __name__ == '__main__':
    main()