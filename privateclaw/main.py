"""Main entry point for PrivateClaw."""

import asyncio
import sys
from privateclaw.config.settings import Settings, get_settings
from privateclaw.gateway.server import Gateway


async def run_gateway(settings: Settings) -> None:
    """Run the gateway server."""
    gateway = Gateway(settings)
    await gateway.start()


def main() -> None:
    """Main entry point."""
    settings = get_settings()

    try:
        asyncio.run(run_gateway(settings))
    except KeyboardInterrupt:
        print("\nShutting down PrivateClaw...")
        sys.exit(0)


if __name__ == "__main__":
    main()
