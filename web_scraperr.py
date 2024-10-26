import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time
from urllib.parse import urljoin, urlparse
from googlesearch import search
import os

def google_search(query):
    try:
        search_results = list(search(query, num_results=1))
        if search_results:
            return search_results[0]
    except Exception as e:
        print(f"Google search error: {e}")
    return "No results"

def find_emails(url, visited=None, limit=50):
    if visited is None:
        visited = set()

    if len(visited) >= limit:
        return set()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    emails = set()
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text()
            emails.update(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text))

            visited.add(url)
            base_url = "{0.scheme}://{0.netloc}".format(urlparse(url))
            for link in soup.find_all('a', href=True):
                link_url = urljoin(base_url, link['href'])
                if base_url in link_url and link_url not in visited and len(visited) < limit:
                    visited_emails = find_emails(link_url, visited, limit)
                    emails.update(visited_emails)
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
    
    return emails

def read_csv(file_path):
    return pd.read_csv(file_path)

def write_csv(data, file_path):
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)

def process_batch(batch, batch_number, output_folder):
    results = []
    for company in batch['Company Name']:
        print(f"Searching for: {company}")
        search_query = f"{company} official site"
        website = google_search(search_query)
        if website != "No results":
            emails = find_emails(website, limit=50)
            if emails:
                email = ", ".join(emails)
            else:
                email = "No email found"
            results.append({'Company Name': company, 'Website': website, 'Email': email})
        else:
            results.append({'Company Name': company, 'Website': "No results", 'Email': "No email found"})
        time.sleep(2)  # Be polite and wait between requests to avoid being blocked

    output_file = os.path.join(output_folder, f'output_batch_{batch_number}.csv')
    write_csv(results, output_file)

def main(input_csv, output_folder, batch_size=30):
    queries = read_csv(input_csv)
    os.makedirs(output_folder, exist_ok=True)
    
    for i in range(0, len(queries), batch_size):
        batch = queries.iloc[i:i + batch_size]
        process_batch(batch, i // batch_size + 1, output_folder)

if __name__ == "__main__":
    input_csv = 'company_listings.csv'  # Path to your input CSV file
    output_folder = 'output_batches'  # Folder to save output CSV files

    main(input_csv, output_folder)
