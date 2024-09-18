import argparse
from datetime import datetime
import json
import os
import re
import time

from urllib.request import urlopen
from urllib.error import HTTPError
import bs4
import pandas as pd


def get_all_lists(soup):

    lists = []
    list_count_dict = {}

    if soup.find('a', text='More lists with this book...'):

        lists_url = soup.find('a', text='More lists with this book...')['href']

        source = urlopen('https://www.goodreads.com' + lists_url)
        soup = bs4.BeautifulSoup(source, 'lxml')
        lists += [' '.join(node.text.strip().split()) for node in soup.find_all('div', {'class': 'cell'})]

        i = 0
        while soup.find('a', {'class': 'next_page'}) and i <= 10:

            time.sleep(2)
            next_url = 'https://www.goodreads.com' + soup.find('a', {'class': 'next_page'})['href']
            source = urlopen(next_url)
            soup = bs4.BeautifulSoup(source, 'lxml')

            lists += [node.text for node in soup.find_all('div', {'class': 'cell'})]
            i += 1

        # Format lists text.
        for _list in lists:
            # _list_name = ' '.join(_list.split()[:-8])
            # _list_rank = int(_list.split()[-8][:-2]) 
            # _num_books_on_list = int(_list.split()[-5].replace(',', ''))
            # list_count_dict[_list_name] = _list_rank / float(_num_books_on_list)     # TODO: switch this back to raw counts
            _list_name = _list.split()[:-2][0]
            _list_count = int(_list.split()[-2].replace(',', ''))
            list_count_dict[_list_name] = _list_count

    return list_count_dict


def get_shelves(soup):

    shelf_count_dict = {}
    
    if soup.find('a', text='See top shelves…'):

        # Find shelves text.
        shelves_url = soup.find('a', text='See top shelves…')['href']
        source = urlopen('https://www.goodreads.com' + shelves_url)
        soup = bs4.BeautifulSoup(source, 'lxml')
        shelves = [' '.join(node.text.strip().split()) for node in soup.find_all('div', {'class': 'shelfStat'})]
        
        # Format shelves text.
        shelf_count_dict = {}
        for _shelf in shelves:
            _shelf_name = _shelf.split()[:-2][0]
            _shelf_count = int(_shelf.split()[-2].replace(',', ''))
            shelf_count_dict[_shelf_name] = _shelf_count

    return shelf_count_dict


def get_genres(soup):
    genres = []
    for node in soup.find_all('div', {'class': 'left'}):
        current_genres = node.find_all('a', {'class': 'actionLinkLite bookPageGenreLink'})
        current_genre = ' > '.join([g.text for g in current_genres])
        if current_genre.strip():
            genres.append(current_genre)
    return genres


def get_series_name(soup):
    series_tag = soup.find(id="bookSeries")
    if series_tag:
        series = series_tag.find("a")
        if series:
            series_name = re.search(r'\((.*?)\)', series.text)
            if series_name:
                return series_name.group(1)
    return ""


def get_top_5_other_editions(soup):
    other_editions = []
    for div in soup.findAll('div', {'class': 'otherEdition'}):
      other_editions.append(div.find('a')['href'])
    return other_editions

def get_isbn13(soup):
    try:
        isbn_label = soup.find('div', text='ISBN')
        if isbn_label:
            isbn13_tag = isbn_label
        # 找到 data-testid 为 'contentContainer' 的 <div> 标签
        isbn13_tag = soup.find('div', {'data-testid': 'contentContainer'})
        if isbn13_tag:
            # 只提取13位的ISBN (前面的部分)
            isbn13 = isbn13_tag.text.strip().split()[0]  # 提取第一个数字部分（即ISBN13）
            return isbn13
        else:
            return "isbn13 not found"
    except Exception as e:
        return "isbn13 not found"

def get_original_title(soup):
    try:
        # 找到 <dt> 标签中内容为 'Original title' 的部分
        original_title_tag = soup.find('dt', text='Original title')
        if original_title_tag:
            # 找到与 <dt> 标签对应的下一个 <dd> 标签
            original_title = original_title_tag.find_next('dd').find('div', {'data-testid': 'contentContainer'}).text.strip()
            return original_title
        else:
            return "Original title not found"
    except Exception as e:
        return "Original title not found"


def get_rating_distribution(soup):
    distribution = re.findall(r'renderRatingGraph\([\s]*\[[0-9,\s]+', str(soup))[0]
    distribution = ' '.join(distribution.split())
    distribution = [int(c.strip()) for c in distribution.split('[')[1].split(',')]
    distribution_dict = {'5 Stars': distribution[0],
                         '4 Stars': distribution[1],
                         '3 Stars': distribution[2],
                         '2 Stars': distribution[3],
                         '1 Star':  distribution[4]}
    return distribution_dict


def get_num_pages(soup):
    if soup.find('span', {'itemprop': 'numberOfPages'}):
        num_pages = soup.find('span', {'itemprop': 'numberOfPages'}).text.strip()
        return int(num_pages.split()[0])
    return ''


def get_year_first_published(soup):
    year_first_published = soup.find('nobr', attrs={'class':'greyText'})
    if year_first_published:
        year_first_published = year_first_published.string
        return re.search('([0-9]{3,4})', year_first_published).group(1)
    else:
        return ''

