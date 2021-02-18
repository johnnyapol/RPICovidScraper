"""
Copyright (C) 2020-2021 John C. Allwein 'johnnyapol' (admin@johnnyapol.me)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

from main import CovidData, load_previous, save
from datetime import date


def print_stats(data):
    print("Current COVID data statistics: ")
    print("RPI ARRAY: ", data.get_case_data())
    print("2 week rolling: ", data.get_rolling())
    print("Rolling array: ", data.rolling_array)
    print("Last updated: ", data.last_updated)
    print("Array index: ", data.array_index)


if __name__ == "__main__":
    data = load_previous()
    print("Got data: ", data)
    print_stats(data)

    new_rolling = [int(x) for x in input("Please enter a new data array: ").split(",")]
    new_array_index = len(new_rolling) - 1
    new_day = date.today()
    print("New rolling array ", new_rolling)
    print("Array index: ", new_array_index)
    print("New last updated: ", new_day)
    assert new_array_index >= 0

    # pad off 0s till we get to 14
    while len(data.rolling_array) != 14:
        data.rolling_array.append(0)

    data.rolling_array = new_rolling
    data.array_index = new_array_index
    data.last_updated = new_day

    print("**** STATS HAVE BEEN CHANGED. Please review the changes *****")
    print_stats(data)

    input("Press any key to continue")
    save(data)

    print("Changes have been saved")
