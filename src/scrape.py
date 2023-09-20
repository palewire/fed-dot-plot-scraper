"""Extracting the "dot plot" economic projections posted online by the Federal Open Market Committee.

Example usage:
    $ python src/scrape.py > data/output.csv
"""
from __future__ import annotations

import sys
from datetime import datetime

import pandas as pd
from bs4 import BeautifulSoup
from slugify import slugify

from src import utils


def scrape() -> pd.DataFrame:
    """Scrape the projections from the source URLs.

    Returns:
        pd.DataFrame: A DataFrame with the columns "date", "midpoint", and the projections.
    """
    # Get the list of source URLs.
    source_df = _get_source_urls()

    # Create a list to hold the DataFrames.
    df_list = []

    # Convert the source dataframe to a list of dictionaries.
    source_list = source_df.to_dict(orient="records")

    # Loop through the source URLs.
    for source in source_list:
        # Parse the source URL.
        df = _parse_source_url(**source)

        # Append the DataFrame to the list of DataFrames.
        df_list.append(df)

    # Concatenate the DataFrames into a single DataFrame.
    big_df = pd.concat(df_list)

    # Reorder the columns.
    col_order = ["date", "midpoint"] + sorted(
        [col for col in big_df if col not in ["date", "midpoint"]]
    )

    # Return the result.
    return big_df[col_order]


def _get_source_urls() -> pd.DataFrame:
    """Scrape a list of all the URLs that contain projection tables.

    Returns:
        pd.DataFrame: A DataFrame with the columns "url" and "date".

    Example:
        >>> df = _get_source_urls()
        >>> df.head()
           url                                            date
        0  https://www.federalreserve.gov/monetarypoli... 2012-01-25
    """
    # Get the root url, which lists all the FOMC meetings.
    root_url = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
    html = utils.get_url(root_url)

    # Parse the HTML and extract the URLs.
    soup = BeautifulSoup(html, "html.parser")
    target_links = soup.find_all(
        "a", href=lambda href: href and "fomcprojtabl" in href and ".htm" in href
    )

    # Convert the list of URLs into a DataFrame.
    df = pd.DataFrame(
        dict(url=f"https://www.federalreserve.gov{a['href']}") for a in target_links
    )

    # Parse the date from the URL.
    df["date"] = df.url.apply(utils.parse_date)

    # Sort the DataFrame by date.
    sorted_df = df.sort_values("date")

    # Return the result.
    return sorted_df


def _parse_source_url(url: str, date: datetime) -> pd.DataFrame:
    """Parse projections from the provided URL.

    Args:
        url (str): The URL to parse.
        date (datetime): The date of the FOMC meeting.

    Returns:
        pd.DataFrame: A DataFrame with the columns "date", "midpoint", and the projections.
    """
    # Get the HTML from the URL.
    html = utils.get_url(url)
    soup = BeautifulSoup(html, "html.parser")

    # Find the table with the projections.
    target_h4 = soup.find(
        ["h4", "h5"],
        string=lambda text: text
        and "assessments of appropriate monetary policy" in text.lower(),
    )
    target_table = target_h4.find_next("table")

    # Extract the headers from the table.
    headers = [utils.safestr(th.text) for th in target_table.thead.tr.find_all("th")]

    # Create a list to hold the rows.
    row_list = []

    # Loop through the rows
    for tr in target_table.tbody.find_all("tr"):
        # Create a dictionary to hold the row data.
        row_dict = {}

        # Loop through the cells in the row.
        cell_list = tr.find_all(["th", "td"])
        for i, cell in enumerate(cell_list):
            # Get the header for the cell.
            header = slugify(str(headers[i]), separator="_")

            # Set the cell value in the row dictionary.
            row_dict[header] = utils.safestr(cell.text)

        # Append the row dictionary to the list of rows.
        row_list.append(row_dict)

    # Convert the list of rows into a DataFrame.
    df = pd.DataFrame(row_list)

    # Add the date to the DataFrame.
    df["date"] = date

    # Rename the first column to "midpoint".
    df.rename(columns={df.columns[0]: "midpoint"}, inplace=True)

    # Return the result.
    return df


if __name__ == "__main__":
    """Scrape the data and print it to stdout as a CSV."""
    # Scrape the data
    df = scrape()

    # Print the dataframe to stdout as a CSV
    df.to_csv(sys.stdout, index=False)
