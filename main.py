#!/usr/bin/env python3
# Usage: ./main.py
"""
Copyright (C) 2020 John C. Allwein 'johnnyapol' (admin@johnnyapol.me)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
import requests
from discord_webhook import DiscordEmbed, DiscordWebhook
from bs4 import BeautifulSoup
from random import choice
import sys

try:
    import webhook_urls

    webhooks = webhook_urls.webhooks
except:
    print("No discord webhooks supplied - data will just be stored locally")
    webhooks = None


def check_for_updates():
    request = requests.get("https://covid19.rpi.edu/dashboard")
    soup = BeautifulSoup(request.text, features="lxml")
    header = "field field--name-field-stats field--type-entity-reference-revisions field--label-hidden field__items"
    header2 = "field field--name-field-stat field--type-string field--label-hidden field__item"
    data = soup.find("div", {"class": header})
    data = data.findAll("div", {"class": header2})

    """
        Current data format:

        case_data[0] = positive tests (last 24 hours)
        case_data[1] = positive test results (last 7 days)
        case_data[2] = positive test results (since august 17th)
        case_data[3] = total tests (last 7 days)
        case_data[4] = total tests (since august 17th)
    """
    return [x.text.strip() for x in data]


def post_discord(case_data, urls):
    thumbnails = [
        "https://www.continentalmessage.com/wp-content/uploads/2015/09/123rf-alert2.jpg",
        "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/clans/5671259/7923c9b8e0a5799d4d422208b31f5ca0f4f49067.png",
    ]

    # Calculate weekly positivity rate
    # Need to strip commas out
    pcr = (
        int(case_data[1].replace(",", "")) / int(case_data[3].replace(",", ""))
    ) * 100

    embed = DiscordEmbed(color=242424)
    embed.set_thumbnail(url=choice(thumbnails))
    embed.add_embed_field(
        name="Positive Tests (24 hours)", value=case_data[0], inline=False
    )
    embed.add_embed_field(name="Positive Tests (7 days)", value=case_data[1])
    embed.add_embed_field(name="Total Tests (7 days)", value=case_data[3])
    embed.add_embed_field(name="Weekly Positivty Rate", value=f"{round(pcr, 4)}%")
    embed.add_embed_field(
        name="Positive Test Results (since August 17th)", value=case_data[2]
    )
    embed.add_embed_field(name="Total Tests (since August 17th)", value=case_data[4])
    embed.set_author(
        name="Click for dashboard",
        url="https://covid19.rpi.edu/dashboard",
        icon_url="https://i.redd.it/14nqzc0hswy31.png",
    )
    embed.set_footer(
        text="Made with ❤️ - https://github.com/johnnyapol/RPICovidScraper"
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
    case_data = []
    try:
        with open(".cache", "r") as file:
            lines = file.readlines()
            for line in lines:
                case_data.append(line.rstrip())
    except:
        print("Cache read failed")
    return case_data


def save(case_data):
    with open(".cache", "w") as file:
        for case in case_data:
            file.write(case + "\n")


def main():
    previous_case_data = load_previous()
    current_case_data = check_for_updates()

    if current_case_data != previous_case_data:
        if webhooks == None:
            print("Skipping posting to discord as no webhooks supplied")
        else:
            post_discord(current_case_data, webhooks)
        save(current_case_data)
    print(f"Done. Old: {previous_case_data} New: {current_case_data}")


if __name__ == "__main__":
    main()
