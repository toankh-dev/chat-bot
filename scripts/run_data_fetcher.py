"""
Run data fetcher to ingest data from GitLab, Slack, Backlog into S3
"""

import sys
import os
import logging

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambda', 'data_fetcher'))

from lambda_function import lambda_handler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Run data fetcher locally"""

    logger.info("=" * 60)
    logger.info("Running Data Fetcher")
    logger.info("=" * 60)

    # Set S3 bucket name
    os.environ['S3_BUCKET_NAME'] = 'chatbot-raw-data'

    # Run the lambda handler
    result = lambda_handler({}, {})

    logger.info("\n" + "=" * 60)
    logger.info("Data Fetcher Result")
    logger.info("=" * 60)
    logger.info(f"Status Code: {result['statusCode']}")
    logger.info(f"Body: {result['body']}")

    if result['statusCode'] == 200:
        logger.info("\n✅ Data fetching completed successfully!")
        logger.info("\nNext step: Run build_vector_index.py to index the data")
    else:
        logger.error("\n❌ Data fetching failed!")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
