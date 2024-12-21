import logging
import colorlog
from dotenv import load_dotenv
import os
from .core.article import fetch_news, summarize_articles, translate_content

load_dotenv(".env")

# Set up Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
formatter = colorlog.ColoredFormatter(
    "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",  # Date format
    log_colors={
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold_red",
    },
)
console_handler.setFormatter(formatter)
logger.propagate = False
logger.addHandler(console_handler)

def post_articles():
  pass


def main():
  news: list = fetch_news()
  articles: list = summarize_articles(articles=news)
  translated_content = translate_content(articles)
  logger.info(translate_content)

if __name__ == "__main__":
  main()