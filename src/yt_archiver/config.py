from collections import namedtuple
import os
import yaml


class Config(object):
    """
    Configuration handler for the YouTube archiver.

    Loads and manages a YAML configuration file that contains a list of channels
    and downloader settings. Supports adding new channels and accessing structured
    config values.

    Attributes:
        Channel (namedtuple): Represents a YouTube channel with attributes `name`, `id`, and optional `keep`.
        path (str): Path to the loaded YAML configuration file.
        config (dict): Parsed YAML data.
    """

    Channel = namedtuple("Channel", "name id keep", defaults=(None,))

    def __init__(self, path):
        """
        Initialize the Config object by reading a YAML config file from the given path.

        Args:
            path (str): Path to the YAML configuration file (can include ~ for home).
        """
        path = os.path.expanduser(path)
        with open(path, "r") as f:
            self.config = yaml.safe_load(f)
        self.path = path

    def save(self, path=None):
        """
        Save the current configuration back to a file.

        Args:
            path (str, optional): Path to write the configuration. If None, uses the original path.
        """
        if not path:
            path = self.path
        path = os.path.expanduser(path)
        with open(path, "w") as f:
            yaml.dump(self.config, f, sort_keys=False)

    def channels(self):
        """
        Return the list of configured YouTube channels.

        Returns:
            list[Channel]: A list of Channel namedtuples defined in the config.
        """
        return [self.Channel(**c) for c in self.config.get("channels", [])]

    def add_channel(self, new_channel):
        """
        Add a new channel to the configuration, avoiding duplicates.

        Args:
            new_channel (Channel): A Channel namedtuple to add.

        Returns:
            bool: True if the channel was added successfully, False if it already exists.
        """
        for channel in self.channels():
            if channel.id == new_channel.id:
                print(f"Channel ID '{channel.id}' already in archive")
                return False

        kwargs = new_channel._asdict()
        if kwargs["keep"] is None:
            del kwargs["keep"]

        self.config.get("channels", []).append(kwargs)
        return True

    def downloader(self):
        """
        Get the downloader configuration section.

        Returns:
            dict or None: Downloader configuration, if defined.
        """
        return self.config.get("downloader", None)

    def output_path(self):
        """
        Get the output path for downloads from the downloader config.

        Returns:
            str or None: The output path string, or None if not set.
        """
        return self.downloader().get("output_path", None)
