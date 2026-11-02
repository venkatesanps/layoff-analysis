"""Combine and clean TWC WARN Act yearly listings into one dataset."""
import glob, re, sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW, DATA = ROOT / "raw", ROOT / "data"

# Manual aliases: regex on the cleaned lowercase name -> canonical organization
ALIASES = [
    (r"\bat&t\b|^att\b", "AT&T"),
    (r"\bfedex\b|federal express", "FedEx"),
    (r"\bups\b|united parcel", "UPS"),
    (r"\bamazon\b", "Amazon"),
    (r"\bwalmart\b|wal-mart", "Walmart"),
    (r"\btesla\b", "Tesla"),
    (r"\bdell\b", "Dell"),
    (r"\boracle\b", "Oracle"),
    (r"\bintel\b", "Intel"),
    (r"\bsamsung\b", "Samsung"),
    (r"\bmeta\b|facebook", "Meta"),
    (r"\bgoogle\b", "Google"),
    (r"\bmicrosoft\b", "Microsoft"),
    (r"\bapple\b", "Apple"),
    (r"\bnokia\b", "Nokia"),
    (r"\bamerican airlines\b", "American Airlines"),
    (r"\bsouthwest airlines\b", "Southwest Airlines"),
    (r"\bunited airlines\b", "United Airlines"),
    (r"\bmarriott\b", "Marriott"),
    (r"\bhilton\b", "Hilton"),
    (r"\bhyatt\b", "Hyatt"),
    (r"\bsodexo\b", "Sodexo"),
    (r"\baramark\b", "Aramark"),
    (r"\bcompass group\b", "Compass Group"),
    (r"\bhertz\b", "Hertz"),
    (r"\bschlumberger\b|\bslb\b", "Schlumberger (SLB)"),
    (r"\bhall?iburton\b", "Halliburton"),
    (r"\bhooters\b", "Hooters"),
    (r"^southwest\s*-", "Southwest Airlines"),
    (r"\bpappas\b", "Pappas Restaurants"),
    (r"\bfirst texas hospital\b", "First Texas Hospital"),
    (r"\busaa\b", "USAA"),
    (r"\basarco\b", "ASARCO"),
    (r"management (&|and) training|\bmtc\b", "Management & Training Corp (MTC)"),
    (r"\bmv[- ]+transportation|^mv\b", "MV Transportation"),
    (r"\bspirit aerosystems\b", "Spirit AeroSystems"),
    (r"\bspirit airlines\b|^spirit$", "Spirit Airlines"),
    (r"\bzachry\b", "Zachry"),
    (r"\balorica\b", "Alorica"),
    (r"\bfrontier (enterp|communications)", "Frontier Communications"),
    (r"\bsouthwest key\b", "Southwest Key Programs"),
    (r"\bwillie'?s grill\b", "Willie's Grill & Icehouse"),
    (r"\bdavid'?s bridal\b", "David's Bridal"),
    (r"\bconifer\b", "Conifer Health Solutions"),
    (r"\btexas children'?s", "Texas Children's Hospital"),
    (r"\bymca\b", "YMCA"),
    (r"\bgaylord\b", "Gaylord Texan (Marriott)"),
    (r"\bavis\b", "Avis Budget"),
    (r"\bsouthwestern & pacific\b", "Southwestern & Pacific Specialty Finance"),
    (r"\bbaker hughes\b", "Baker Hughes"),
    (r"\bnational oilwell|\bnov\b", "NOV"),
    (r"\bexxon", "ExxonMobil"),
    (r"\bconocophillips\b", "ConocoPhillips"),
    (r"\bshell\b", "Shell"),
    (r"\bchevron\b", "Chevron"),
    (r"\bdxc\b", "DXC Technology"),
    (r"\bconduent\b", "Conduent"),
    (r"\bteleperformance\b", "Teleperformance"),
    (r"\bconcentrix\b", "Concentrix"),
    (r"\bsitel\b", "Sitel"),
    (r"\btelvista\b", "Telvista"),
    (r"\bibex\b", "IBEX"),
    (r"\bxerox\b", "Xerox"),
    (r"\bkroger\b", "Kroger"),
    (r"\bh-?e-?b\b", "H-E-B"),
    (r"\btarget\b", "Target"),
    (r"\bmacy'?s\b", "Macy's"),
    (r"\bjcpenney|j\.?\s?c\.?\s?penney", "JCPenney"),
    (r"\bdillard", "Dillard's"),
    (r"\bboeing\b", "Boeing"),
    (r"\blockheed\b", "Lockheed Martin"),
    (r"\bgeneral motors\b|\bgm\b", "General Motors"),
    (r"\bherzog\b", "Herzog"),
    (r"\bcentral freight\b", "Central Freight Lines"),
    (r"\bkforce\b", "Kforce"),
    (r"\bwells fargo\b", "Wells Fargo"),
    (r"\bjpmorgan|chase bank", "JPMorgan Chase"),
    (r"\bcitigroup|\bcitibank\b|\bciti\b", "Citi"),
    (r"\bbank of america\b", "Bank of America"),
    (r"\bcharles schwab\b|\bschwab\b", "Charles Schwab"),
    (r"\bcaremark\b|\bcvs\b", "CVS Health"),
    (r"\bwalgreen", "Walgreens"),
    (r"\bhcl\b", "HCL"),
    (r"\bcognizant\b", "Cognizant"),
    (r"\binfosys\b", "Infosys"),
    (r"\baccenture\b", "Accenture"),
    (r"\bibm\b", "IBM"),
    (r"\bhewlett|\bhpe?\b", "HP / HPE"),
    (r"\bcisco\b", "Cisco"),
    (r"\bbest buy\b", "Best Buy"),
    (r"\bhome depot\b", "Home Depot"),
    (r"\blowe'?s\b", "Lowe's"),
    (r"\bsix flags\b", "Six Flags"),
    (r"\bcinemark\b", "Cinemark"),
    (r"\bamc\b", "AMC Theatres"),
    (r"\bdave & buster|dave and buster", "Dave & Buster's"),
    (r"\bdel frisco", "Del Frisco's"),
    (r"\blandry'?s\b", "Landry's"),
    (r"\bhms host|hmshost", "HMSHost"),
    (r"\bsky chefs|lsg\b", "LSG Sky Chefs"),
    (r"\bgate gourmet\b", "Gate Gourmet"),
    (r"\bprospect airport", "Prospect Airport Services"),
    (r"\bswissport\b", "Swissport"),
    (r"\benvoy\b", "Envoy Air"),
    (r"\bjohnson controls\b", "Johnson Controls"),
    (r"\bgeneral electric\b|\bge\b", "General Electric"),
    (r"\bsiemens\b", "Siemens"),
    (r"\bspirit aerosystems\b", "Spirit AeroSystems"),
    (r"\bbell (textron|helicopter)", "Bell Textron"),
    (r"\bpilgrim'?s", "Pilgrim's Pride"),
    (r"\btyson\b", "Tyson Foods"),
    (r"\bcargill\b", "Cargill"),
    (r"\bfrito", "Frito-Lay"),
    (r"\bpepsi", "PepsiCo"),
    (r"\bcoca-?cola\b", "Coca-Cola"),
    (r"\bkellogg", "Kellogg"),
    (r"\bstate farm\b", "State Farm"),
    (r"\ballstate\b", "Allstate"),
    (r"\bunited ?health|optum\b", "UnitedHealth / Optum"),
    (r"\bmckesson\b", "McKesson"),
    (r"\bcardinal health\b", "Cardinal Health"),
    (r"\btenet\b", "Tenet Healthcare"),
    (r"\bmedical city\b|\bhca\b", "HCA / Medical City"),
    (r"\bbaylor scott", "Baylor Scott & White"),
    (r"\bmd anderson\b", "MD Anderson"),
    (r"\bus foods\b", "US Foods"),
    (r"\bsysco\b", "Sysco"),
    (r"\bdhl\b", "DHL"),
    (r"\bxpo\b", "XPO"),
    (r"\byellow\b", "Yellow Corp"),
    (r"\bgeodis\b", "GEODIS"),
    (r"\bryder\b", "Ryder"),
    (r"\bmaximus\b", "Maximus"),
    (r"\bstaffmark\b", "Staffmark"),
    (r"\bcomerica\b", "Comerica"),
    (r"\btexas instruments\b", "Texas Instruments"),
    (r"\bnxp\b", "NXP"),
    (r"\bglobalfoundries\b", "GlobalFoundries"),
    (r"\bapplied materials\b", "Applied Materials"),
    (r"\bcanoo\b", "Canoo"),
    (r"\brivian\b", "Rivian"),
    (r"\bindeed\b", "Indeed"),
    (r"\bbumble\b", "Bumble"),
    (r"\bsalesforce\b", "Salesforce"),
    (r"\bpaypal\b", "PayPal"),
    (r"\bfluor\b", "Fluor"),
    (r"\bjacobs\b", "Jacobs"),
    (r"\bkbr\b", "KBR"),
    (r"\bmckinsey\b", "McKinsey"),
    (r"\bbristow\b", "Bristow"),
    (r"\bweatherford\b", "Weatherford"),
    (r"\bnabors\b", "Nabors"),
    (r"\bpatterson-uti\b", "Patterson-UTI"),
    (r"\bliberty oilfield\b", "Liberty Oilfield"),
    (r"\bproPetro|propetro\b", "ProPetro"),
    (r"\bfts international\b", "FTS International"),
    (r"\bkeane\b|nextier", "NexTier / Keane"),
    (r"\bgoodwill\b", "Goodwill"),
    (r"\bdallas county\b", "Dallas County"),
    (r"\bcity of\b", None),  # leave as-is
]
ALIASES = [(re.compile(p, re.I), c) for p, c in ALIASES]

