import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Function to send email
def send_email(to_address, subject, body, from_address, smtp_server, smtp_port, smtp_user, smtp_password):
    msg = MIMEMultipart()
    msg['From'] = from_address
    msg['To'] = to_address
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(smtp_user, smtp_password)
    text = msg.as_string()
    server.sendmail(from_address, to_address, text)
    server.quit()

# Read CSV file
csv_file = 'companies.csv'
df = pd.read_csv(csv_file)

# Email details
from_address = 'your_email@example.com'
smtp_server = 'smtp.example.com'
smtp_port = 587
smtp_user = 'your_smtp_username'
smtp_password = 'your_smtp_password'

for index, row in df.iterrows():
    company = row['Company']
    website = row['Website']
    email = row['Email']
    search_time = row['Search Time']

    # Custom email content
    subject = f'Introduction to Wing Loong Industries’ Solutions for {company}'
    body = f'''insert message here'''

    # Send email
    send_email(email, subject, body, from_address, smtp_server, smtp_port, smtp_user, smtp_password)
    print(f'Email sent to {company} at {email}')

print('All emails sent successfully!')
