# Goodreads Review Scraper

## Overview

This project is a web scraper designed to extract book reviews from Goodreads. It fetches user reviews, ratings, and other related data using **Selenium** and **BeautifulSoup** for web scraping. The scraper was initially inspired by [Maria Antoniak's GoodReadsScraper](https://github.com/maria-antoniak/goodreads-scraper), but has been modified to work with Goodreads' current HTML structure and optimized for large-scale data collection.

## Features

- Fetches user reviews, ratings, and metadata from Goodreads.
- Handles pagination using the "Show more reviews" button.
- Saves reviews to CSV files, supporting incremental saving as data is scraped.
- Designed to handle large datasets, with support for writing reviews incrementally to reduce memory load.

## Requirements

Before running the scraper, ensure you have the following packages installed.

### Required Packages

| Package            | Version | Description                                   |
| ------------------ | ------- | --------------------------------------------- |
| `python`           | 3.10.2  | Python programming language                   |
| `selenium`         | 4.24.0  | WebDriver for automating web interactions     |
| `beautifulsoup4`   | 4.12.0  | For parsing HTML pages                        |
| `pandas`           | 2.1.4   | For managing and storing scraped data in CSV  |
| `webdriver_manager`| 4.0.2   | To manage WebDriver installation automatically|
| `bs4`              | 0.0.2   | For BeautifulSoup functionality               |
| `regex`            | 2022.10.31 | Regular expressions library                   |
| `logging`          | Native  | For logging scraper activity                  |

### Installation

You can install the required packages using pip. To install all dependencies at once, run:

```bash
pip install -r requirements.txt
