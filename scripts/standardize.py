# scripts/standardize.py
import pandas as pd
import re
import os

os.makedirs("standardized", exist_ok=True)

## --- Apartment List: wide YYYY_MM -> long ---
ap = pd.read_csv("data/raw/aptlist/2024-01-01/apartmentlist_rent_estimates.csv..csv")
id_cols = ["location_name","location_type","location_fips_code","population","state","county","metro"]
date_cols = [c for c in ap.columns if re.fullmatch(r"\d{4}_\d{2}", c)]
ap_long = ap.melt(id_vars=id_cols, value_vars=date_cols,
                  var_name="yyyymm", value_name="rent_index")
ap_long["month"] = pd.to_datetime(ap_long["yyyymm"].str.replace("_","-") + "-01")
ap_long = ap_long.drop(columns=["yyyymm"]).sort_values(["metro","month"])
# (Optional) keep Tampa metro only:
# ap_long = ap_long[ap_long["metro"].str.contains("Tampa", na=False)]
ap_long.to_csv("standardized/apartmentlist_long.csv", index=False)

## --- Zillow ZORI ZIP: wide 2015-01-31 -> long ---
z = pd.read_csv("data/raw/zillow/zori_zip_month.csv")
fixed = [c for c in ["RegionID","SizeRank","RegionName","RegionType","StateName","Metro","CountyName"] if c in z.columns]
date_cols = [c for c in z.columns if re.fullmatch(r"\d{4}-\d{2}-\d{2}", c)]
z_long = z.melt(id_vars=fixed, value_vars=date_cols,
                var_name="month", value_name="zori")
z_long["month"] = pd.to_datetime(z_long["month"])
# Rename to nicer names
z_long = z_long.rename(columns={"RegionName":"zip","StateName":"state_name","CountyName":"county_name"})
# (Optional) keep Tampa metro only:
# z_long = z_long[z_long["Metro"].str.contains("Tampa", na=False)]
z_long.to_csv("standardized/zori_zip_long.csv", index=False)

## --- FRED: make sure it's two cols: observation_date, value ---
# If you already converted JSON→CSV, point to it; else adjust the filename:
fred = pd.read_csv("data/raw/fred/obs._by_real-time_period.csv")   # cols: period_start_date,GNPCA,realtime_start_date,realtime_end_date
fred = fred.rename(columns={"period_start_date":"month","GNPCA":"cpi_rent_sa"})
fred["month"] = pd.to_datetime(fred["month"])
fred = fred[fred["cpi_rent_sa"].notna()]
fred = fred[["month", "cpi_rent_sa"]]  # Keep only the two needed columns
fred.to_csv("standardized/fred_cpi_long.csv", index=False)

print("Wrote standardized/*.csv")