def get_id(bookid):
    pattern = re.compile("([^.-]+)")
    return pattern.search(bookid).group()

def get_cover_image_uri(soup):
    series = soup.find('img', id='coverImage')
    if series:
        series_uri = series.get('src')
        return series_uri
    else:
        return ""
    
def scrape_book(book_id):
    url = 'https://www.goodreads.com/book/show/' + book_id
    source = urlopen(url)
    soup = bs4.BeautifulSoup(source, 'html.parser')

    time.sleep(2)

    # get book title
    book_title_tag = soup.find('h1', {'data-testid': 'bookTitle'})
    if book_title_tag:
        book_title = ' '.join(book_title_tag.text.split())
    else:
        book_title = "Unknown"

    # 提取多个作者名字
    author_tags = soup.find_all('span', {'data-testid': 'name'})
    authors = ', '.join([author_tag.text.strip() for author_tag in author_tags]) if author_tags else "Unknown"

    # 提取评分
    average_rating_tag = soup.find('div', {'class': 'RatingStatistics__rating'})
    if average_rating_tag:
        average_rating = average_rating_tag.text.strip()
    else:
        average_rating = "Unknown"

    # 提取评分数
    num_ratings_tag = soup.find('span', {'data-testid': 'ratingsCount'})
    if num_ratings_tag:
        num_ratings = num_ratings_tag.text.strip().split()[0]  # 提取数字
    else:
        num_ratings = "Unknown"

    # 提取评论数
    num_reviews_tag = soup.find('span', {'data-testid': 'reviewsCount'})
    if num_reviews_tag:
        num_reviews = num_reviews_tag.text.strip().split()[0]  # 提取数字
    else:
        num_reviews = "Unknown"

    return {
        'book_id_title':        book_id,
        'book_id':              get_id(book_id),
        # 'cover_image_uri':      get_cover_image_uri(soup),
        'book_title':           book_title,
        "book_series":          get_series_name(soup),
        # 'top_5_other_editions': get_top_5_other_editions(soup),
        # 'isbn':                 get_isbn(soup),
        'isbn13':               get_isbn13(soup),
        'original_title':       get_original_title(soup),
        'year_first_published': get_year_first_published(soup),
        'author':               authors,
        'num_ratings':          num_ratings,  # 更新为提取的 num_ratings
        'num_reviews':          num_reviews,  # 更新为提取的 num_reviews
        'average_rating':       average_rating,  # 更新为提取的 average_rating
        # 'shelves':              get_shelves(soup),
        # 'lists':                get_all_lists(soup),x``
        # 'rating_distribution':  get_rating_distribution(soup)
    }


def condense_books(books_directory_path):

    books = []
    
    # Look for all the files in the directory and if they contain "book-metadata," then load them all and condense them into a single file
    for file_name in os.listdir(books_directory_path):
        if file_name.endswith('.json') and not file_name.startswith('.') and file_name != "all_books.json" and "book-metadata" in file_name:
            _book = json.load(open(books_directory_path + '/' + file_name, 'r')) #, encoding='utf-8', errors='ignore'))
            books.append(_book)

    return books

def main():

    start_time = datetime.now()
    script_name = os.path.basename(__file__)

    parser = argparse.ArgumentParser()
    parser.add_argument('--book_ids_path', type=str)
    parser.add_argument('--output_directory_path', type=str)
    parser.add_argument('--format', type=str, action="store", default="json",
                        dest="format", choices=["json", "csv"],
                        help="set file output format")
    args = parser.parse_args()

    book_ids              = [line.strip() for line in open(args.book_ids_path, 'r') if line.strip()]
    books_already_scraped =  [file_name.replace('_book-metadata.json', '') for file_name in os.listdir(args.output_directory_path) if file_name.endswith('.json') and not file_name.startswith('all_books')]
    books_to_scrape       = [book_id for book_id in book_ids if book_id not in books_already_scraped]
    condensed_books_path   = args.output_directory_path + '/all_books'

    for i, book_id in enumerate(books_to_scrape):
        try:
            print(str(datetime.now()) + ' ' + script_name + ': Scraping ' + book_id + '...')
            print(str(datetime.now()) + ' ' + script_name + ': #' + str(i+1+len(books_already_scraped)) + ' out of ' + str(len(book_ids)) + ' books')

            book = scrape_book(book_id)
            # Add book metadata to file name to be more specific
            json.dump(book, open(args.output_directory_path + '/' + book_id + '_book-metadata.json', 'w'))

            print('=============================')

        except HTTPError as e:
            print(e)
            exit(0)


    books = condense_books(args.output_directory_path)
    if args.format == 'json':
        json.dump(books, open(f"{condensed_books_path}.json", 'w'))
    elif args.format == 'csv':
        json.dump(books, open(f"{condensed_books_path}.json", 'w'))
        book_df = pd.read_json(f"{condensed_books_path}.json")
        book_df.to_csv(f"{condensed_books_path}.csv", index=False, encoding='utf-8')
        
    print(str(datetime.now()) + ' ' + script_name + f':\n\n🎉 Success! All book metadata scraped. 🎉\n\nMetadata files have been output to /{args.output_directory_path}\nGoodreads scraping run time = ⏰ ' + str(datetime.now() - start_time) + ' ⏰')



if __name__ == '__main__':
    main()
