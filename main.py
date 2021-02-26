#!/usr/bin/env python3
# Usage: ./main.py
"""
Copyright (C) 2020-2021 John C. Allwein 'johnnyapol' (admin@johnnyapol.me)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
import os
import pickle
import requests
from random import choice
from subprocess import run
import sys
import traceback
from datetime import date, timedelta
from copy import deepcopy
from itertools import chain
from io import BytesIO

from bs4 import BeautifulSoup
from discord_webhook import DiscordEmbed, DiscordWebhook
import matplotlib.pyplot as plot
import savepagenow

# Import configuration (if available)
try:
    import config

    WEBHOOKS = config.webhooks
    PSA = config.PSA
    QUIET = config.QUIET
except:
    print("No discord webhooks supplied - data will just be stored locally")
    traceback.print_exc()
    WEBHOOKS = None
    PSA = None
    QUIET = False

DASHBOARD = "https://covid19.rpi.edu/dashboard"


class CovidData:
    def __init__(self):
        self.rpi_array = [0] * 5
        self.rolling_array = [0] * 14
        self.last_updated = date.today()
        self.array_index = 0

    def increment_index(self):
        self.array_index = (self.array_index + 1) % 14

    def update(self, case_data):
        today = date.today()
        if today != self.last_updated:
            assert today > self.last_updated
            delta = (today - self.last_updated).days - 1
            self.increment_index()

            # Fill in 0s
            while delta != 0:
                self.rolling_array[self.array_index] = 0
                self.increment_index()
                delta -= 1

        # Write out next data
        self.rolling_array[self.array_index] = case_data[0]
        self.rpi_array = case_data
        self.last_updated = today

    def get_rolling(self):
        return sum(self.rolling_array)

    def get_case_data(self):
        return self.rpi_array

    def get_rolling_iterator(self):
        return chain(self.rolling_array[self.array_index + 1:14], self.rolling_array[:self.array_index + 1])


def check_for_updates():
    global DASHBOARD
    request = requests.get(DASHBOARD)
    soup = BeautifulSoup(request.text, features="lxml")
    header = "field field--name-field-stats field--type-entity-reference-revisions field--label-hidden field__items"
    header2 = "field field--name-field-stat field--type-string field--label-hidden field__item"
    date_header = "field field--name-field-stats-caption field--type-string field--label-hidden field__item"

    """
        Current data format:

        case_data[0] = positive tests (last 24 hours)
        case_data[1] = positive test results (last 7 days)
        case_data[2] = positive test results (since august 17th)
        case_data[3] = total tests (last 7 days)
        case_data[4] = total tests (since august 17th)
    """
    return (
        [
            int("".join(("".join(x.text.strip().split(" "))).split(",")))
            for x in soup.find("div", {"class": header}).findAll(
            "div", {"class": header2}
        )
        ],
        soup.find("div", {"class": date_header}).text,
    )


def case_value_to_string(case_data, previous_case_data, index):
    diff = case_data[index] - previous_case_data[index]
    diff_string = f"({diff:+,})" if diff != 0 else ""
    return f"{case_data[index]:,} {diff_string}"


def get_git_hash():
    try:
        return f'({run(["git", "log", "--pretty=format:%h", "-n", "1"], capture_output=True).stdout.decode("ascii")})'
    except:
        return ""


def post_discord(
        rolling, old_rolling, case_data, previous_case_data, date, dashboard_url, graph
):
    global WEBHOOKS
    global PSA
    global QUIET
    if WEBHOOKS is None:
        return print("Skipping posting to discord as no webhooks supplied")

    positive_thumbnails = [
        "https://www.continentalmessage.com/wp-content/uploads/2015/09/123rf-alert2.jpg",
        "https://i.kym-cdn.com/photos/images/newsfeed/000/675/645/2c7.gif",
        "https://media.discordapp.net/attachments/783375197604413445/790625854202839100/image0.png",
    ]

    negative_thumbnails = [
        "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/clans/5671259/7923c9b8e0a5799d4d422208b31f5ca0f4f49067.png",
        "https://static01.nyt.com/images/2020/01/28/science/28VIRUS-BATS1/28VIRUS-BATS1-videoSixteenByNineJumbo1600.jpg",
        "https://media.tenor.com/images/6603c0a47ff16ad8d3682e481e727f76/tenor.gif",
        "https://ih1.redbubble.net/image.1877589148.0162/ur,mask_flatlay_front,wide_portrait,750x1000.jpg",
    ]

    closed_thumbnail = "https://www.insidehighered.com/sites/default/server_files/styles/large-copy/public/media/iStock-851180708_0.jpg?itok=8vdbtNt4"

    emojis = ["❤️", "✨", "🥓", "🍺", "🧻", "🐍", "☃️"]

    if QUIET and case_data[0] == 0:
        return

    embed = DiscordEmbed()

    if rolling < 30:
        if case_data[0] > 0:
            embed.set_color(15158332)
            embed.set_thumbnail(url=choice(positive_thumbnails))
        else:
            embed.set_color(3066993)
            embed.set_thumbnail(url=choice(negative_thumbnails))
    else:
        embed.set_thumbnail(url=closed_thumbnail)

    if PSA is not None:
        embed.add_embed_field(name="ANNOUNCEMENT", value=PSA, inline=False)
        embed.color = 15844367

    embed.add_embed_field(
        name="New Positive Tests",
        value=f"{case_data[0]}",
        inline=False,
    )
    embed.add_embed_field(
        name="Positive Tests (7 days)",
        value=case_value_to_string(case_data, previous_case_data, 1),
        inline=False,
    )

    embed.add_embed_field(
        name="Positive Tests (14 days)",
        value=case_value_to_string([rolling], [old_rolling], 0),
        inline=False,
    )

    embed.add_embed_field(
        name="Weekly Test Count",
        value=case_value_to_string(case_data, previous_case_data, 3),
        inline=False,
    )
    if case_data[1] != 0:
        # Calculate weekly positivity rate
        pcr = (case_data[1] / case_data[3]) * 100
        embed.add_embed_field(name="Weekly Positivty Rate", value=f"{round(pcr, 4)}%")
    embed.add_embed_field(
        name="Total Positive Tests",
        value=case_value_to_string(case_data, previous_case_data, 2),
    )
    embed.add_embed_field(
        name="Total Tests",
        value=case_value_to_string(case_data, previous_case_data, 4),
    )
    embed.set_author(
        name="Click for dashboard",
        url=dashboard_url,
        icon_url="https://i.redd.it/14nqzc0hswy31.png",
    )

    embed.set_footer(
        text=f"{date}\nMade with {choice(emojis)} - https://github.com/johnnyapol/RPICovidScraper {get_git_hash()}"
    )

    hook = DiscordWebhook(
        url=WEBHOOKS,
        content=choice(
            [
                "The RPI Covid Dashboard has been updated!",
                "I got yer COVID cases right here!",
                "Special delivery!",
                "Beep beep boop",
                "I found some data!",
            ]
        ),
        username="RPI Covid Dashboard",
        avatar_url="https://www.minnpost.com/wp-content/uploads/2020/03/coronavirusCDC640.png",
    )
    hook.add_file(file=graph.read(), filename='graph.png')
    embed.set_image(url="attachment://graph.png")
    hook.add_embed(embed)
    hook.execute()


def load_previous():
    try:
        with open(".cache", "rb") as file:
            return pickle.load(file)
    except:
        print("Cache read failed")
        return CovidData()


def save(case_data):
    with open(".cache", "wb") as file:
        pickle.dump(case_data, file)


def create_graph(iterator):
    x = [int(z) for z in iterator]
    cum = [x[0]]
    for i in range(1, len(x)):
        cum.append(cum[-1] + x[i])
    print(x)
    # thanks to https://www.tutorialspoint.com/matplotlib/matplotlib_bar_plot.htm for help
    today = date.today()
    monthday = lambda d: f"{d.month}-{d.day}"
    dates = [monthday(today - timedelta(days=x)) for x in range(13, -1, -1)]
    plot.title(f"Previous 14 days")
    plot.bar(dates, x, color='red', label='daily cases')
    plot.plot(dates, cum, color='orange', label='cumulative total')
    if x[-1] > 15:
        plot.plot(dates, [30] * 14, 'g--', label='trigger level 1')
    plot.xticks(dates, dates, rotation=90)
    plot.legend()
    # plot.show()
    data = BytesIO()
    plot.savefig(data, format='png')
    data.seek(0)
    return data


def main():
    global DASHBOARD
    covid_data = load_previous()
    previous_case_data = deepcopy(covid_data.get_case_data())
    current_case_data, date = check_for_updates()

    ci = any(x.lower() == "--ci" for x in sys.argv)

    # Only post under the following conditions:
    # 1. There is new data from RPI
    #           - AND -
    # 2. there are new positive tests OR new weekly/total numbers reported
    # This avoids the bs updates where all RPI does is reset the daily/weekly numbers
    if current_case_data != previous_case_data and (
            current_case_data[0] != 0
            or any(
        current_case_data[x] != previous_case_data[x]
        for x in range(2, len(current_case_data))
    )
    ) or True:
        dashboard_url = DASHBOARD
        try:
            # We don't want to abuse the Wayback Machine in actions
            if not ci:
                dashboard_url = savepagenow.capture(DASHBOARD, accept_cache=True)
            else:
                print("Skipping page archive as we are running in CI mode")
        except:
            print(f"Page archived failed")
            traceback.print_exc()

        old_rolling = covid_data.get_rolling()
        covid_data.update(current_case_data)

        post_discord(
            covid_data.get_rolling(),
            old_rolling,
            current_case_data,
            previous_case_data,
            date,
            dashboard_url,
            create_graph(covid_data.get_rolling_iterator())
        )

        save(covid_data)
    print(
        f"Done. Old: {previous_case_data} New: {current_case_data}\n Rolling: {covid_data.get_rolling()}"
    )


if __name__ == "__main__":
    main()
