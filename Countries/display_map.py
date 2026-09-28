"""World map: the peer countries recorded in countries.csv, present or not.

Reads the CSV written by qBittorrent's peer-country logging and draws a
two-color choropleth: red (1) for a country seen at least once, grey (0) for
the rest. Every country is plotted, so hovering works either way.
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
    """Returns [(alpha_3, name, seen)] for every country, CSV ones marked seen."""
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

    # Every country is plotted, not just the ones seen, so that the unseen ones
    # get a hover label and a 0 of their own.
    countries = [(c.alpha_3, found.get(c.alpha_3, c.name), c.alpha_3 in found)
                 for c in pycountry.countries]
    return sorted(countries)


def create_map(countries, path=HTML_FILE, auto_open=True):
    """Writes the choropleth to an HTML file."""
    codes, names, seen = map(list, zip(*countries))
    z = [int(s) for s in seen]

    data = [dict(
        type='choropleth',
        locations=codes,
        z=z,
        text=names,
        hovertemplate='%{text}<br>%{z}<extra></extra>',
        # Repeating the color at the midpoint makes plotly draw two flat
        # classes instead of a 0-to-1 gradient.
        colorscale=[[0.0, ABSENT_COLOR], [0.5, ABSENT_COLOR],
                    [0.5, PRESENT_COLOR], [1.0, PRESENT_COLOR]],
        zmin=0,
        zmax=1,
        autocolorscale=False,
        showscale=False,
        marker=dict(
            line=dict(
                color=BORDER_COLOR,
                width=1
            )),
    )]

    # The land underneath only shows through for the few codes plotly's ISO-3
    # map doesn't know, so it is drawn in the same grey as an unseen country.
    layout = dict(
        title=f'Peer Countries ({sum(z)} seen)',
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
