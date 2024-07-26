import requests
from bs4 import BeautifulSoup, Comment
import re
from urllib.parse import urljoin, urlparse
import time

def get_emails_from_url(start_url, max_depth=2):
    def scrape(url, visited_urls, visited_domains, depth, start_time):
        if depth > max_depth:
            return set()

        # Parse the current domain
        domain = urlparse(url).netloc

        # Check if URL has already been visited
        if url in visited_urls:
            return set()

        # Mark the URL as visited
        visited_urls.add(url)
        visited_domains.add(domain)

        # Send a GET request to the URL
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Failed to retrieve the webpage: {url} Error: {e}")
            return set()

        # Print the status and elapsed time
        elapsed_time = time.time() - start_time
        print(f"Scanning {url} at depth {depth}, elapsed time: {elapsed_time:.2f} seconds")

        # Parse the HTML content of the page
        soup = BeautifulSoup(response.text, 'html.parser')

        # Use a regular expression to find all email addresses in text and comments
        email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        emails = set(re.findall(email_pattern, soup.get_text()))

        # Check for email addresses in HTML comments
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        for comment in comments:
            emails.update(re.findall(email_pattern, comment))

        # Check for email addresses in attributes
        for tag in soup.find_all(True):
            for attr, value in tag.attrs.items():
                if isinstance(value, list):
                    for item in value:
                        emails.update(re.findall(email_pattern, item))
                else:
                    emails.update(re.findall(email_pattern, value))

        # Print found emails
        if emails:
            print(f"Emails found on {url}: {emails}")
        else:
            print(f"No emails found on {url}")

        # Find all the links on the page
        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href']
            # Join the URL if it's relative
            full_url = urljoin(url, href)
            link_domain = urlparse(full_url).netloc

            # Only follow links within the same domain or to a new domain within the allowed depth
            if link_domain == domain:
                emails.update(scrape(full_url, visited_urls, visited_domains, depth, start_time))
            elif link_domain not in visited_domains:
                emails.update(scrape(full_url, visited_urls, visited_domains, depth + 1, start_time))

        return emails

    visited_urls = set()
    visited_domains = set()
    start_time = time.time()
    return scrape(start_url, visited_urls, visited_domains, 0, start_time)

# Example usage
start_url = 'https://www.example.com/'
max_depth = 0  # Change this to set the degrees of freedom for different domains
emails = get_emails_from_url(start_url, max_depth)
print(f"Emails found: {emails}")
