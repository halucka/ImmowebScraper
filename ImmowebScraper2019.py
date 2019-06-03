#!/usr/bin/python3

"""
Adapted from:
https://gist.github.com/hbro/e8a640851bb8b076c37394903f28adf4
hbro/ImmowebScraper.py

Usage:
- Install the requirements
-- python3
-- selenium  (to install run: pip3 install selenium)
-- chromedriver (http://chromedriver.chromium.org/downloads) -> this should be visible in your OS path, but worked for me out of the box

- Let less secure apps access your Gmail account (this is because this script contains your password in plain text) 
  instructions here: https://support.google.com/accounts/answer/6010255
  it can take few minutes until the settings are adapted, I recommend to disable this after you are finished house hunting / running the code

- Fill in the settings below, then run with `python3 ImmowebScraper2019.py`.
- Each run opens a chrome window for couple of seconds, this is because Immoweb blocks headless connections from webscrapers

- First run won't send any mails (or you'd get dozens at once), then you'll get email for any new property matching your parameters

"""

import sqlite3
from selenium import webdriver
import smtplib
from email.mime.text import MIMEText

# settings
# adapt the url to your needs (e.g. do a manual search on immoweb with your parameters and copy the url here)
url = 'http://www.immoweb.be/nl/zoek/huis/te-koop?zips=2640,2610,2070&minprice=150000&maxprice=350000&minroom=2&maxroom=4'
maxpages = 5
emailaddress = 'yourEmail@gmail.com'
smtp_host = 'smtp.gmail.com'
smtp_port = '587'
smtp_mail = 'yourEmail@gmail.com'
smtp_user = 'yourEmail@gmail.com'
smtp_pass = 'yourPassword'


# prepare the option for the chrome driver
options = webdriver.ChromeOptions()
#options.add_argument('headless')
db = sqlite3.connect('ImmowebScraper.db')
c = db.cursor()
browser = webdriver.Chrome(chrome_options=options)
browser.implicitly_wait(5)
smtpserver = smtplib.SMTP(smtp_host, smtp_port)
smtpserver.ehlo()
smtpserver.starttls()
smtpserver.login(smtp_user, smtp_pass)

# create the immos table
c.execute('CREATE TABLE IF NOT EXISTS immos (id INTEGER PRIMARY KEY UNIQUE NOT NULL);')
db.commit()

# if there are no id's yet, this is the first run
c.execute('SELECT COUNT(*) FROM immos;')
firstRun = c.fetchone()[0] == 0

# zhu li, do the thing
for page in range(1,maxpages+1):
    print('Browsing page {} ...'.format(page))
    browser.get(url + '&page=' + str(page))
    results = browser.find_elements_by_xpath('//div[@id="result"]/div')
    for i, result in enumerate(results):
            immoweb_id = result.get_attribute('id')
            print(i, immoweb_id)
            c.execute('SELECT COUNT(*) FROM immos WHERE id=:id;', {'id':immoweb_id})
            if c.fetchone()[0] == 0:
                immoweb_text = result.find_element_by_tag_name('a').text
                print(immoweb_text)
                immoweb_url = result.find_element_by_tag_name('a').get_attribute('href')
                print('New property found: ID {}! Storing in db.'.format(immoweb_id))
                c.execute('INSERT INTO immos(id) VALUES (:id);', {'id':immoweb_id})
                db.commit()
                if not firstRun:
                    print('Sending mail about new property ID {}.'.format(immoweb_id))
                    immoweb_text = result.find_element_by_tag_name('a').text
                    immoweb_url = result.find_element_by_tag_name('a').get_attribute('href')
                    message = immoweb_text + '\nURL: ' + immoweb_url
                    email = MIMEText(message.encode('utf-8'), 'plain', 'utf-8')
                    email['Subject'] = 'New property on Immoweb: {}'.format(immoweb_id)
                    email['From'] = smtp_user
                    email['To'] = emailaddress
                    smtpserver.sendmail(smtp_user,emailaddress,email.as_string())
smtpserver.quit()
db.close()
browser.close()