SUFFIX = re.compile(r"[,\s]+(l\.?l\.?c\.?|inc\.?|incorporated|corp\.?|corporation|co\.?|company|ltd\.?|l\.?p\.?|lp|llp|plc|n\.?a\.?|holdings?|group|usa|us|u\.s\.|of texas|texas)\s*$", re.I)

def canonical_org(name: str) -> str:
    if not isinstance(name, str) or not name.strip():
        return "Unknown"
    s = re.split(r"\s{2,}", name.strip())[0]           # "Company, LLC  Grand Prairie" -> site after 2+ spaces
    s = re.sub(r"\s+", " ", s).strip()
    for rx, canon in ALIASES:
        if rx.search(s):
            if canon:
                return canon
            break
    s = re.split(r"\s+(?:d/?b/?a|dba|a/k/a|aka|f/k/a)\s+", s, flags=re.I)[0]  # keep legal name
    if "(" in s and s.split("(")[0].strip():          # "Name (site / parent) more site" -> "Name"
        s = s.split("(")[0]
    s = re.sub(r"\(.*?\)", "", s)
    s = re.split(r"\s*[-–—]\s+|\s+[-–—]\s*|(?<=[a-z.])[-–—](?=[A-Z])", s)[0]  # drop "-Site"
    for _ in range(3):
        s = SUFFIX.sub("", s).strip(" ,.-")
    if s.isupper() and len(s) > 6 or s.islower():
        s = s.title()
    return s or name.strip()

