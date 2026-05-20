from __future__ import annotations

import logging

import uvicorn
from dotenv import load_dotenv

from health_agent.bootstrap.container import create_container
from health_agent.bootstrap.wiring import create_fastapi_app
from health_agent.core.config import get_settings
from health_agent.core.logging import setup_api_logging


load_dotenv()

setup_api_logging(
    log_file="logs/api.log",
    console=True,
)

logger = logging.getLogger(__name__)

settings = get_settings()
container = create_container(settings)
app = create_fastapi_app(container)


def main() -> None:
    logger.info("FastAPI scheduler server starting.")

    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=settings.scheduler_control_base_port,
            reload=False,
            log_config=None,
            access_log=False,
        )
    except KeyboardInterrupt:
        logger.info("FastAPI scheduler server interrupted by KeyboardInterrupt.")
    except BaseException:
        logger.exception("FastAPI scheduler server crashed.")
        raise
    finally:
        logger.info("FastAPI scheduler server stopped.")
        logging.shutdown()


if __name__ == "__main__":
    main()