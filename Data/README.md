# /Data

**Description**: File path for all data files

## /Goodreads_Comics_Data

**Description**: Path for Goodreads comics data metadata

### /GraphicBios.xlsx (Original)

**Description**: Old metadata file, *Archived*

### /GraphicBiosNew.xlsx (Original)

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

### /GraphicBiosCleaned.csv (New)

**Description**: A cleaned csv data from GraphicBiosNew.xlsx

- 9 columns:
    - URL
    - ISBN
    - Goodreads ID
    - Title
    - Author(s)/Illustrators/Other Contributors (Editors, Translators, Sources, etc.)
    - Categorization
    - Subject(s)
    - Gender
    - Career Type/Known For

## /Web-Scraped_Data

**Description**: Book reviews scraped from Goodreads.

### /AllReviews_135_Unique.csv (New)

**Description**: Cleaned and merged review data from /Raw/AllReviews/MainDataset

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


<br/>
<br/>

# Data information

229 graphic comics in total

135 book review data collected