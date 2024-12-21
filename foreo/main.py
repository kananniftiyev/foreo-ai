from dotenv import load_dotenv
import os
from .core.article import fetch_news, summarize_articles, translate_content
from .core.utils import clean_article_text


load_dotenv(".env")

def main():
  news: list = fetch_news()
  # articles: list = summarize_articles(articles=news)
  # translated_content = translate_content(articles)
  # print(translate_content)

  print(news[1])

if __name__ == "__main__":
  main()