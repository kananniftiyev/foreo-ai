import requests
from bs4 import BeautifulSoup, Tag
from transformers import AutoTokenizer, LongT5Model, LongT5ForConditionalGeneration
import logging
import json
import time
import torch

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__file__)
torch.set_num_threads(30)

def fetch_news() -> list:
  """

  """
  base_link = "https://www.allure.com"
  links = []
  articles: list = []
  allure_response = requests.get("https://www.allure.com/topic/trends")
  soup = BeautifulSoup(allure_response.text, "html.parser")
  div_headlines: Tag = soup.find("div", class_="summary-list__items")
  headlines: Tag = div_headlines.find_all("a", class_="SummaryItemHedLink-civMjp")


  for link_to_headline in headlines:
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
    time.sleep(3) # Wait three seconds to not detect site



  return articles

def summarize_articles():
    # Fetch the first article
    a = fetch_news()
    article = a[0] + a[1] + a[2]
    prompt = f"Summarize the following articles into a single coherent article with an introduction, body, and conclusion:\n{article}\n"

    # Load tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained("google/long-t5-tglobal-base")
    model = LongT5ForConditionalGeneration.from_pretrained("google/long-t5-tglobal-base")

    # Tokenize the input article
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=5048)

    # Generate summary
    summary_ids = model.generate(inputs.input_ids, max_length=4096, min_length=2048, num_beams=4, length_penalty=2.0, early_stopping=True)

    # Decode the summary
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)

    print(summary)

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