# YouTube Content Consumption Analysis

## Project Overview

This project explores YouTube content consumption using publicly available data collected through the YouTube Data API.

The data was collected using the YouTube API:

https://www.googleapis.com/youtube/v3

The project focused on videos returned for a set of 10 keywords/categories and was designed to support analysis of videos, channels, keywords, views, and engagement.

---

## Data Collection

Data was extracted from two YouTube Data API endpoints:

- `search` - used to search for videos based on the selected keywords.
- `videos` - used to retrieve additional video metadata and public statistics.

### Search Categories

The analysis covered the following 10 keywords:

- Data Analytics
- Artificial Intelligence
- Career Development
- Business Intelligence
- Machine Learning
- Data Science
- Entrepreneurship
- Technology Trends
- Finance
- Politics

For each keyword, the API was queried across up to 5 search pages, with a maximum of 50 results per page.

### Retrieved Records

The number of videos returned varied by keyword:

| Keyword | Videos Retrieved |
|---|---:|
| Data Analytics | 250 |
| Artificial Intelligence | 250 |
| Career Development | 250 |
| Business Intelligence | 250 |
| Machine Learning | 250 |
| Data Science | 250 |
| Entrepreneurship | 150 |
| Technology Trends | 123 |
| Finance | 250 |
| Politics | 250 |

The API returned statistics for **2,116 unique videos**.

A total of **2,273 records** were saved to:

`youtube_content_consumption.csv`

The difference between total records and unique videos is due to videos appearing in multiple search results across the selected keywords.

---

## ETL Process

The extracted CSV data was imported into Power BI using the **Text/CSV connector**.

The ETL process included:

1. Connecting the CSV file to Power BI.
2. Transforming and cleaning the data using **Power Query**.
3. Creating a data model using a **star schema**.
4. Creating measures for analysis and reporting.
5. Building visualizations and dashboards in Power BI.

---

## Data Model

A star schema was created to organize the data for analysis.

### Fact Table

- `factYoutube_Content`

This table contains the main video-level records and analytical measures such as views, likes, comments, engagement rates, video age, and search information.

### Dimension Tables

- `dimQuery`
- `dimVideos`
- `dimChannels`
- `Date`

The dimension tables are connected to the fact table using one-to-many relationships, with the dimension tables providing descriptive attributes used to filter and analyze the fact data.

---

## Measures

Several Power BI measures were created to support the analysis, including:

- Total Videos
- Unique Videos
- Total Query Categories
- Unique Channels

Additional measures were used to analyze views and engagement across videos, channels, and keywords.

---

## Analysis

The analysis was designed to answer the following questions:

### Content Overview

- What is the total number of videos collected?
- What is the total number of channels collected?
- How many query categories were included in the dataset?

### Channel Analysis

- Which channels appear most frequently across the selected queries?
- Which channels have the highest video views?
- How does channel performance vary across the different queries?

### Keyword Analysis

- Which keywords returned the most videos?
- How do video views and engagement vary across keywords?

### Video Analysis

- Which are the top 10 videos by views?
- Which videos have the highest engagement rates?
- Which video titles appear most frequently or perform most strongly?

Further analysis was conducted to examine individual channel and video performance.

---

## Key Findings

The key findings and visual analysis are presented in the Power BI dashboard included with the project.

The dashboard focuses on:

- Video and channel distribution
- Keyword performance
- Channel popularity
- Video views
- Engagement
- Video title patterns
- Individual channel and video performance

---

## Tools Used

- **YouTube Data API** - Data collection
- **Python** - API data extraction and CSV generation
- **CSV** - Data storage
- **Power Query** - Data transformation
- **Power BI** - Data modelling, analysis, and visualization

---

## Project Workflow

```text
YouTube Data API
       ↓
Data Extraction
       ↓
CSV Dataset
       ↓
Power Query
       ↓
Data Cleaning & Transformation
       ↓
Star Schema
       ↓
DAX Measures
       ↓
Power BI Visualization
       ↓
Content Consumption Analysis