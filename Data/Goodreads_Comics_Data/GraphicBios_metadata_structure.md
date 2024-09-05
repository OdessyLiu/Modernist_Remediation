# Graphic Biography Database Structure Documentation

## 1. Overview

This document provides a comprehensive overview of the database structure used for managing Goodreads_Reviews_Masterdata (the metadata of graphic biographies collected for analyses). The data is organized across multiple Excel sheets, each storing different entities and their relationships.

- **Entities:** book;
- **Attributes:** ID, website, ISBN, contributor(s), ...

## 2. Tables/sheets description

### 2.1 ID_SHEET

- **Description:** Stores the unique IDs of the books;
- **Fields:** 
    - **id:** Unique identifier of each book, within the dataset;
    - **isbn:** Unique identifier of each book, universal; International Standard Book Numbers;
    - **goodreads_id** Unique identifier of each book, within Goodreads;


### 2.2 BOOK_SHEET

- **Description:** Stores basic information about the books;
- **Fields:**
  - **id:** Unique identifier of each book, within the dataset;
  - **title_primary:** The primary title of each book, in English;
  - **title_secondary:** The seconary title (subtitle) of each book, in English (*na* if none);
  - **language:** The language of the original version of each book, in ISO language code; 
  - **publication_date:** The year that the book was published;
  - **publisher:** The publisher of the book;
  - **contributor_number:** The number of contributors of the book, on Goodreads;
  - **author01:** The primary author of the book, showed as the first on Goodreads;  
  - ... (other contributors -- authors, illustrators, performers, drawings, translators, etc.; final columns depend on books;)

### 2.3 SUBJECT_SHEET

- **Description:** Stores

### 2.4 BOOK_SUBJECT_RELATION_SHEET

### 2.5 TRANSLATION_SHEET
- **Description:** Stores information about translated books;
- **Fields:** 
  - **id:** Unique identifier of each book, within the dataset;
  - **is_from_translation:** a binary categorization *(0 -- not from translation, 1 -- is from translation)*, indicating if the book was translated from different language;
  - **isbn_original:** The ISBN of the original version of each book;
  - **goodreads_id_original:** The unique Goodreads ID of the original version of each book;
  - **title_original:** The title, both primary and secondary (subtitle), of each book, in its original language (*na* if not from translation);
  - **language_original:** The language of the original version of each book, in ISO language code; 
  - **publication_date_original:** The year that the original book was published;
  - **publisher_original:** The publisher of the book's original version;

## 3. Data relationships

## 4. Guideline for datamanagement 