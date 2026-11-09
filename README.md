# Texas WARN layoff analysis (2020 – Oct 2026)

An analysis of layoffs across organizations and across Texas, built from the
Texas Workforce Commission's WARN Act notices:
<https://www.twc.texas.gov/data-reports/warn-notice>

Every notice in this data is for a Texas worksite. "Across the state" here
means across Texas's 28 workforce regions (WDAs), its counties and its cities.

**Interactive dashboard:** https://claude.ai/artifact/CeGjGLp8bxRPxF41icPHGw

## Key findings

Data covers notices dated **Jan 3, 2020 to Nov 3, 2026**: **2,279 notices,
206,019 workers, 1,327 organizations, 136 counties**.

| Year | Notices | Workers | Median notice size |
|---|---:|---:|---:|
| 2020 | 1,206 | 90,990 | 47 |
| 2021 | 123 | 13,413 | 67 |
| 2022 | 86 | 7,303 | 60 |
| 2023 | 224 | 24,000 | 66 |
| 2024 | 237 | 27,627 | 45 |
| 2025 | 289 | 26,630 | 60 |
| 2026 (to Nov 3) | 114 | 16,056 | 90 |

- **COVID dominates.** 2020 alone accounts for 44% of all affected workers.
  Most of those notices came from restaurants, hotels and oilfield companies
  in March to May 2020.
- **The new normal is about 24k to 28k workers a year** (2023 to 2025), up
  from 2021 and 2022.
- **2026 is lower but lumpier.** To Nov 3 there were 16,056 workers, which is
  **−27.4%** against the same window in 2025 (22,110). There were fewer than
  half as many notices (114 vs 266), but the median notice is much larger
  (90 vs 60 workers).
- **Largest organizations overall:** Halliburton (5,664 workers), Zachry
  (4,536, mostly the 2024 Golden Pass LNG notice at Sabine Pass), Walmart
  (3,324), American Airlines (3,284), Pappas Restaurants (3,195), Aramark
  (3,175), Hooters (3,025) and Tesla (2,738).
- **2026 so far:** Republic National Distributing (1,903, across 5 sites),
  Conifer Health Solutions (1,037), Spirit Airlines (959), Sodexo (672) and
  First Brands (658).
- **Repeat filers:** these are contract food-service firms and prison
  operators, whose layoffs follow contract changes. Sodexo filed in 6 of 7
  years; MTC and Compass Group each filed in 5.
- **Geography follows the metros.** The Gulf Coast (Houston) region has 22.4%
  of workers, then Dallas County 14.9%, Tarrant County 11.6%, Alamo (San
  Antonio) 10.6% and Capital Area (Austin) 9.0%. Together these five regions
  hold about two thirds of the total. The top counties are Harris, Dallas,
  Tarrant, Bexar and Travis.
- **Size:** 45% of notices cover fewer than 50 workers. The 47 notices of
  500+ workers make up 22% of all affected workers.
- **Warning time:** 78% of notices give less than 60 days between the notice
  date and the first layoff date. Leaving out 2020, the share runs
  between 50% and 75% a year. The WARN Act's exceptions allow shorter notice in
  some cases.

## Project layout

```
scripts/download.sh   fetch yearly XLSX files from TWC into raw/
scripts/clean.py      combine, dedupe, normalize organizations -> data/
scripts/analyze.py    sector tags, summary tables, dashboard CSV -> output/
raw/                  original TWC spreadsheets (2020–2026)
data/                 tx_warn_2020_2026_clean.csv (one row per notice)
output/               summary CSVs by organization, region, county, city,
                      sector; summary.json; dashboard CSV
dashboard/index.html  source of the online dashboard page
```

Run it:

```bash
pip install -r requirements.txt
./scripts/download.sh
python scripts/clean.py && python scripts/analyze.py
```

## Method and caveats

- TWC's yearly files overlap (for example, the 2024 file repeats late-2023
  notices). 232 exact duplicate rows were removed, along with 2 "Updated"
  notices that re-filed the same headcount. Other amended notices are kept
  and flagged in `is_amendment`.
- `organization` is derived from the job site name. The cleaning strips
  legal suffixes, site parts (after " - ", parentheses or a double space) and
  "dba" names, and about 150 large employers are matched by hand. Some
  variants will still be split or merged imperfectly.
- `sector` is a keyword match on the name because WARN data has no industry
  code. It is approximate, and about 22% of workers are unclassified.
- WARN notices report *planned* layoffs from employers that the Act covers
  (generally 100+ employees). Actual layoffs can be lower, and smaller
  layoffs are not in this data.