def main():
    frames = []
    for f in sorted(RAW.glob("warn-*.xlsx")):
        d = pd.read_excel(f, sheet_name=0)
        d["source_file"] = f.name
        frames.append(d)
    df = pd.concat(frames, ignore_index=True)
    df.columns = [c.lower() for c in df.columns]
    df = df.rename(columns={"job_site_name": "employer", "total_layoff_number": "layoffs",
                            "layoff_date": "layoff_date", "wda_name": "wda", "county_name": "county",
                            "city_name": "city", "wfdd_received_date": "received_date"})
    for c in ["notice_date", "layoff_date", "received_date"]:
        df[c] = pd.to_datetime(df[c], errors="coerce")
    df["layoffs"] = pd.to_numeric(df["layoffs"], errors="coerce")
    df["organization"] = df["employer"].map(canonical_org)  # before whitespace is collapsed
    for c in ["employer", "county", "wda", "city"]:
        df[c] = df[c].astype("string").str.strip().str.replace(r"\s+", " ", regex=True)
    df["county"] = df["county"].str.title()
    df["city"] = df["city"].str.title().replace({"Ft. Worth": "Fort Worth", "Ft Worth": "Fort Worth"})
    df["wda"] = (df["wda"].str.replace(r"\s*WDA$", "", regex=True)
                 .replace({"Borderplexjobs": "Borderplex", "North Central": "North Central Texas"}))
    df = df.dropna(how="all", subset=["employer", "layoffs", "notice_date"])
    before = len(df)
    # Yearly files overlap (e.g. the 2024 file repeats late-2023 notices), so dedupe across files
    df = df.drop_duplicates(subset=["notice_date", "employer", "county", "layoffs", "layoff_date"])
    # Fill missing workforce region from the county's usual region
    wmap = df.dropna(subset=["wda"]).groupby("county")["wda"].agg(lambda s: s.mode().iat[0])
    df["wda"] = df["wda"].fillna(df["county"].map(wmap))
    # Amended notices ("Updated") - flag them; drop ones that just re-file an earlier notice
    # with the same organization, city and headcount (e.g. Tyson Foods Amarillo, 1,761 twice)
    df = df.sort_values("notice_date").reset_index(drop=True)
    df["is_amendment"] = df["employer"].str.contains(r"\bupdated?\b|\bamended\b|\brevised\b", case=False, na=False)
    refile = df["is_amendment"] & df.duplicated(["organization", "city", "layoffs"])
    print(f"dropped {int(refile.sum())} amended re-filings", file=sys.stderr)
    df = df[~refile]
    df["year"] = df["notice_date"].dt.year.astype("Int64")
    df["month"] = df["notice_date"].dt.to_period("M").astype(str)
    df["lead_days"] = (df["layoff_date"] - df["notice_date"]).dt.days
    df = df.sort_values("notice_date")
    df.to_csv(DATA / "tx_warn_2020_2026_clean.csv", index=False)
    print(f"rows={len(df)} (dropped {before-len(df)} exact dupes), missing layoffs={df.layoffs.isna().sum()}",
          f"date range {df.notice_date.min().date()}..{df.notice_date.max().date()}", file=sys.stderr)

if __name__ == "__main__":
    main()
