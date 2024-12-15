import requests
from bs4 import BeautifulSoup, Tag
from transformers import AutoTokenizer, LongT5Model, LongT5ForConditionalGeneration
import logging
import time
import torch
import colorlog
import re
from time import perf_counter
from .utils import clean_article_text
import multiprocessing

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
# Apply the formatter to the handler
console_handler.setFormatter(formatter)
logger.propagate = False
logger.addHandler(console_handler)


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

      time.sleep(3) # Wait three seconds to not detect site
  except Exception as e:
    logger.error(f"Error occurred while fetching news: {e}")
    raise

  return articles


# TODO: Generator Pref
def summarize_articles():
  """

  """
  # Fetch the first article
  a = fetch_news()
  pre_article = " ".join(a)
  article = clean_article_text(pre_article)
  prompt = f"Summarize the following articles into a single coherent article with an introduction, body, and conclusion:\n{article}\n"
  t1_start = perf_counter()

  logger.info("Summarizing articles...")
  tokenizer = AutoTokenizer.from_pretrained("google/long-t5-tglobal-base")
  model = LongT5ForConditionalGeneration.from_pretrained("google/long-t5-tglobal-base")

  if torch.cuda.is_available():
      model = model.to('cuda')

  chunk_size = 4000  # You can adjust this based on your model's max input length
  chunks = [prompt[i:i + chunk_size] for i in range(0, len(prompt), chunk_size)]

  summaries = []

  # TODO: Multiprocess
  for chunk in chunks:
      inputs = tokenizer(chunk, return_tensors="pt", truncation=True, max_length=512)

      if torch.cuda.is_available():
          inputs = {key: value.to('cuda') for key, value in inputs.items()}

      summary_ids = model.generate(inputs['input_ids'],
                                    max_length=300,
                                    min_length=100,
                                    num_beams=4,
                                    length_penalty=2.0,
                                    early_stopping=True)

      chunk_summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
      summaries.append(chunk_summary)

  # Combine the summaries from all chunks
  t1_stop = perf_counter()
  final_summary = " ".join(summaries)


  logger.info("Final Summary: " + final_summary)
  logger.info(f"Elapsed time during the summarize in seconds:{t1_stop-t1_start}")

def translate_content():
  pass

def post_articles():
  pass

def create_video():
  pass

def post_videos():
  pass





def main():
  summarize_articles()