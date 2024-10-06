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
    filename='Analysis/Scraper/scraper_log2.log',
    filemode='w',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def get_rating(node):
    rating_element = node.find('span', {'class': 'RatingStars'})
    if rating_element and 'aria-label' in rating_element.attrs:
        rating_text = rating_element['aria-label']
        rating = rating_text.split()[1]
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

# Scrape page and parse HTML with retries
def fetch_goodreads_reviews(url, driver, retries=3):
    for attempt in range(retries):
        try:
            driver.get(url)
            time.sleep(3)
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            return soup
        except Exception as e:
            logging.error(f"Error fetching page: {e}. Retrying... {attempt + 1}/{retries}")
            time.sleep(random.uniform(10, 20))
    
    logging.error(f"Failed to fetch page after {retries} attempts.")
    return None

# Click 'Show more reviews' button
def click_show_more_reviews(driver):
    try:
        if len(driver.find_elements(By.XPATH, '//span[@data-testid="loadMore"]/ancestor::button')) == 0:
            logging.info("No 'Show more reviews' button found, all reviews are loaded.")
            return False
        
        wait = WebDriverWait(driver, 20)
        show_more_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//span[@data-testid="loadMore"]/ancestor::button')))
        
        driver.execute_script("arguments[0].click();", show_more_button)
        time.sleep(3)
        return True
    except TimeoutException:
        logging.info("Timed out waiting for 'Show more reviews' button to become clickable.")
        return False
    except Exception as e:
        logging.info(f"Error clicking 'Show more reviews': {e}")
        return False

# Retrieve all reviews from a Goodreads review URL
def get_all_reviews(url, goodreads_id, driver, base_path):
    # initialize csv file path to save
    filename = f"{base_path}/{goodreads_id}_reviews.csv"

    # Check if file exists to decide whether to write header
    file_exists = os.path.isfile(filename)

    # initialize review saver
    soup = fetch_goodreads_reviews(url, driver)

    if soup is None:
        logging.error(f"Failed to retrieve reviews for {goodreads_id}")
        return
    
    scraped_review_urls = set()  # Unique identifiers for reviews (user url -- one can only rate a book once)

    while True:
        new_reviews = []
        review_cards = soup.find_all('article', {'class': 'ReviewCard'})
        
        for review in review_cards:
            user_url = get_user_url(review)

            if user_url in scraped_review_urls:
                continue

            review_data = {
                "user_name": get_user_name(review),
                "user_url": user_url,
                "rating": get_rating(review),
                "date": get_date(review),
                "text": get_text(review),
                "likes": get_num_likes(review),
                "shelves": get_shelves(review)
            }
            new_reviews.append(review_data)
            scraped_review_urls.add(user_url)
        
        if len(new_reviews) > 0:
            df = pd.DataFrame(new_reviews)

            try:
                # Append to the CSV file, only write header if it's a new file
                df.to_csv(filename, index=False, mode='a', header=not file_exists)
                file_exists = True  # Once written, future writes won't need header
                logging.info(f"Saved {len(new_reviews)} reviews for book ID: {goodreads_id} to {filename}")
            except Exception as e:
                logging.error(f"Error writing reviews to file {filename}: {e}")

        if not click_show_more_reviews(driver):
            break  # No more reviews to show, stop scraping

        soup = BeautifulSoup(driver.page_source, 'html.parser')


# Retrieve goodreads id from metadata file
def read_goodreads_ids(file_path, sheet_name="BOOK_SHEET"):
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    goodread_ids = df['goodreads_id'].tolist()
    return goodread_ids

# Generate goodreads review URL from goodreads id
def generate_goodreads_review_url(goodreads_id):
    return f"https://www.goodreads.com/book/show/{goodreads_id}/reviews"

def get_random_user_agent(user_agents):
    return random.choice(user_agents)

# Main function
def main():
    user_agents = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.3",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.3"]
    
    base_path = "Data/Reviews_Scraped/Raw"
    metadata_file_path = "Data/Goodreads_Comics_Data/Data_Files/Masterdata_ongoing.xlsx"
    goodreads_ids = read_goodreads_ids(metadata_file_path)

    driver = init_driver(get_random_user_agent(user_agents))

    for i, goodreads_id in enumerate(goodreads_ids[130:], start=130):
        logging.info(f"Scraping reviews for book with Goodreads ID: {goodreads_id}")
        url = generate_goodreads_review_url(goodreads_id)
        get_all_reviews(url, goodreads_id, driver, base_path)

        if (i + 1) % 10 == 0:  # Restart WebDriver after every 10 books
            logging.info("Restarting WebDriver...")
            driver.quit()
            time.sleep(5)
            driver = init_driver(get_random_user_agent(user_agents))

        time.sleep(random.uniform(10, 20))

    driver.quit()

if __name__ == "__main__":
    main()
