import argparse
from rich.console import Console
from rich.table import Table
from yt_archiver.archiver import Archiver
from yt_archiver.config import Config


def configure():
    """
    Configure the argument parser for the CLI.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("--config", "-c", default="~/.yt-archiver.yaml")

    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", help="Channel search")
    search.add_argument("term", nargs="*")

    add = subparsers.add_parser("add", help="Add a channel")
    add.add_argument("--id", "-i", required=True)
    add.add_argument("--name", "-n", required=True)
    add.add_argument("--keep", "-k", type=int)

    subparsers.add_parser("status", help="Archive status")

    sync = subparsers.add_parser("sync", help="Sync channels")

    return parser.parse_args()


class ArchiverCLI(object):
    """
    ArchiverCLI - Command-line interface handler for the YouTube Archiver.
    """

    def __init__(self, config):
        """
        Initialize the CLI with a given configuration file.

        Args:
            config (str): Path to the configuration file.
        """
        self.console = Console()
        self.archiver = Archiver(config)

    def search(self, term):
        """
        Search for YouTube channels using a term and display results in a table.

        Args:
            term (str): Search keyword.

        Returns:
            int: Exit status code (0).
        """
        table = Table(show_header=True, header_style="bold blue")

        table.add_column("Channel")
        table.add_column("URL")
        table.add_column("ID", style="dim")

        print("Searching..")
        for result in self.archiver.channel_search(term):
            table.add_row(result.name, result.url, result.id)

        self.console.print(table)
        return 0

    def add(self, channel):
        """
        Add a channel to the configuration.

        Args:
            channel (Config.Channel): Channel to add.

        Returns:
            int: 0 if the channel was added, 1 if it was already present.
        """
        return 0 if self.archiver.add_channel(channel) else 1

    def status(self):
        """
        Display the current download status of all configured channels.

        Returns:
            int: Exit status code (0).
        """
        table = Table(show_header=True, header_style="bold blue")

        table.add_column("Channel")
        table.add_column("Downloads", justify="right")

        for channel in self.archiver.channels():
            downloads = str(len(self.archiver.get_local_videos(channel)))
            downloads += f"/{channel.keep}" if channel.keep else ""
            table.add_row(channel.name, downloads)

        self.console.print(table)
        return 0

    def sync(self):
        """
        Sync all channels by downloading new videos and cleaning up old ones.

        Returns:
            int: Exit status code (0).
        """
        for channel in self.archiver.channels():
            print(f"Syncing channel: {channel.name}")
            self.archiver.sync_channel(channel)
        return 0


def main():
    args = configure()

    archiver_cli = ArchiverCLI(args.config)

    status = None
    if args.command == "search":
        status = archiver_cli.search(" ".join(args.term))
    elif args.command == "status":
        status = archiver_cli.status()
    elif args.command == "add":
        channel = Config.Channel(name=args.name, id=args.id, keep=args.keep)
        status = archiver_cli.add(channel)
    elif args.command == "sync":
        status = archiver_cli.sync()

    return status
