import os

from slack import WebClient
from slack.errors import SlackApiError


class SlackService:
    def __init__(self, channel='#infrastructure-events'):
        self.slack_token = os.environ.get('SLACK_TOKEN')
        self.channel = channel
        self.client = WebClient(token=self.slack_token)

    def send_message(self, content):
        try:
            self.client.chat_postMessage(
                channel=self.channel,
                text=content
            )
            return True
        except SlackApiError as e:
            print(f'Slack error: {e}')
            return False
