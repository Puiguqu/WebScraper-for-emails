import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import pandas as pd
import time

keywords = ["Inc.", "Corp", "LLC", "Ltd", "Pte", "Limited"]

def is_valid_company(name):
    return any(keyword.lower() in name.lower() for keyword in keywords)

def truncate_company_name(name):
    last_index = -1
    last_keyword = ""
    for keyword in keywords:
        index = name.lower().find(keyword.lower())
        if index != -1 and index > last_index:
            last_index = index
            last_keyword = keyword
    if last_index != -1:
        return name[:last_index + len(last_keyword)]
    return name

def get_all_links(url, domain):
    print(f"Fetching links from {url}...")
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    links = set()
    for a_tag in soup.find_all('a', href=True):
        link = urljoin(url, a_tag['href'])
        if domain in urlparse(link).netloc:
            links.add(link)
    print(f"Found {len(links)} links on {url}")
    return links

def scrape_company_names(url, visited, domain):
    if url in visited:
        return []
    print(f"Scraping {url}...")
    visited.add(url)
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    company_tags = soup.find_all(['h2', 'h3', 'p'])
    companies = [truncate_company_name(tag.text.strip()) for tag in company_tags if is_valid_company(tag.text.strip())]
    print(f"Found {len(companies)} companies on {url}")

    links = get_all_links(url, domain)
    for link in links:
        companies.extend(scrape_company_names(link, visited, domain))

    return companies

if __name__ == '__main__':
    url = 'https://www.sg-electronics.com/company-listings'  # Replace with the actual URL
    domain = urlparse(url).netloc
    visited = set()

    print("Starting scraping process...")
    start_time = time.time()

    companies = scrape_company_names(url, visited, domain)

    unique_companies = list(set(companies))

    if unique_companies:
        df = pd.DataFrame(unique_companies, columns=['Company Name'])
        print("Scraping completed. Saving results...")

        # Save to a CSV file with a custom name
        csv_filename = 'company_listings.csv'
        df.to_csv(csv_filename, index=False)
        print(f'\nCompany names saved to {csv_filename}')
    else:
        print('No company names found.')

    end_time = time.time()
    print(f"Scraping process completed in {end_time - start_time:.2f} seconds.")
