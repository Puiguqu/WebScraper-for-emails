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

def find_emails(url, visited=None, emails_seen=None, limit=50, max_depth=3, current_depth=0, start_time=None, max_time=3600):
    if visited is None:
        visited = set()
    if emails_seen is None:
        emails_seen = set()

    if len(visited) >= limit or current_depth >= max_depth:
        return set()

    if start_time and time.time() - start_time > max_time:
        print(f"Stopping search for {url} due to time limit exceeded.")
        return set()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    emails = set()
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text()
            found_emails = set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text))
            valid_emails = {email for email in found_emails if ',' not in email}
            new_emails = valid_emails - emails_seen
            emails_seen.update(new_emails)
            emails.update(new_emails)

            visited.add(url)
            base_url = "{0.scheme}://{0.netloc}".format(urlparse(url))
            for link in soup.find_all('a', href=True):
                link_url = urljoin(base_url, link['href'])
                if base_url in link_url and link_url not in visited and len(visited) < limit:
                    visited_emails = find_emails(link_url, visited, emails_seen, limit, max_depth, current_depth + 1, start_time, max_time)
                    emails.update(visited_emails)
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    
    return emails

def read_csv(file_path):
    return pd.read_csv(file_path)

def write_csv(data, file_path):
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)

def process_batch(batch, batch_number, output_folder, seen_websites, seen_emails):
    results = []
    for company in batch['Company Name']:
        print(f"Searching for: {company}")
        search_query = f"{company} official site"
        website = google_search(search_query)
        if website != "No results" and website not in seen_websites:
            try:
                start_time = time.time()
                emails = find_emails(website, limit=50, start_time=start_time, max_time=3600, emails_seen=seen_emails)
                elapsed_time = time.time() - start_time
                seen_websites.add(website)
                if emails:
                    email = ", ".join(emails)
                else:
                    email = "No email found"
                results.append({'Company Name': company, 'Website': website, 'Email': email, 'Search Time (seconds)': elapsed_time})
            except Exception as e:
                print(f"Error processing {company}: {e}")
                results.append({'Company Name': company, 'Website': website, 'Email': "Error occurred", 'Search Time (seconds)': "N/A"})
        else:
            results.append({'Company Name': company, 'Website': "No results" if website == "No results" else "Duplicate", 'Email': "No email found", 'Search Time (seconds)': "N/A"})
        time.sleep(2)  # Be polite and wait between requests to avoid being blocked

    output_file = os.path.join(output_folder, f'output_batch_{batch_number}.csv')
    write_csv(results, output_file)

def main(input_csv, output_folder, batch_size=30):
    queries = read_csv(input_csv)
    os.makedirs(output_folder, exist_ok=True)
    
    seen_websites = set()
    seen_emails = set()
    
    for i in range(0, len(queries), batch_size):
        batch = queries.iloc[i:i + batch_size]
        process_batch(batch, i // batch_size + 1, output_folder, seen_websites, seen_emails)

if __name__ == "__main__":
    input_csv = 'company_listings.csv'  # Path to your input CSV file
    output_folder = 'output_batches'  # Folder to save output CSV files

    main(input_csv, output_folder)
