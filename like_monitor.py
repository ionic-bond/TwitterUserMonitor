#!/usr/bin/python3
"""
Because the twitter api only allows to query the last 200 tweets sorted by creation time,
we cannot know if the user likes a very old tweet.
"""

from typing import List, Union, Set

from monitor_base import MonitorBase


def _get_like_id_set(like_list: list) -> Set[str]:
    return set(like['id'] for like in like_list)


class LikeMonitor(MonitorBase):

    def __init__(self, token_config: dict, username: str, telegram_chat_id_list: List[str]):
        super().__init__('Like', token_config, username, telegram_chat_id_list)

        like_list = None
        while like_list is None:
            like_list = self.get_like_list()
        self.existing_like_id_set = _get_like_id_set(like_list)
        self.min_like_id = min(self.existing_like_id_set) if self.existing_like_id_set else 0

        self.logger.info('Init like monitor succeed.\nUser id: {}\nExisting likes: {}'.format(
            self.user_id, self.existing_like_id_set))

    def get_like_list(self) -> Union[list, None]:
        url = 'https://api.twitter.com/1.1/favorites/list.json'
        params = {'user_id': self.user_id, 'count': 200}
        return self.twitter_watcher.query(url, params)

    def watch(self):
        like_list = self.get_like_list()
        if not like_list:
            return
        for like in reversed(like_list):
            if like['id'] not in self.existing_like_id_set and like['id'] > self.min_like_id:
                self.telegram_notifier.send_message('@{}: {}'.format(like['user']['screen_name'],
                                                                     like['text']))
        self.existing_like_id_set |= _get_like_id_set(like_list)
        self.update_last_watch_time()

    def status(self) -> str:
        return 'Last: {}, number: {}'.format(self.last_watch_time, len(self.existing_like_id_set))
