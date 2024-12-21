import requests
from bs4 import BeautifulSoup, Tag
from transformers import AutoTokenizer, LongT5ForConditionalGeneration, MarianMTModel, MarianTokenizer
from .utils import elapsed_time, clean_article_text
import torch
import time
import os
import logging

logger = logging.getLogger(__file__)
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")


# TODO: Add more resources
def fetch_news() -> list:
  """

  """
  base_link = "https://www.allure.com"
  links = []
  articles: list = []
  logger.info("Fetching news from Allure...")
  try:

    allure_response = requests.get("https://www.allure.com/topic/trends")
    soup = BeautifulSoup(allure_response.text, "html.parser")
    div_headlines: Tag = soup.find("div", class_="summary-list__items")
    headlines: Tag = div_headlines.find_all("a", class_="SummaryItemHedLink-civMjp")

    count = 0
    for link_to_headline in headlines:
      if count >= 3:  # Check if we've already processed 3 headlines
        break
      count += 1
      links.append(link_to_headline.get("href"))

    del soup, allure_response, div_headlines, headlines
    links_iterator = iter(links)
    for i in links:
      new_link = base_link + next(links_iterator)
      article_response = requests.get(new_link)
      article_soup = BeautifulSoup(article_response.text, "html.parser")
      wrapper: Tag = article_soup.find_all("div", class_="body__inner-container")
      base_article: str = ""
      for i in wrapper:
        for j in i.find_all("p"):
          base_article += j.get_text()

      articles.append(base_article)
      logger.info(f"Got article from {new_link}")

      time.sleep(int(os.getenv("SECONDS_BETWEEN_FETCH"))) # Wait three seconds to not detect site
  except Exception as e:
    logger.error(f"Error occurred while fetching news: {e}")
    raise

  return articles


@elapsed_time(logger=logger)
def summarize_articles(articles: list) -> list:
  """
    Summarizes a list of articles into a single coherent summary with an introduction, body, and conclusion.

    Parameters:
    - articles (list): A list of articles, where each article is a string (could be a sentence, paragraph, etc.)

    Returns:
    - list: A list of summarized chunks of the original articles, with each chunk being a part of the final summary.

    Example:
    >>> summarize_articles(["This is article 1.", "This is article 2."])
    ['Summary part 1...', 'Summary part 2...']
    """
  pre_article = " ".join(articles)
  article = clean_article_text(pre_article)
  prompt = f"Summarize the following articles into a single coherent article with an introduction, body, and conclusion:\n{article}\n"

  logger.info("Summarizing articles...")
  tokenizer = AutoTokenizer.from_pretrained("google/long-t5-tglobal-base")
  model = LongT5ForConditionalGeneration.from_pretrained("google/long-t5-tglobal-base")

  if torch.cuda.is_available():
      model = model.to('cuda')

  chunk_size = 4000  # You can adjust this based on your model's max input length
  chunks = [prompt[i:i + chunk_size] for i in range(0, len(prompt), chunk_size)]

  summaries = []

  for chunk in chunks:
      inputs = tokenizer(chunk, return_tensors="pt", truncation=True, max_length=512)

      if torch.cuda.is_available():
          inputs = {key: value.to('cuda') for key, value in inputs.items()}

      summary_ids = model.generate(inputs['input_ids'],
                                    max_length=300,
                                    min_length=100,
                                    num_beams=8,
                                    length_penalty=2.0,
                                    early_stopping=True)

      chunk_summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
      summaries.append(chunk_summary)

  final_summary = " ".join(summaries)


  logger.info("Final Summary: " + final_summary)
  return summaries

def translate_content(articles: list) -> str:
    """
    Translates a list of articles into multiple target languages using the DeepL API.

    Parameters:
    - articles (list): A list of articles, where each article is a list of text strings that make up the full article.

    Returns:
    - str: A string containing the translated articles in different languages (Spanish, Polish, Turkish).

    Example:
    >>> translate_content([["This is an article.", "It has multiple sentences."]])
    'Translated to ES:\nEste es un artículo.\nTiene varias oraciones.\n...'
    """
    def translate_text(text, target_language):
        url = "https://api-free.deepl.com/v2/translate"

        params = {
            'auth_key': DEEPL_API_KEY,  # Your DeepL API key
            'text': text,               # Text to be translated
            'target_lang': target_language.upper()  # Target language (e.g., 'ES' for Spanish)
        }

        response = requests.post(url, data=params)

        if response.status_code == 200:
            result = response.json()
            translated_text = result['translations'][0]['text']
            return translated_text
        else:
            raise Exception(f"Error: {response.status_code}, {response.text}")

    target_langs = ['es', 'pl', 'tr']  # Spanish, Polish, Turkish

    translated_articles = []

    for article in articles:
        full_article = " ".join(article)

        for lang in target_langs:
            try:
                translated_text = translate_text(full_article, lang)
                translated_articles.append(f"Translated to {lang.upper()}:\n{translated_text}\n")
            except Exception as e:
                print(f"Error translating to {lang}: {e}")
                translated_articles.append(f"Error translating to {lang.upper()}: {e}\n")

    # Return all translations as a single string
    return "\n".join(translated_articles)