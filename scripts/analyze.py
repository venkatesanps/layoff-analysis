"""Build summary tables + JSON for the Texas WARN layoff report."""
import json, re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA, OUT = ROOT / "data", ROOT / "output"
OUT.mkdir(exist_ok=True)

# Rough keyword-based sector tags (WARN data has no industry field) - approximate only
SECTORS = [
    ("Airlines & aviation", r"airline|airport|aviation|air lines|sky chefs|gate gourmet|swissport|envoy|hmshost|prospect airport|aerosystems|\bdfw\b|jet\b"),
    ("Energy & oilfield", r"oil|gas\b|energy|petrol|drilling|fractur|halliburton|schlumberger|baker hughes|nov\b|nabors|weatherford|exxon|chevron|conoco|shell|refin|pipeline|seadrill|apache|equinor|tenaris|wellhead|pressure pumping|production\b|offshore|lng\b|nextier|propetro|patterson|liberty oilfield|well service|zachry|turner industries|asarco"),
    ("Restaurants & bars", r"restaurant|grill|chang|benihana|diner|breads|brewhouse|punch bowl|otg management|hooters|bar\b|cafe|kitchen|pizza|burger|steak|taco|bbq|bar-b|pappas|landry|dave & buster|del frisco|willie|icehouse|cantina|brewing|food service|sodexo|aramark|compass group"),
    ("Hotels & leisure", r"hotel|hilton|hyatt|marriott|resort|inn\b|suites|gaylord|omni|ritz|cinema|drafthouse|regal|seaworld|sheraton|westin|casino|six flags|cinemark|amc\b|theat|live nation|ymca|club|golf|entertainment|museum"),
    ("Healthcare", r"health|treatment center|hospital|medical|clinic|care\b|rehab|pharma|nursing|hospice|dental|surgical|conifer|optum|mckesson|cardinal|texas children|baylor|md anderson|tenet|labcorp|quest diag"),
    ("Retail", r"walmart|target|macy|jcpenney|dillard|best buy|home depot|lowe|store|retail|mall|bridal|francesca|vroom|pier 1|conn's|fossil|stitch fix|custom ink|sport clips|kroger|h-e-b|walgreen|cvs|boutique|outlet|sears|kmart|bed bath|party city|joann|big lots"),
    ("Transportation & logistics", r"fedex|ups\b|dhl|xpo|freight|logistic|trucking|transport|ryder|geodis|yellow|distribution|warehouse|delivery|distributing|wholesale|chewy|fulfil|fullfil|produce|parking|waitr|scoobeez|amazon|mv transportation|bus\b|transit|herzog|avis|hertz|vehicle"),
    ("Manufacturing", r"manufactur|tesla|plant|steel|metal|tube|paper|foods|tyson|pilgrim|cargill|frito|pepsi|coca|kellogg|packaging|plastic|chemical|industries|semiconductor|samsung|texas instruments|nxp|masonite|tenneco|fabricat|mill\b|bakery|brands"),
    ("Tech, telecom & BPO", r"tech|software|vmware|cyracom|data|digital|dell|oracle|intel\b|ibm|hp / hpe|cisco|microsoft|google|meta|apple|salesforce|paypal|indeed|bumble|at&t|nokia|frontier comm|telecom|wireless|accenture|cognizant|infosys|hcl|dxc|conduent|teleperformance|concentrix|sitel|telvista|ibex|alorica|genpact|xerox|call center|communications|systems|solutions"),
    ("Finance & insurance", r"bank|financ|insurance|capital|credit|mortgage|wells fargo|chase|citi|schwab|usaa|state farm|allstate|comerica|loan|invest|lending"),
    ("Government, education & nonprofit", r"school|isd\b|universit|college|county|city of|state of|correction|detention|corecivic|jail|raices|family initiative|children's home|management & training|southwest key|charities|goodwill|ministr|church|foundation|workforce|maximus|federal"),
    ("Business & professional services", r"fluor|amentum|maintenance|engineering|construction|staffing|services|security|janitorial|cleaning|abm\b|kforce|staffmark|consult"),
]
SECTORS = [(n, re.compile(p, re.I)) for n, p in SECTORS]

