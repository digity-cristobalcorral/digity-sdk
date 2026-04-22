"""
digity.viz — Real-time dashboard for the Digity sensorized exohand.

Install:
    pip install digity[viz]

Launch dashboard:
    digity-viz              # opens desktop window
    digity-viz --browser    # open in system browser
    digity-viz --port COM3  # explicit serial port

Stream glove to cloud dashboard:
    digity-viz --agent --token TOKEN
    digity-viz --agent --token TOKEN --url https://app.digity.de/chiros

Or from Python:
    import digity.viz
    digity.viz.start()
"""

from ._server import run
from ._agent import run as _run_agent


def main():
    """Entry point for the `digity-viz` CLI command."""
    import argparse

    parser = argparse.ArgumentParser(
        description="digity viz — real-time hand dashboard and agent"
    )
    parser.add_argument("--port", default=None, metavar="PORT",
                        help="Serial port for glove (e.g. COM3, /dev/ttyUSB0)")
    parser.add_argument("--browser", action="store_true",
                        help="Open dashboard in system browser instead of desktop window")
    parser.add_argument("--agent", action="store_true",
                        help="Stream glove to a remote digity-viz server (requires --token)")
    parser.add_argument("--token", default=None, metavar="TOKEN",
                        help="Agent token from the cloud dashboard Setup page")
    parser.add_argument("--url", default="https://app.digity.de/chiros", metavar="URL",
                        help="Remote server URL (default: https://app.digity.de/chiros)")
    args = parser.parse_args()

    if args.agent:
        if not args.token:
            parser.error("--token is required in agent mode (copy it from the dashboard Setup page)")
        _run_agent(token=args.token, url=args.url, port=args.port)
    else:
        run(port=args.port, desktop=not args.browser)


def main_agent():
    """Entry point for the `digity-agent` CLI command."""
    import argparse

    parser = argparse.ArgumentParser(
        description="digity agent — stream glove data to a remote digity-viz server"
    )
    parser.add_argument("--token", required=True, metavar="TOKEN",
                        help="Agent token from the cloud dashboard Setup page")
    parser.add_argument("--url", default="https://app.digity.de/chiros", metavar="URL",
                        help="Remote server URL (default: https://app.digity.de/chiros)")
    parser.add_argument("--port", default=None, metavar="PORT",
                        help="Serial port for glove (e.g. COM3, /dev/ttyUSB0)")
    args = parser.parse_args()
    _run_agent(token=args.token, url=args.url, port=args.port)


def start(port=None, desktop=True):
    """Start the digity visualizer (blocking until window is closed)."""
    run(port=port, desktop=desktop)


__all__ = ["main", "main_agent", "start", "run"]
