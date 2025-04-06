from collections import namedtuple
from glom import glom
import scrapetube
from urllib.parse import urljoin


class YTApi(object):
    """
    Provides utility methods for extracting YouTube channel information
    from search results using the Scrapetube and Glom libraries.
    """

    CHANNEL_TYPE = "WEB_PAGE_TYPE_CHANNEL"

    BASE_URL = "https://www.youtube.com/"

    PAGE_TYPE_PATH = ".".join(
        [
            "longBylineText",
            "runs",
            "0",
            "navigationEndpoint",
            "commandMetadata",
            "webCommandMetadata",
            "webPageType",
        ]
    )

    CHANNEL_ID_PATH = ".".join(
        [
            "longBylineText",
            "runs",
            "0",
            "navigationEndpoint",
            "browseEndpoint",
            "browseId",
        ]
    )

    CHANNEL_NAME_PATH = ".".join(["longBylineText", "runs", "0", "text"])

    CHANNEL_URL_PATH = ".".join(
        [
            "longBylineText",
            "runs",
            "0",
            "navigationEndpoint",
            "browseEndpoint",
            "canonicalBaseUrl",
        ]
    )

    SearchResult = namedtuple("SearchResult", "id name url")

    @staticmethod
    def is_channel(search_result):
        """
        Determine whether the given search result represents a YouTube channel.

        Args:
            search_result (dict): A single search result from scrapetube.

        Returns:
            bool: True if the result is a channel, False otherwise.
        """
        page_type = glom(search_result, YTApi.PAGE_TYPE_PATH, default=None)
        return page_type == YTApi.CHANNEL_TYPE

    @staticmethod
    def channel_id(search_result):
        """
        Extract the channel ID from a search result.

        Args:
            search_result (dict): A single search result from scrapetube.

        Returns:
            str or None: Channel ID if found, else None.
        """
        return glom(search_result, YTApi.CHANNEL_ID_PATH, default=None)

    @staticmethod
    def channel_name(search_result):
        """
        Extract the channel name from a search result.

        Args:
            search_result (dict): A single search result from scrapetube.

        Returns:
            str or None: Channel name if found, else None.
        """
        return glom(search_result, YTApi.CHANNEL_NAME_PATH, default=None)

    @staticmethod
    def channel_url(search_result):
        """
        Extract and return the full YouTube channel URL from a search result.

        Args:
            search_result (dict): A single search result from scrapetube.

        Returns:
            str or None: Full channel URL if found, else None.
        """
        channel_url = glom(search_result, YTApi.CHANNEL_URL_PATH, default=None)
        return urljoin(YTApi.BASE_URL, channel_url)

    @staticmethod
    def channel_search(term):
        """
        Perform a search on YouTube using the given term and yield unique channel results.

        Args:
            term (str): Search term to query YouTube.

        Yields:
            SearchResult: A named tuple containing the channel ID, name, and URL.
        """
        result_ids = set()
        for result in scrapetube.get_search(term):
            id_ = YTApi.channel_id(result)
            if YTApi.is_channel(result) and id_ not in result_ids:
                result_ids.add(id_)
                name = YTApi.channel_name(result)
                url = YTApi.channel_url(result)
                yield YTApi.SearchResult(id=id_, name=name, url=url)
