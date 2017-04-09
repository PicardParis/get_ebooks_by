# Copyright 2017 Laurent Picard
# Licensed under the Apache License, Version 2.0
# http://www.apache.org/licenses/LICENSE-2.0

import webapp2
import urllib
import urllib2
import json
from timeit import default_timer as timer


AUTHORS = [
  "Miguel de Cervantes",
  "Charles Dickens",
  "Antoine de Saint-Exupéry",
  "J. K. Rowling",
  "J. R. R. Tolkien",
  "Agatha Christie",
  "Lewis Carroll",
  "C. S. Lewis",
  "Dan Brown",
  "Arthur Conan Doyle",
  "Jules Verne",
  "Stephen King",
  "Stieg Larsson",
  "George Orwell",
  "Ian Fleming",
  "James Patterson",
  "Anne Rice",
  "Terry Pratchett",
  "George R. R. Martin",
  "Edgar Rice Burroughs",
  "Michael Connelly",
  "Jo Nesbo"
  ]

HTML_CONTENT_BEG = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Ebooks By Demo</title>
  <style>body{font-family: sans-serif}</style>
</head>
<body>
  <h1>Welcome</h1>
  <h2>List available ebooks written by</h2>
  <ul>'''
HTML_CONTENT_LI_FMT = '''
    <li><a href="./%s">%s</a></li>'''
HTML_CONTENT_END = '''
  </ul>
</body>
</html>'''

class ListAuthors(webapp2.RequestHandler):
  def get(self):
    self.response.headers["Content-Type"] = "text/html"
    self.response.write(HTML_CONTENT_BEG)
    for author in sorted(AUTHORS):
      li = (HTML_CONTENT_LI_FMT) % (
        urllib.quote_plus(author),
        author
        )
      self.response.write(li)
    self.response.write(HTML_CONTENT_END)


COUNTRY = "US"
BOOK_LG = "en"
BOOK_FIELDS = (
  "items("
    "id"
    ",accessInfo(epub/isAvailable)"
    ",volumeInfo(title,subtitle,language,pageCount)"
  ")"
  )

def GetGoogleBooksData(author):
  books = []
  errors = None
  pageBookIdx = 0
  pageBookCnt = 40 # Default: 10, Max: 40

  while True:
    
    # Request paginated data from Google Books API
    url = (
      "https://www.googleapis.com/books/v1/volumes?"
      "q={}"
      "&startIndex={}"
      "&maxResults={}"
      "&country={}"
      "&langRestrict={}"
      "&download=epub"
      "&printType=books"
      "&showPreorders=false"
      "&fields={}"
    ).format(
      urllib.quote_plus('inauthor:"%s"' % (author)),
      pageBookIdx,
      pageBookCnt,
      COUNTRY,
      BOOK_LG,
      urllib.quote_plus(BOOK_FIELDS)
    )
    
    reqPageData = None
    try:
      response = urllib2.urlopen(url)
      reqPageData = json.load(response)   
    except urllib2.HTTPError, err:
      errors = err.read()
      print "HTTPError = ", str(err.code)
    except:
      print "Error when handling\n", url
    
    if reqPageData is None:
      break

    pageBookItems = reqPageData.get("items", None)
    if pageBookItems is None:
      break

    books += pageBookItems
    itemCnt = len(pageBookItems)
    if itemCnt < pageBookCnt:
      # Do not issue another HTTP request
      break

    pageBookIdx += pageBookCnt
    # Loop and request next page data

  return books, errors


def PrintGoogleBooksData(books, response):
  if books:
    response.write("  # | Pages | Title\n")

    # Sort by largest page count
    def SortByPageCount(book):
      pageCount = book["volumeInfo"].get("pageCount", 0)
      return pageCount
    books.sort(key=SortByPageCount, reverse=True)

  i = 0
  for book in books:
    accessInfo = book["accessInfo"]

    # Skip books not available in epub (bug in Google Books API?)
    if not accessInfo["epub"]["isAvailable"]:
      continue

    volumeInfo = book["volumeInfo"]

    # Skip ebooks not in requested language (bug in Google Books API?)
    if volumeInfo["language"] <> BOOK_LG:
      continue

    title = volumeInfo["title"]
    subtitle = volumeInfo.get("subtitle", None)
    if subtitle is not None:
      title += " / " + subtitle
    pageCount = volumeInfo.get("pageCount", None)
    if pageCount is None:
      pageCount = ""
    else:
      pageCount = "{:,}".format(pageCount)

    i += 1
    response.write(u"{:3d} | {:>5} | {:.65}\n".format(i, pageCount, title))


class ListEbooksByAuthor(webapp2.RequestHandler):
  def get(self, author):
    author = urllib.unquote_plus(author)
    self.response.headers["Content-Type"] = "text/plain; charset=utf-8"

    caption = ' "%s" ebooks available on Google Books\n' % (author)
    border = "".ljust(len(caption),"=") + "\n"
    self.response.write(border)
    self.response.write(caption)
    self.response.write(border)

    start = timer()
    books, errors = GetGoogleBooksData(author)
    end = timer()

    if errors is None:
      PrintGoogleBooksData(books, self.response)
    else:
      self.response.write("### Error ###\n%s" % (errors))

    self.response.write(border)
    self.response.write(" Executed in %.1f s\n" % (end - start))
    self.response.write(border)


app = webapp2.WSGIApplication([
  ("/", ListAuthors),
  ("/(.*)", ListEbooksByAuthor),
], debug=True)
