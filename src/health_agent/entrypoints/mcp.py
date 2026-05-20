from __future__ import annotations

import asyncio
import signal
import sys
import logging

from health_agent.adapters.inbound.mcp.server import create_mcp_server
from health_agent.bootstrap.container import create_container
from health_agent.core.config import get_settings
from health_agent.core.logging import setup_mcp_logging

setup_mcp_logging(log_file="logs/mcp.log")

settings = get_settings()
container = create_container(settings)

mcp = create_mcp_server(
    user_profile_use_cases=container.user_profile_use_cases,
    tracking_use_cases=container.tracking_use_cases,
    schedule_management_use_cases=container.schedule_management_use_cases,
    feedback_use_cases=container.feedback_use_cases,
    observation_use_cases=container.observation_use_cases,
)

logger = logging.getLogger(__name__)

# ... Your tools and resources definitions here ...

async def shutdown(sig, loop):
    """Safely closes the MCP server on termination signals."""
    logger.info(f"Received signal {sig.name}, shutting down...")
    
    # Add any custom cleanup logic here (e.g., closing db pools)
    
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
        
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()
    sys.exit(0)

def main_for_async():
    loop = asyncio.get_event_loop()
    
    # Capture standard termination signals
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(
            sig, 
            lambda s=sig: asyncio.create_task(shutdown(s, loop))
        )

    try:
        # Run your FastMCP application
        mcp.run()
    except KeyboardInterrupt:
        pass


def main() -> None:
    logger.info("MCP server starting.")

    try:
        mcp.run()

    except KeyboardInterrupt:
        logger.info("MCP server interrupted by KeyboardInterrupt.")

    except SystemExit:
        logger.info("MCP server received SystemExit.")
        raise

    except BaseException:
        logger.exception("MCP server crashed.")
        raise

    finally:
        logger.info("MCP server stopped.")
        logging.shutdown()


if __name__ == "__main__":
    main()