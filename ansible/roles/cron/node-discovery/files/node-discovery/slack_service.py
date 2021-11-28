import os

from slack import WebClient
from slack.errors import SlackApiError
from logging_service import LoggingService as Log


class SlackService:
    def __init__(self, channel='#infrastructure-events'):
        self.slack_token = os.environ.get('SLACK_TOKEN')
        self.channel = channel
        self.client = WebClient(token=self.slack_token)

    def send_message(self, content):
        if self.slack_token is not None:
            try:
                self.client.chat_postMessage(
                    channel=self.channel,
                    text=content
                )
                return True
            except SlackApiError as e:
                Log.err(f'Slack error: {e}')
                return False
