# Graphic Biography Database Structure Documentation

## 1. Overview

This document provides a comprehensive overview of the database structure used for managing Goodreads_Reviews_Masterdata (the metadata of graphic biographies collected for analyses). The data is organized across multiple Excel sheets, each storing different entities and their relationships.

- **Entity:** book;
  - **Attributes:** ID, website, ISBN, contributor(s), ...
- **Entity:** figure;
  - **Attributes:** ID, name, gender, career, ...

## 2. Tables/sheets description

### 2.1 BOOK_SHEET

- **Description:** Stores basic information about the books;
- **Fields:**
  - **book_id:** Unique identifier of each book, within the dataset;
  - **isbn:** Unique identifier of each book, universal; International Standard Book Numbers;
  - **goodreads_id** Unique identifier of each book, within Goodreads;
  - **title:** The primary title of each book, in English;
  - **subtitle:** The subtitle of each book, in English (*na* if none);
  - **publication_date:** The year that the book was published;
  - **publisher:** The publisher of the book;
  - **contributor_number:** The number of contributors of the book, on Goodreads;
  - **contributors:** The contributors of the book, as shown on Goodreads; stored in *list* format, i.e., ["Author 1", "Author 2", "Author 3"]; the first item in the list is considered as the primary author/contributor of the book;

### 2.2 FIGURE_SHEET

- **Description:** Stores information about graphic biography subject, within the dataset; the subjects include single figures, as well as groups (i.e., bands);
- **Fields:**
  - **figure_id:** The unique identifier of the graphic biography subject;
  - **figure_name:** The name of the graphic biography subject;
  - **figure_gender:** The gender of the graphic biography subject (*mixed* if a group);
  - **figure_career:** In which career or field that the graphic biography subject is known for, saved in *list* format, i.e., ["professor", "political activist"];
  - **figure_birth:** The year of birth of the graphic biography subject (*na* if not traceable or applicable);
  - **figure_death:** The year of death of the graphic biography subject (*na* if not traceable or applicable);
  - **figure_active_start:** The year from which the graphic biography subject became active in their field (i.e., first book publication, first song/movie release, etc.);
  - **figure_active_end:** The year in which the graphic biography subject ended activities in their field (*na* if not traceable or applicable);

### 2.3 FIGURE_PERIOD_SHEET

- **Description:** Stores the one-to-many relationship of graphic biography subject(s) with their active period;
- **Fields:**
  - **figure_id:** The unique identifier of the graphic biography subject;
  - **figure_active_period:** The active periods of a graphic biography subject;


### 2.4 BOOK_FIGURE_SHEET

- **Description:** Stores the many-to-many relationship between BOOK_SHEET and FIGURE_SHEET;
- **Fields:**
  - **book_id:** The unique identifier of each book, within the dataset;
  - **figure_id:** The unique identifier of the graphic biography subject;

### 2.5 TRANSLATION_SHEET

- **Description:** Stores information about translated books;
- **Fields:** 
  - **book_id:** Unique identifier of each book, within the dataset;
  - **is_from_translation:** Binary indicators of if the book was translated from different language, *0* if is not from translation, *1* if is from translation;
  - **isbn_original:** The ISBN of the original version of each book;
  - **goodreads_id_original:** The unique Goodreads ID of the original version of each book;
  - **title_original:** The title, both title and subtitle, of each book, in its original language (*na* if not from translation);
  - **language_original:** The language of the original version of each book, in ISO language code; 
  - **publication_date_original:** The year that the original book was published;
  - **publisher_original:** The publisher of the book's original version;

## 3. Data relationships

- **BOOK and SUBJECT:** many-to-many relationship;
- **SUBJECT and subject active PERIOD:** one-to-many relationship, one subject with multiple active periods;

## 4. Guideline for datamanagement 

### 4.1 Data updates

All updates to the data should be made directly in the respective Excel sheets. Ensure consistency across related fields, such as *book_id* and *subject_id*. Make sure the old version is committed to Github before updating the dataset.

### 4.2 Queries and analysis

For complex queries and data analysis, it is recommended to use *Python* with the *pandas* library. This allows for efficient data manipulation and integration across different data sources.

### 4.3 Version control

The dataset is saved on Github repository [Modernist_Remediation_ReMedia](https://github.com/OdessyLiu/Modernist_Remediation_ReMedia) (currently a private repository) for version control purpose. 

Path: Data/Goodreads_Comics_Data/Masterdata_ongoing.xlsx

The dataset should be committed to Github before each update. 

Changes to the project files will be updated to Teams weekly (by the end of every Sunday).