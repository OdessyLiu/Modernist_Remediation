import time
import pandas as pd
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import random
import logging

# Set up logging
logging.basicConfig(
    filename='Analysis/Scraper/scraper_log.log',
    filemode='w',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def get_rating(node):
    # Finding the RatingStars element that contants aria-label attribute
    rating_element = node.find('span', {'class': 'RatingStars'})
    if rating_element and 'aria-label' in rating_element.attrs:
        # Retrieving the ratings from aria-label, i.e., "Rating 3 out of 5"
        rating_text = rating_element['aria-label']
        rating = rating_text.split()[1]  # Extracting the rating value
        return rating
    return ''

def get_user_name(node):
    user_element = node.find('div', {'class': 'ReviewerProfile__name'})
    if user_element:
        return user_element.find('a').text
    return ''

def get_user_url(node):
    user_element = node.find('div', {'class': 'ReviewerProfile__name'})
    if user_element:
        return user_element.find('a')['href']
    return ''

def get_date(node):
    date_element = node.find('span', {'class': 'Text Text__body3'})
    if date_element:
        return date_element.find('a').text
    return ''

def get_text(node):
    text_element = node.find('div', {'class': 'TruncatedContent__text TruncatedContent__text--large'})
    if text_element:
        return text_element.text.strip()
    return ''

def get_num_likes(node):
    likes_element = node.find('div', {'data-testid': 'stats'})
    if likes_element:
        likes_text = likes_element.find('span', {'class': 'Button__labelItem'}).text
        if 'likes' in likes_text:
            return int(likes_text.split()[0])
    return 0

def get_shelves(node):
    shelves = []
    shelves_element = node.find_all('a', {'class': 'Button Button--tag Button--medium'})
    if shelves_element:
        for shelf in shelves_element:
            shelves.append(shelf.text.strip())
    return shelves

# Set up and initialize WebDriver
def init_driver(user_agent):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument(user_agent)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    return driver

# Scrape page and parse HTML
def fetch_goodreads_reviews(url, user_agent):
    driver = init_driver(user_agent)
    driver.get(url)
    
    time.sleep(3)  # wait for the page to load
    html = driver.page_source

    soup = BeautifulSoup(html, 'html.parser')
    return soup, driver

# Click 'Show more reviews' button
def click_show_more_reviews(driver):
    try:
        # Check if 'Show more reviews' button is present
        if len(driver.find_elements(By.XPATH, '//span[@data-testid="loadMore"]/ancestor::button')) == 0:
            logging.info("No 'Show more reviews' button found, all reviews are loaded.")
            return False
        
        # Use WebDriverWait to wait for the 'Show more reviews' button to become clickable
        wait = WebDriverWait(driver, 20)
        show_more_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//span[@data-testid="loadMore"]/ancestor::button')))
        
        # Use JavaScript to click the button
        driver.execute_script("arguments[0].click();", show_more_button)
        time.sleep(3)  # wait for the page to load
        return True
    except TimeoutException:
        logging.info("Timed out waiting for 'Show more reviews' button to become clickable.")
        return False
    except Exception as e:
        logging.info(f"Error clicking 'Show more reviews': {e}")
        return False


# Retrieve all reviews from a Goodreads review URL
def get_all_reviews(url, user_agent):
    soup, driver = fetch_goodreads_reviews(url, user_agent)
    reviews = []

    while True:
        review_cards = soup.find_all('article', {'class': 'ReviewCard'})
        for review in review_cards:
            review_data = {
                "user_name": get_user_name(review),
                "user_url": get_user_url(review),
                "rating": get_rating(review),
                "date": get_date(review),
                "text": get_text(review),
                "likes": get_num_likes(review),
                "shelves": get_shelves(review)
            }
            reviews.append(review_data)

        if not click_show_more_reviews(driver):
            break  # no more reviews to show, stop scraping

        # update soup
        soup = BeautifulSoup(driver.page_source, 'html.parser')

    driver.quit()
    return reviews

# Retrieve goodreads id from metadata file
def read_goodreads_ids(file_path, sheet_name = "BOOK_SHEET"):
    df = pd.read_excel(file_path, sheet_name = sheet_name)
    goodread_ids = df['goodreads_id'].tolist()
    return goodread_ids

# Generate goodreads review URL from goodreads id
def generate_goodreads_review_url(goodreads_id):
    return f"https://www.goodreads.com/book/show/{goodreads_id}/reviews"

# Save each book's reviews to CSV
def save_reviews_to_csv(reviews, goodreads_id, base_path):
    if not os.path.exists(base_path):
        os.makedirs(base_path)
    
    filename = f"{base_path}/{goodreads_id}_reviews.csv"
    df = pd.DataFrame(reviews)
    df.to_csv(filename, index=False)
    logging.info(f"Reviews saved to {filename}")

# Main function
def main():
    user_agent  = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    base_path = "Data/Reviews_Scraped/Raw"
    metadata_file_path = "Data/Goodreads_Comics_Data/Data_Files/Masterdata_ongoing.xlsx"
    goodreads_ids = read_goodreads_ids(metadata_file_path)
    
    for goodreads_id in goodreads_ids[7:8]:
        logging.info(f"Scraping reviews for book with Goodreads ID: {goodreads_id}")
        url = generate_goodreads_review_url(goodreads_id)
        all_reviews = get_all_reviews(url, user_agent)
        if len(all_reviews) == 0:
            logging.info(f"No reviews found for book with Goodreads ID: {goodreads_id}")
            return
        save_reviews_to_csv(all_reviews, goodreads_id, base_path)
        time.sleep(random.uniform(5, 10))

if __name__ == "__main__":
    main()
