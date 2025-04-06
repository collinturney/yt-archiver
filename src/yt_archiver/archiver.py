import glob
import os
import re
import scrapetube
import subprocess
from .config import Config
from .yt_api import YTApi


class Archiver(object):
    """
    Archiver - manages YouTube channel subscriptions and local video archival.

    This class provides functionality to sync videos from YouTube channels,
    download new content, and clean up old or deleted videos based on configured
    preferences.
    """

    def __init__(self, config_file):
        """
        Initialize the Archiver with a given configuration file.

        Args:
            config_file (str): Path to the YAML or JSON configuration file.
        """
        self.config = Config(config_file)

    def channels(self):
        """
        Get the list of configured channels.

        Returns:
            list: A list of Channel objects loaded from the configuration.
        """
        return self.config.channels()

    def channel_search(self, term, max_results=5):
        """
        Search for YouTube channels using a search term.

        Args:
            term (str): Search keyword for YouTube channels.
            max_results (int): Maximum number of results to return. Defaults to 5.

        Yields:
            dict: Search result for each matching YouTube channel.
        """
        for index, result in enumerate(YTApi.channel_search(term)):
            if index + 1 == max_results:
                break

            yield result

    def add_channel(self, channel):
        """
        Add a channel to the configuration if it does not already exist.

        Args:
            channel (dict): Channel object to add.

        Returns:
            bool: True if the channel was added and config was saved, False otherwise.
        """
        if self.config.add_channel(channel):
            self.config.save()
            return True
        return False

    def sync(self):
        """
        Synchronize all configured channels by downloading new videos
        and cleaning up removed or outdated ones.
        """
        for channel in self.config.channels():
            self.sync_channel(channel)

    def sync_channel(self, channel):
        """
        Synchronize a single channel.

        Args:
            channel (Channel): The channel to sync.

        This involves downloading new videos and deleting those no longer in the latest list.
        """
        local_videos = self.get_local_videos(channel)
        latest_videos = self.get_latest_videos(channel)

        new_videos = latest_videos.difference(local_videos)
        self.download_videos(channel, new_videos)

        old_videos = local_videos.difference(latest_videos)
        self.cleanup_videos(channel, old_videos)

    def get_latest_videos(self, channel):
        """
        Get the latest video IDs from a YouTube channel.

        Args:
            channel (Channel): The channel to retrieve videos from.

        Returns:
            set: A set of video IDs.
        """
        video_ids = set()

        videos = scrapetube.get_channel(channel.id)

        for index, video in enumerate(videos):
            video_ids.add(video["videoId"])

            if index + 1 == channel.keep:
                break

        return video_ids

    def get_local_videos(self, channel):
        """
        Get the set of locally downloaded video IDs for a channel.

        Args:
            channel (Channel): The channel whose videos to check locally.

        Returns:
            set: A set of video IDs present locally.
        """
        video_ids = set()

        channel_path = os.path.join(self.config.output_path(), channel.name)

        try:
            files = os.listdir(channel_path)
        except Exception as e:
            print(f"Error listing path '{channel_path}': {e}")
            return video_ids

        # match: 'title [id].mpg'
        video_pattern = re.compile("\\[([\\w-]+)\\]\\.\\w+$")

        for file in files:
            full_path = os.path.join(channel_path, file)
            if os.path.isfile(full_path):
                result = re.search(video_pattern, file)

                if result:
                    video_ids.add(result.group(1))

        return video_ids

    def download_videos(self, channel, new_videos):
        """
        Download new videos for a channel.

        Args:
            channel (Channel): The channel for which to download videos.
            new_videos (set): Set of new video IDs to download.
        """
        downloader = self.config.downloader()
        for video in new_videos:
            kwargs = downloader | {"video_id": video, "channel_name": channel.name}
            subprocess.call(downloader["command"].format(**kwargs), shell=True)

    def cleanup_videos(self, channel, patterns):
        """
        Delete local video files that are no longer part of the latest set.

        Args:
            channel (Channel): The channel to clean up.
            patterns (set): Set of video ID substrings to match for deletion.
        """
        output_path = self.config.downloader().get("output_path")
        for pattern in patterns:
            match_path = os.path.join(output_path, channel.name, f"*{pattern}*")
            for file_path in glob.glob(match_path):
                try:
                    os.unlink(file_path)
                    print(f"Deleted: {file_path}")
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")
