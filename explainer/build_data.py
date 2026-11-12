"""Turn the GWOSC catalog (data/gwtc_catalog.csv) into a small JSON file for the explainer page.

Data source: LIGO-Virgo-KAGRA Gravitational-Wave Transient Catalog (GWTC-1 ... GWTC-5.0),
Gravitational Wave Open Science Center, https://gwosc.org/eventapi/csv/GWTC/
Run from the repo's top folder:  python3 explainer/build_data.py
"""
import json, os
import pandas as pd
from astropy.cosmology import Planck18   # standard cosmology, used to turn redshift into travel time

CSV = 'data/gwtc_catalog.csv'
if not os.path.exists(CSV):
    os.makedirs('data', exist_ok=True)
    pd.read_csv('https://gwosc.org/eventapi/csv/GWTC/').to_csv(CSV, index=False)
df = pd.read_csv(CSV)

# GPS seconds count from 6 Jan 1980; convert to a calendar date
df['date'] = (pd.Timestamp('1980-01-06') + pd.to_timedelta(df['GPS'], unit='s')).dt.strftime('%Y-%m-%d')
# How many billion years the gravitational waves travelled to reach Earth
df['travel_gyr'] = Planck18.lookback_time(df['redshift'].fillna(0).values).value
df.loc[df['redshift'].isna(), 'travel_gyr'] = None

def num(v, nd=2):
    return None if pd.isna(v) else round(float(v), nd)

events = []
for _, r in df.sort_values('GPS').iterrows():
    events.append({
        'name': r['commonName'], 'date': r['date'], 'catalog': r['catalog.shortName'],
        'm1': num(r['mass_1_source']), 'm1lo': num(r['mass_1_source_lower']), 'm1hi': num(r['mass_1_source_upper']),
        'm2': num(r['mass_2_source']), 'm2lo': num(r['mass_2_source_lower']), 'm2hi': num(r['mass_2_source_upper']),
        'mf': num(r['final_mass_source']), 'dist': num(r['luminosity_distance'], 0),
        'travel': num(r['travel_gyr']), 'chi': num(r['chi_eff']),
    })
json.dump(events, open('explainer/events.json', 'w'), separators=(',', ':'))
print(len(events), 'events written to explainer/events.json')

# Put the data into the page template, producing the finished explainer page
html = open('explainer/template.html').read().replace('__EVENTS__', json.dumps(events, separators=(',', ':')))
open('explainer/stellar_graveyard.html', 'w').write(html)
print('wrote explainer/stellar_graveyard.html')
