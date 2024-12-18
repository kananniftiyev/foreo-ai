# Foreo - AI

## Pipeline Overview

- Fetching Articles
  The fetch_news() function fetches articles from Allure's Trends section using requests and parses the content using BeautifulSoup. Only the first 3 articles are fetched.

- Summarizing Articles
  The summarize_articles() function takes the fetched articles and combines them into a single long string. The content is then cleaned (using the clean_article_text() utility) to remove unwanted text such as ads and irrelevant content.
  A prompt is prepared for the AI model, and the text is chunked to ensure that the model's input limit is respected.
  Using the LongT5 model from Hugging Face's transformers, the article is summarized into a coherent structure (with an introduction, body, and conclusion).

- Posting Articles
  Placeholder functions for posting articles (post_articles()) are provided but need to be implemented based on the platform (e.g., Medium or Substack).
  The post_articles() function is where integration with the Substack API or Medium API would occur. You'll need to use the respective platform's API to post the summarized articles.

- Translation (To be implemented)
  translate_content(): This function is meant to handle translation of articles or summaries into different languages. You can integrate with translation APIs like Google Translate or DeepL here.

- Creating Videos (To be implemented)
  create_video(): Placeholder function for creating videos from the summarized articles. This could include generating a video script, voiceover, and using libraries like moviepy to combine images or video clips.

- Posting Videos (To be implemented)
  post_videos(): Placeholder function for posting the generated videos to platforms like YouTube or Vimeo.

- Performance Optimization (Future Work)
  The summarize_articles() function currently processes the chunks sequentially. Multiprocessing or multi-threading is suggested for faster processing, especially when handling long texts.

  ## How to run project

  Clone the project

```bash
  git clone https://link-to-project
```

Go to the project directory

```bash
  cd my-project
```

Enter Shell mode

```bash
  poetry shell
```

Install dependencies

```bash
  poetry install
```

Run Project

```bash
  poetry run foreo
```
