import urllib.request
import bs4

f = open('durant.txt', 'r')
resulttext = f.read()
soup = bs4.BeautifulSoup(resulttext, "html5lib")
advTable = soup.body.find_all(id="advanced")
print(advTable)
