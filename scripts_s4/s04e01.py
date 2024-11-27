import asyncio
from loguru import logger
from src.s_04.e_01 import (ImagePipeline,
                           send_request,
                           extract_filenames)


async def main():

    res = send_request("START")

    initial_filenames = extract_filenames(res.message)

    logger.info(f"Extracted files: {initial_filenames}")

    try:
        # Initialize and run the pipeline
        pipeline = ImagePipeline()
        result = await pipeline.run_pipeline(initial_filenames)

        logger.info("Pipeline completed successfully")
        logger.info(f"Final result: {result}")

    except Exception as e:
        logger.error(f"Main execution error: {str(e)}")
        raise


if __name__ == "__main__":
   asyncio.run(main())