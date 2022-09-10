import argparse
from pathlib import Path
import os

from bs4 import BeautifulSoup
import requests
import zipfile

parser = argparse.ArgumentParser(description='A Mangakakalot downloader')

parser.add_argument('-b', '--book', type=str,
                    help='use this to download a manga book')

parser.add_argument('-c', '--chapter', type=str,
                    help='use this to download a manga chapter')

args = parser.parse_args()

# check for no args
if args.book is None and args.chapter is None:
    parser.print_help()
    exit(1)

# check for trying to download a book and a chapter
if args.book is not None and args.chapter is not None:
    print('You may only download a book or a chapter!')
    exit(1)


def make_file_safe(path):
    return "".join([c for c in path if c.isalpha() or c.isdigit() or c == ' ' or c == '.' or c == '-']).rstrip()


def get_name(url):
    # get webpage HTML
    html = requests.get(url).text
    document = BeautifulSoup(html, 'html.parser')
    return document.find('h1').text


def get_chapters(url):
    # get webpage HTML
    html = requests.get(url).text
    document = BeautifulSoup(html, 'html.parser')
    # find all links that are inside a span class
    # if we don't check for span class, we get links to chapters that haven't yet been released
    spans = document.find_all('span')
    links = []
    for span in spans:
        for link in span.find_all('a'):
            links.append(link.get('href'))
    # check if the link is a chapter link
    chapters = []
    for link in links:
        if '/chapter/' in link:
            chapters.append(link)

    return chapters


def get_pages(url):
    # get webpage HTML
    html = requests.get(url).text
    document = BeautifulSoup(html, 'html.parser')
    images = []
    for image in document.find_all('img'):
        src = image.get('src')
        # detects if the image is part of a chapter by looking for the word "chapter" in the image URL
        # a bit of a scuffed way to do this, but I haven't found a time when it fails
        if 'chapter' in src:
            images.append(src)
    return images


def download_chapter(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/100.0',
               'Accept': 'image/avif,image/webp,*/*',
               'Accept-Encoding': 'gzip, deflate, br',
               'Accept-Language': 'en-US,en;q=0.5',
               'Referer': 'https://mangakakalot.com/'}
    pages = get_pages(url)
    if len(pages) == 0:
        print("No manga pages found for " + url)
        return
    for pgNum, page in enumerate(pages):
        extension = page.rsplit('.', 1)[-1]
        f = open('tmp/' + str(pgNum + 1) + '.' + extension, 'wb')
        f.write(requests.get(page, headers=headers).content)
        f.close()


if args.book is not None:
    if 'mangakakalot' not in args.book:
        print('Bad URL!')
        exit(1)
    if '/chapter/' in args.book:
        print('You have entered a chapter URL! Run again with -c instead of -b')
        exit(1)
    try:
        Path("tmp").mkdir(exist_ok=True)
        for file in os.listdir('tmp'):
            os.remove('tmp/' + file)
        book_name = get_name(args.book)
        print('Downloading ' + book_name)

        chapters = get_chapters(args.book)
        if len(chapters) == 0:
            print('No chapters found! Make sure this is the page for the manga')
            exit(1)

        chapters = reversed(chapters)

        Path(make_file_safe(book_name)).mkdir(exist_ok=True)

        for chapter in chapters:
            chapter_name = get_name(chapter)
            print('Downloading ' + chapter_name)
            download_chapter(chapter)
            z = zipfile.ZipFile(make_file_safe(book_name) + '/' + make_file_safe(chapter_name) + '.cbz', 'a')
            for file in os.listdir('tmp'):
                z.write('tmp/' + file, arcname=file)
                os.remove('tmp/' + file)
    except Exception as e:
        print(e.__str__())


else:
    if 'mangakakalot' not in args.chapter or 'chapter' not in args.chapter:
        print('Bad URL!')
        exit(1)
    try:
        Path("tmp").mkdir(exist_ok=True)
        for file in os.listdir('tmp'):
            os.remove('tmp/' + file)

        chapter_name = get_name(args.chapter)
        print('Downloading ' + chapter_name)
        download_chapter(args.chapter)
        z = zipfile.ZipFile(make_file_safe(chapter_name) + '.cbz', 'a')
        for file in os.listdir('tmp'):
            z.write('tmp/' + file, arcname=file)
            os.remove('tmp/' + file)
    except Exception as e:
        print(e.__str__())
