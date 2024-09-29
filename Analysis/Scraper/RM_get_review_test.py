import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup

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
def init_driver():
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    return driver

# Scrape page and parse HTML
def fetch_goodreads_reviews(url):
    driver = init_driver()
    driver.get(url)
    
    time.sleep(3)  # wait for the page to load
    html = driver.page_source

    soup = BeautifulSoup(html, 'html.parser')
    return soup, driver

# Click 'Show more reviews' button
def click_show_more_reviews(driver):
    try:
        # Use WebDriverWait to wait for the 'Show more reviews' button to become clickable
        wait = WebDriverWait(driver, 20)
        show_more_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//span[@data-testid="loadMore"]/ancestor::button')))
        
        # Use JavaScript to click the button
        driver.execute_script("arguments[0].click();", show_more_button)
        time.sleep(3)  # wait for the page to load
        return True
    except TimeoutException:
        print("Timed out waiting for 'Show more reviews' button to become clickable.")
        return False
    except Exception as e:
        print(f"Error clicking 'Show more reviews': {e}")
        return False


# Retrieve all reviews from a Goodreads review URL
def get_all_reviews(url):
    soup, driver = fetch_goodreads_reviews(url)
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

# Save to CSV
def save_reviews_to_csv(reviews, filename="Analysis/Scraper/RM_output/27132988-thoreau_reviews.csv"):
    df = pd.DataFrame(reviews)
    df.to_csv(filename, index=False)
    print(f"Reviews saved to {filename}")

# 测试主函数
def main():
    # 使用某本书的 Goodreads 评论页面作为测试
    url = 'https://www.goodreads.com/book/show/27132988-thoreau/reviews'
    all_reviews = get_all_reviews(url)
    save_reviews_to_csv(all_reviews)

if __name__ == "__main__":
    main()
