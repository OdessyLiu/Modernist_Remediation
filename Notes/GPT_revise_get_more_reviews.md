问题出现在 `get_all_reviews` 函数中，每次翻页后你重新从页面中解析并获取所有评论，而没有记录哪些评论已经爬取，因此导致重复收集同一页面上的评论。

具体问题在这里：
```python
# update soup
soup = BeautifulSoup(driver.page_source, 'html.parser')

# 解析新的评论（会重新解析所有的评论，包括之前已经解析过的）
review_cards = soup.find_all('article', {'class': 'ReviewCard'})
```

这样每次点击 “Show more reviews” 按钮后，程序会重新加载所有的评论，导致之前爬取的评论再次被解析并添加到 `reviews` 列表中，从而出现重复评论。

### 改进思路：
你需要确保在每次翻页时只收集新加载的评论，避免重复爬取已经处理的评论。

### 改进方案：
1. **使用评论的唯一标识符**：你可以使用每条评论的唯一标识符（如评论的 `id` 属性）来跟踪哪些评论已经被收集。
2. **只处理新加载的评论**：每次翻页后，只处理新加载的部分，而忽略之前已经爬取的评论。

### 代码改进：
以下是改进的 `get_all_reviews` 函数，使用评论的唯一 `user_url` 来跟踪已爬取的评论，并确保每次翻页后只处理新的评论。

```python
def get_all_reviews(url, user_agent):
    soup, driver = fetch_goodreads_reviews(url, user_agent)
    
    if soup is None:
        logging.error(f"Failed to retrieve reviews for {url}")
        return []
    
    reviews = []
    scraped_review_urls = set()  # 用于存储已经处理过的评论的唯一标识符 (如 user_url)

    while True:
        review_cards = soup.find_all('article', {'class': 'ReviewCard'})
        new_reviews_count = 0  # 记录新评论的数量

        for review in review_cards:
            user_url = get_user_url(review)
            
            # 如果评论已经爬取，跳过
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
            
            reviews.append(review_data)
            scraped_review_urls.add(user_url)  # 记录已经爬取的评论
            new_reviews_count += 1

        logging.info(f"Found {new_reviews_count} new reviews.")

        # 如果没有找到新的评论，退出循环
        if new_reviews_count == 0:
            logging.info("No more new reviews found.")
            break

        if not click_show_more_reviews(driver):
            break  # No more reviews to load, stop scraping

        # 更新 soup 以包含新加载的页面内容
        soup = BeautifulSoup(driver.page_source, 'html.parser')

    driver.quit()
    return reviews
```

### 改进要点：
1. **`scraped_review_urls` 集合**：该集合存储已经爬取过的评论的 `user_url`，确保每个评论只处理一次。
2. **只处理新评论**：在每次翻页时，只处理新的评论（根据 `user_url` 是否在 `scraped_review_urls` 中判断）。
3. **检查新评论数量**：如果翻页后没有发现新的评论，则结束爬取过程，避免无效翻页。

通过这样的改进，爬虫在翻页时只会处理新加载的评论，避免了重复爬取的问题。