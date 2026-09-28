"""World map: the peer countries recorded in countries.csv, present or not.

Reads the CSV written by qBittorrent's peer-country logging and draws a
two-color choropleth: red for a country seen at least once, grey for the rest.
"""
import csv
import os

import plotly.graph_objects as go
import plotly.io as pio
import pycountry
import webcolors

CSV_FILE = 'countries.csv'
HTML_FILE = 'countries-world-map.html'

def color(x):
    # https://www.quackit.com/css/css_color_codes.cfm
    rint = webcolors.name_to_rgb(x)
    return f'rgb({rint.red}, {rint.green}, {rint.blue})'

PRESENT_COLOR = color('red')
ABSENT_COLOR = color('lightgrey')
BORDER_COLOR = 'rgb(0, 0, 0)'


def load_countries(path=CSV_FILE):
    """Returns [(alpha_3, name)] for the countries listed in the CSV."""
    if not os.path.isfile(path):
        raise SystemExit(f'{path} not found. Run qBittorrent with country '
                         f'recording enabled first.')

    found = {}
    unknown = []
    with open(path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            code = (row.get('code') or '').strip().upper()
            if not code:
                continue

            country = pycountry.countries.get(alpha_2=code)
            if country is None:
                unknown.append(code)
                continue

            # The CSV name is what qBittorrent displayed; prefer it in hovers.
            found[country.alpha_3] = (row.get('name') or '').strip() or country.name

    if unknown:
        print(f'Skipped unrecognized code(s): {", ".join(sorted(set(unknown)))}')

    total = len(pycountry.countries)
    print(f'{len(found)} of {total} countries seen '
          f'({100 * len(found) / total:.2f}%).')

    return sorted(found.items())


def create_map(countries, path=HTML_FILE, auto_open=True):
    """Writes the choropleth to an HTML file."""
    codes, names = map(list, zip(*countries))

    data = [dict(
        type='choropleth',
        locations=codes,
        z=[1] * len(codes),
        text=names,
        hovertemplate='%{text}<extra></extra>',
        colorscale=[[0.0, PRESENT_COLOR], [1.0, PRESENT_COLOR]],
        autocolorscale=False,
        showscale=False,
        marker=dict(
            line=dict(
                color=BORDER_COLOR,
                width=1
            )),
    )]

    # Countries with no peers aren't plotted at all, so the land drawn
    # underneath them supplies the grey "not present" color.
    layout = dict(
        title=f'Peer Countries ({len(codes)} seen)',
        geo=dict(
            showframe=False,
            showcoastlines=False,
            showland=True,
            landcolor=ABSENT_COLOR,
            showcountries=True,
            countrycolor=BORDER_COLOR,
            lonaxis=dict(range=[-180, 180]),
            lataxis=dict(range=[-60, 85]),
            projection=dict(
                type='mercator',
                rotation=dict(lon=0)
            )
        )
    )

    fig = go.Figure(data=data, layout=layout)
    pio.write_html(fig, file=path, auto_open=auto_open)
    print(f'Wrote {path}')


if __name__ == '__main__':
    create_map(load_countries())
