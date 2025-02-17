import requests
from bs4 import BeautifulSoup

def scrap_document(url):
    """
    scrapes the text content of a medical document from the given url.

    this function extracts content from the url by first searching
    for a `<div>` element with the class "document". if not found, it looks for
    an `<article>` tag as fallback.

    args:
        url (str): the url of the document to be scraped

    returns:
        str or none: the extracted text content of the document if found; otherwise, none
    """

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        # find the div with class "document"
        document_div = soup.find('div', class_='document')
        if document_div:
            return document_div.get_text(strip=True)
        else:
            # try to find the article tag
            article_tag = soup.find('article')
            if article_tag:
                return article_tag.get_text(strip=True)
            else:
                return None
    return None

def retrieve_documents(search_term):
    """
    searches for medical documents on ncbi using duckduckgo and scrapes for link to articles/books.

    args:
        search_term (str): the medical term or topic to search for.

    returns:
        str: the extracted text content of the most relevant document, or an error message if no results are found.
    """
    search_url = "https://lite.duckduckgo.com/lite/"
    params = {"q": f"{search_term} site:ncbi.nlm.nih.gov"}

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    response = requests.post(search_url, data=params, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")

        # find all search result links
        result_links = soup.find_all("a", class_="result-link")

        if result_links:
            # extract href values
            hrefs = [result.get("href") for result in result_links if result.get("href")]

            """
            we are scraping duckduckgo for results, and sometimes, 
            the first link is an ad.
            """
            if "ncbi.nlm.nih.gov" in hrefs[0]:
                link = hrefs[0]
            elif len(hrefs) > 1:
                link = hrefs[1]
            else:
                return "No valid links found."

            print(f"{search_term}: {link}")
            return scrap_document(link)

    return "No results found."
