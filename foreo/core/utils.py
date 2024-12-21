from time import perf_counter
import re
import colorlog
import logging



def clean_article_text(article: str) -> str:
    """
    This function removes unwanted content such as brand names, newspaper names, and ads.
    """
    # Remove common ad phrases or text that typically appear in articles
    ad_keywords = [
        "read this", "watch this", "advertisement", "sponsored", "brought to you by",
        "subscribe now", "learn more", "buy now", "follow us", "like this", "click here"
    ]

    # Remove specific brand or newspaper names (you can expand this list)
    brand_names = ["New York Times", "CNN", "BBC", "Forbes", "Reuters", "Allure"]  # Example
    ad_keywords_pattern = "|".join([re.escape(keyword) for keyword in ad_keywords])
    brand_names_pattern = "|".join([re.escape(brand) for brand in brand_names])

    # Remove the unwanted content
    article_cleaned = re.sub(ad_keywords_pattern, "", article, flags=re.IGNORECASE)
    article_cleaned = re.sub(brand_names_pattern, "", article_cleaned, flags=re.IGNORECASE)

    # Remove extra whitespace after removal
    article_cleaned = re.sub(r'\s+', ' ', article_cleaned).strip()

    return article_cleaned


def elapsed_time(logger):
    def decorator(func):
        def wrapper(*args, **kwargs):
            t1_start = perf_counter()
            result = func(*args, **kwargs)
            t1_stop = perf_counter()
            logger.info(f"Elapsed time during {func.__name__} in seconds: {t1_stop - t1_start}")
            return result
        return wrapper
    return decorator
