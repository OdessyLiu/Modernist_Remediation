# Modernist Remediation: Deciphering the Graphic Biography Genre with Goodreads Data
 
This project uses **Digital Humanities (DH)** methods to investigate the genre of **Graphic Biographies** perceived by the readers with **Goodreads review** data and metadata. 

This project is a sub-project of *“Modernist Remediations: Embodiment, Technology, and Cultural Memory”* of the ReMedia Lab, UBC Okanagan. 

## Project Overview

Graphic Biographies are biographical stories narrated in the graphic novel or comics format. How do the readers connect with the book and the subjects of the biographies emotionally through the new genre of image-text narrative? This project aims to answer this broad question with Goodreads review data. 

Also, about a quater of graphic biographies feature figures from the early-twentieth century; we would like to reveal how the genre and artistic format mediate the perception the specific modernist figures with evaluative and affective book reviews. 

**Research Questions**

This project seeks to answer the following research questions *(ongoing)*:

- Do readers explicitly combine evaluation with emotion in reviews of graphic biography?
- What vocabulary do they use when they do so?

**Status**

This project is **in progress**. 

## What's in this repository

```
Analysis/            # Jupyter notebooks & analysis scripts
├── Emotion&Keyness/      # Experiemnt for readers' emotional modeling
Data/                # Main datasets and small testing datasets
├── Goodreads_Comics_Data/      # folder for metadata of graphic biographies
├── Tags/                       # folder for tags(shelves) information
├── Reviews/                    # folder for scraped reviews
Figures/             # Plots and exported visuals
Results/             # Other outputs
Scraper/             # Goodreads scraper
ReMedia_Updates_Documentation.md  # Project change log / notes
```

## Quick start

### To view the progress & results

To veiw the documented current progress and results, please see [ReMedia_Updates_Documentation.md](ReMedia_Updates_Documentation.md).

To view the figures, please see [Figures/](Figures).

To view other details of the project, please visit [the lab website](https://ecbmurphy.github.io/ReMedia_DigitalHumanities/).

### To reproduce

#### 1. Scrape reviews

The scraper is located in the [Scraper/](Scraper) folder. Please download the folder and follow the [README](Scraper/README.md) file. 

- **Requirements:** Python 3.10 and dependencies, see [README](Scraper/README.md) file
- **Setup:**
  - Create and activate a virtual environment (conda/venv).
  - `cd` to the scraper's folder and run `pip install -r requirements.txt`
- **Goodreads IDs:** To run the scraper, you will need the Goodreads IDs for the books, which are stored in the [metadata files](Data/Goodreads_Comics_Data/Data_Files).
- **Review cleaning:** To clean the reviews and calculate the review statistics, please see [Analysis/Reviews_CleaningStatistics.ipynb](Analysis/Reviews_CleaningStatistics.ipynb).

#### 2. Emotion analysis and keyness analysis

This experiment aims to investigate the readers' emotional response toward the graphic biographies books, the books' subjects, and the genre, reflected in the book reviews. 

The detailed experiment is located in the [Analysis/Emotion&Keyness/](Analysis/Emotion&Keyness) folder. 

- **Files**
  - **[ValenceArousalAnalysis.ipynb](Analysis/Emotion&Keyness/ValenceArousalAnalysis.ipynb)**: Notebook for applying valence & arousal prediction to the book reviews.
  - **[VA_KeynessAnalysis.md](Analysis/Emotion&Keyness/VA_KeynessAnalysis.md)**: Documentation for keyness analysis. 
- **Tools:**
  - [Multilingual_VA_prediction](https://github.com/gmendes9/multilingual_va_prediction) (Mendes & Martins, 2023)
  - [Sketch Engine](https://www.sketchengine.eu/)

#### 3. Tag statistics

TBC

## Data

## How to cite

## References

## Contributors

👩‍🏫 **PI:** Dr. Emily Christina Murphy

🧠 **Research assistants:**

  - Qilin (Odessy) Liu, M.A., @[OdessyLiu](https://github.com/OdessyLiu)
  - Julie Carr

🔗 For more about the project and ReMedia Lab, please visit [our website](https://remediaresearch.ca/).