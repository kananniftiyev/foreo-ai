from dotenv import load_dotenv
import os
from .core.article import fetch_news, summarize_articles, translate_content


load_dotenv(".env")

def main():
  news: list = fetch_news()
  articles: list = summarize_articles(articles=news)
  translated_content = translate_content(articles)
  print(translate_content)

if __name__ == "__main__":
  main()