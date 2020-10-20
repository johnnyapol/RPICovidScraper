#!/usr/bin/env python3
# Usage: ./main.py
"""
Copyright (C) 2020 John C. Allwein 'johnnyapol' (admin@johnnyapol.me)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
import os
import pickle
import requests
from random import choice
import sys
import traceback

from bs4 import BeautifulSoup
from discord_webhook import DiscordEmbed, DiscordWebhook
import savepagenow

try:
    import webhook_urls

    webhooks = webhook_urls.webhooks
except:
    print("No discord webhooks supplied - data will just be stored locally")
    traceback.print_exc()
    webhooks = None

DASHBOARD = "https://covid19.rpi.edu/dashboard"


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


def post_discord(case_data, previous_case_data, date, dashboard_url, urls):
    if urls is None:
        return print("Skipping posting to discord as no webhooks supplied")

    positive_thumbnails = [
        "https://www.continentalmessage.com/wp-content/uploads/2015/09/123rf-alert2.jpg",
        "https://i.kym-cdn.com/photos/images/newsfeed/000/675/645/2c7.gif",
    ]

    negative_thumbnails = [
        "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/clans/5671259/7923c9b8e0a5799d4d422208b31f5ca0f4f49067.png",
        "https://static01.nyt.com/images/2020/01/28/science/28VIRUS-BATS1/28VIRUS-BATS1-videoSixteenByNineJumbo1600.jpg",
    ]

    closed_thumbnail = "https://www.insidehighered.com/sites/default/server_files/styles/large-copy/public/media/iStock-851180708_0.jpg?itok=8vdbtNt4"

    emojis = ["❤️", "✨", "🥓", "🦄", "🌯", "🍺", "🧻", "🐍", "🦀 unsafe 🦀"]

    if case_data[2] < 100:
        if case_data[0] > 0:
            embed = DiscordEmbed(color=15158332)
            embed.set_thumbnail(url=choice(positive_thumbnails))
        else:
            embed = DiscordEmbed(color=3066993)
            embed.set_thumbnail(url=choice(negative_thumbnails))
    else:
        embed.set_thumbnail(url=closed_thumbnail)

    embed.add_embed_field(
        name="Positive Tests (24 hours)",
        value=case_value_to_string(case_data, previous_case_data, 0),
        inline=False,
    )
    embed.add_embed_field(
        name="Positive Tests (7 days)",
        value=case_value_to_string(case_data, previous_case_data, 1),
    )
    embed.add_embed_field(
        name="Total Tests (7 days)",
        value=case_value_to_string(case_data, previous_case_data, 3),
    )
    if case_data[1] != 0:
        # Calculate weekly positivity rate
        pcr = (case_data[1] / case_data[3]) * 100
        embed.add_embed_field(name="Weekly Positivty Rate", value=f"{round(pcr, 4)}%")
    embed.add_embed_field(
        name="Total Positive Tests (since August 1st)",
        value=case_value_to_string(case_data, previous_case_data, 2),
    )
    embed.add_embed_field(
        name="Total Tests (since August 1st)",
        value=case_value_to_string(case_data, previous_case_data, 4),
    )
    embed.set_author(
        name="Click for dashboard",
        url=dashboard_url,
        icon_url="https://i.redd.it/14nqzc0hswy31.png",
    )

    embed.set_footer(
        text=f"{date}\nMade with {choice(emojis)} - https://github.com/johnnyapol/RPICovidScraper"
    )

    hook = DiscordWebhook(
        url=urls,
        content="The RPI Covid Dashboard has been updated!",
        username="RPI Covid Dashboard",
        avatar_url="https://www.minnpost.com/wp-content/uploads/2020/03/coronavirusCDC640.png",
    )
    hook.add_embed(embed)
    hook.execute()


def load_previous():
    try:
        with open(".cache", "rb") as file:
            return pickle.load(file)
    except:
        print("Cache read failed")
        return [0, 0, 0, 0, 0]


def save(case_data):
    with open(".cache", "wb") as file:
        pickle.dump(case_data, file)


def main():
    global webhooks
    global DASHBOARD
    previous_case_data = load_previous()
    current_case_data, date = check_for_updates()

    ci = any(x.lower() == "--ci" for x in sys.argv)

    if current_case_data != previous_case_data:
        dashboard_url = DASHBOARD
        try:
            # We don't want to abuse the Wayback Machine in actions
            if not ci:
                dashboard_url = savepagenow.capture(DASHBOARD, accept_cache=True)
            else:
                print("Skipping page archive as we are running in CI mode")
        except Exception as e:
            print(f"Page archived failed {e}")
        post_discord(
            current_case_data, previous_case_data, date, dashboard_url, webhooks
        )
        save(current_case_data)
    print(f"Done. Old: {previous_case_data} New: {current_case_data}")


if __name__ == "__main__":
    main()
