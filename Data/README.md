```
Data/
├── README.md
├── Goodreads_Comics_Data/      # folder for metadata of graphic biographies
|   ├── _README.txt
|   ├── GraphicBiosNew.xlsx     # original GraphicBios file 
|   ├── GraphicBiosCleaned.csv  # graphicbios metadata file, cleaned from GraphicBiosNew.xlsx
├── Web-Scraped_Data/           # folder for scraped review data
|   ├── Raw/                                    # Raw data of scrapped reviews
|   |   ├── AllReviews/
|   |   |   ├── MainDataset/                    # Raw AllReviews data from 135 books
|   |   |   |   ├── CSV/
|   |   |   |   |   ├── AllReviews.csv
|   |   |   |   |   ├── AllReviews(1).csv
|   |   |   ├── AdditionalTitles/               # Additional Raw AllReviews data from 30 books
|   |   |   |   ├── AllReviews_AdditionalTitles.csv
|   |   ├── FirstPageReviews/                   # ?
|   ├── AllReviews_135_Unique.csv           # AllReviews data, merged and cleaned from MainDataset/
|   ├── AllReviews_Additional_30_Unique.csv # AllReviews_Additional data, merged and cleaned from AdditionalTitles/
|   ├── AllReviews.otd                      # ?
|   ├── FirstPageReviews.otd                # ?
```

</br>
</br>

# File descriptions

## /Goodreads_Comics_Data/GraphicBios.xlsx

Created by @Carr

**Description**: Old metadata file, *Archived*

## /Goodreads_Comics_Data/GraphicBiosNew.xlsx 

Created by @Carr

**Description**: 

- New metadat file
- Sectioned by publishers

**Contents**:

- Notes
- Techinical info: 
    - URL
    - ISBN
    - Goodreads ID
- Basic information: 
    - Title
    - Author(s)/Illustrators/Other Contributors (Editors, Translators, Sources, etc.)
    - Categorization: Biography, Collective Biography, etc.
- Topics
    - Subject(s): the subject of the graphic biography
    - Gender: the gender of the subject
    - Career Type/Known For: field in which the subject was/were active
    - Brow: ?
    - Is Translation?: if the book is translated from other language
- Chronology
    - Active Period
    - Active Period (Well-Known, If Different)
    - Period Covered by Bio (If Provided)
- Publication Info
    - Publication Date
    - Press
    - Imprint(i/A)
    - Original Language
- Translation Info (If Applicable)
    - Original Title
    - Original Publication Date
    - Original Publisher
    - Original URL
    - Original ISBN

## /Goodreads_Comics_Data/GraphicBiosCleaned.csv

Created by @Liu

**Description**: 

A cleaned csv data from GraphicBiosNew.xlsx

**Contents**:

- URL
- ISBN
- Goodreads ID
- Title
- Author(s)/Illustrators/Other Contributors (Editors, Translators, Sources, etc.)
- Categorization
- Subject(s)
- Gender
- Career Type/Known For


## /Web-Scraped_Data/AllReviews_135_Unique.csv

Created by @Liu

**Description**: 

Cleaned and merged review data from /Raw/AllReviews/MainDataset. Contains the reviews from 135 graphic biographis (all in GraphicBiosCleaned.csv)

**Contents**:

- Title
- Review_Author
- Account_Type
- Author_Social_Stats
- Social_Stats
- Review_Date
- Review_Star_Rating: still in html tab format, will extract star rating later
- Review_Text
- Review_Tag_1
- Review_Tag_2
- Review_Tag_3
- Review_Likes
- Title_Rating
- Title_Rating_Distribution

**Questions**:

- What is Account_Type?
- What is the difference between Author_Social_Stats and Social_Stats?
- Are there only 3 tags collected? What about more tags? (or only 3 tags are allowed?)
- What are Title_Rating and Title_Rating_Distribution?

## /Web-Scraped_Data/AllReviews_Additional_30_Unique.csv

Created by @Liu

**Description**: 

Cleaned and merged review data from /Raw/AllReviews/AdditionalTitles. Contains reviews from 30 graphic biographies, 3 from GraphicBiosCleaned.csv (overlapped with AllReviews_135_Unique.csv), and 27 not from GraphicBiosCleaned.csv. 

**Contents**:

- Title
- Review_Author
- Account_Type
- Author_Social_Stats
- Social_Stats
- Review_Date
- Review_Star_Rating: still in html tab format, will extract star rating later
- Review_Text
- Review_Tag_1
- Review_Tag_2
- Review_Tag_3
- Review_Likes
- Title_Rating
- Title_Rating_Distribution

<br/>
<br/>

# Data information

229 graphic comics in total

135 + 27 book review data collected