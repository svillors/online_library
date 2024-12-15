import requests
import os
import argparse
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urljoin, urlsplit, unquote


def check_for_redirect(url):
    response = requests.get(url)
    response.raise_for_status()
    if response.history:
        raise HTTPError


def download_books(start_id=1, end_id=10):
    for id in range(start_id, end_id + 1):
        try:
            downloading_url = f'https://tululu.org/txt.php?id={id}'
            check_for_redirect(downloading_url)
            response = requests.get(f'https://tululu.org/b{id}/')
            book_data = parse_book_page(response)
            download_image(book_data['image_url'])
            download_txt(downloading_url, f'{id}. {book_data['title']}')
        except HTTPError:
            pass


def download_txt(url, filename, folder='books'):
    response = requests.get(url)
    response.raise_for_status()
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, sanitize_filename(filename) + '.txt')
    with open(filepath, 'wb') as file:
        file.write(response.content)
    return filepath


def download_image(url, folder='images'):
    response = requests.get(url)
    response.raise_for_status()
    os.makedirs(folder, exist_ok=True)
    filename = unquote(urlsplit(url).path).split('/').pop()
    filepath = os.path.join(folder, sanitize_filename(filename))
    with open(filepath, 'wb') as file:
        file.write(response.content)
    return filepath


def parse_book_page(source):
    book = {}
    soup = BeautifulSoup(source.text, 'lxml')
    book['author'] = soup.find('h1').text.split('::').pop().strip()
    book['title'] = soup.find('h1').text.split('::')[::-1].pop().strip()
    book['genre'] = [genre.text.strip() for genre in soup.find(
        'span', class_='d_book').find_all('a')]
    book['comments'] = [comment.find('span').text for comment in soup.find_all(
        class_='texts')]
    book['image_url'] = urljoin(
        source.url, soup.find(class_='bookimage').find('img')['src'])
    return book


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Скачивает обложки книг и сами книги с сайта "tululu.org"')
    parser.add_argument('-start_id', default=1)
    parser.add_argument('-end_id', default=10)
    args = parser.parse_args()
    download_books(args.start_id, args.end_id)