def sector(row):
    text = f"{row['organization']} {row['employer']}"
    for name, rx in SECTORS:
        if rx.search(text):
            return name
    return "Other / unclassified"

def records(df):
    return json.loads(df.to_json(orient="records", date_format="iso"))

def main():
    d = pd.read_csv(DATA / "tx_warn_2020_2026_clean.csv", parse_dates=["notice_date", "layoff_date"])
    d["sector"] = d.apply(sector, axis=1)
    d.to_csv(DATA / "tx_warn_2020_2026_clean.csv", index=False)
    last = d.notice_date.max()

    yearly = d.groupby("year").agg(notices=("layoffs", "size"), employees=("layoffs", "sum"),
                                   avg=("layoffs", "mean"), median=("layoffs", "median"),
                                   organizations=("organization", "nunique")).round(1).reset_index()
    # Same-period comparison (Jan 1 .. last notice day-of-year)
    doy = last.dayofyear
    ytd = d[d.notice_date.dt.dayofyear <= doy].groupby("year").agg(
        ytd_notices=("layoffs", "size"), ytd_employees=("layoffs", "sum")).reset_index()
    yearly = yearly.merge(ytd, on="year")

    monthly = d.groupby("month").agg(notices=("layoffs", "size"), employees=("layoffs", "sum")).reset_index()
    allm = pd.period_range(d.notice_date.min(), last, freq="M").astype(str)
    monthly = monthly.set_index("month").reindex(allm, fill_value=0).rename_axis("month").reset_index()

    org = (d.groupby("organization").agg(notices=("layoffs", "size"), employees=("layoffs", "sum"),
                                         years=("year", lambda s: ", ".join(map(str, sorted(s.unique())))),
                                         n_years=("year", "nunique"), sites=("city", "nunique"),
                                         sector=("sector", lambda s: s.mode().iat[0]),
                                         first=("notice_date", "min"), last=("notice_date", "max"))
           .sort_values("employees", ascending=False).reset_index())
    org["first"] = org["first"].dt.date.astype(str); org["last"] = org["last"].dt.date.astype(str)
    org.to_csv(OUT / "layoffs_by_organization.csv", index=False)

    recent = d[d.year >= 2023]
    org_recent = (recent.groupby("organization").agg(notices=("layoffs", "size"), employees=("layoffs", "sum"),
                                                     sector=("sector", lambda s: s.mode().iat[0]))
                  .sort_values("employees", ascending=False).head(25).reset_index())
    org_by_year = {int(y): records(g.groupby("organization").agg(employees=("layoffs", "sum"), notices=("layoffs", "size"))
                                   .sort_values("employees", ascending=False).head(10).reset_index())
                   for y, g in d.groupby("year")}
    repeat = org[org.n_years >= 3].sort_values(["n_years", "employees"], ascending=False).head(20)

    wda = (d.groupby("wda").agg(notices=("layoffs", "size"), employees=("layoffs", "sum"),
                                organizations=("organization", "nunique"))
           .sort_values("employees", ascending=False).reset_index())
    wda["share"] = (wda.employees / wda.employees.sum() * 100).round(1)
    wda.to_csv(OUT / "layoffs_by_wda_region.csv", index=False)
    wda_year = d.pivot_table(index="wda", columns="year", values="layoffs", aggfunc="sum", fill_value=0)
    wda_year = wda_year.loc[wda.wda].reset_index()
    wda_year.columns = [str(c) for c in wda_year.columns]
    wda_year.to_csv(OUT / "layoffs_by_wda_and_year.csv", index=False)

    county = (d.groupby("county").agg(notices=("layoffs", "size"), employees=("layoffs", "sum"),
                                      organizations=("organization", "nunique"))
              .sort_values("employees", ascending=False).reset_index())
    county.to_csv(OUT / "layoffs_by_county.csv", index=False)
    city = (d.groupby("city").agg(notices=("layoffs", "size"), employees=("layoffs", "sum"))
            .sort_values("employees", ascending=False).reset_index())
    city.to_csv(OUT / "layoffs_by_city.csv", index=False)

    sec = d.pivot_table(index="sector", columns="year", values="layoffs", aggfunc="sum", fill_value=0)
    sec["total"] = sec.sum(axis=1)
    sec = sec.sort_values("total", ascending=False).reset_index()
    sec.columns = [str(c) for c in sec.columns]
    sec.to_csv(OUT / "layoffs_by_sector_and_year.csv", index=False)

    bins = [0, 49, 99, 249, 499, 999, 1e9]
    labels = ["1–49", "50–99", "100–249", "250–499", "500–999", "1,000+"]
    d["size_band"] = pd.cut(d.layoffs, bins=bins, labels=labels)
    size = d.groupby("size_band", observed=False).agg(notices=("layoffs", "size"), employees=("layoffs", "sum")).reset_index()

    lt = d.dropna(subset=["lead_days"])
    lead = {"median_days": float(lt.lead_days.median()),
            "pct_under_60": round(float((lt.lead_days < 60).mean() * 100), 1),
            "pct_negative": round(float((lt.lead_days < 0).mean() * 100), 1),
            "by_year": records(lt.groupby("year").agg(median_days=("lead_days", "median"),
                               pct_under_60=("lead_days", lambda s: round((s < 60).mean() * 100, 1))).reset_index())}

    largest = d.nlargest(15, "layoffs")[["notice_date", "employer", "organization", "city", "county", "wda", "layoffs"]]
    largest["notice_date"] = largest.notice_date.dt.date.astype(str)
    latest = d.sort_values("notice_date", ascending=False).head(15)[["notice_date", "employer", "city", "layoffs", "layoff_date"]]
    latest["notice_date"] = latest.notice_date.dt.date.astype(str)
    latest["layoff_date"] = latest.layoff_date.dt.date.astype(str)

    summary = {
        "source": "https://www.twc.texas.gov/data-reports/warn-notice",
        "rows": int(len(d)), "employees": int(d.layoffs.sum()),
        "organizations": int(d.organization.nunique()), "counties": int(d.county.nunique()),
        "first": str(d.notice_date.min().date()), "last": str(last.date()), "ytd_cutoff": last.strftime("%b %d"),
        "yearly": records(yearly), "monthly": records(monthly), "org_top": records(org.head(25)),
        "org_recent": records(org_recent), "org_by_year": org_by_year, "repeat": records(repeat),
        "wda": records(wda), "wda_year": records(wda_year.head(10)), "county": records(county.head(20)),
        "city": records(city.head(15)), "sector": records(sec), "size": records(size), "lead": lead,
        "largest": records(largest), "latest": records(latest),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1, default=str))
    print(json.dumps({k: summary[k] for k in ["rows", "employees", "organizations", "counties", "first", "last"]}))
    print(yearly.to_string()); print(wda.head(10).to_string()); print(county.head(10).to_string())
    print(sec.to_string()); print(size.to_string()); print({k: v for k, v in lead.items() if k != "by_year"})
    print(org_recent.head(15).to_string()); print(repeat.to_string())
    print(largest.to_string())

if __name__ == "__main__":
    main()


def export_dashboard_csv():
    """Slim notice-level file used by the online dashboard."""
    d = pd.read_csv(DATA / "tx_warn_2020_2026_clean.csv")
    cols = ["notice_date", "month", "year", "employer", "organization", "sector", "city", "county",
            "wda", "layoffs", "layoff_date", "lead_days", "is_amendment"]
    d[cols].to_csv(OUT / "tx_warn_notices_dashboard.csv", index=False)


export_dashboard_csv()
