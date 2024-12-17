import requests
import os
import argparse
from requests.exceptions import HTTPError, ConnectionError
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urljoin, urlsplit, unquote


def check_for_redirect(response):
    if response.history:
        raise HTTPError


def download_txt(response, filename, folder='books'):
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
    soup = BeautifulSoup(source.text, 'lxml')
    book = {
        'author': soup.find('h1').text.split('::').pop().strip(),
        'title': soup.find('h1').text.split('::')[::-1].pop().strip(),
        'genre': [genre.text.strip() for genre in soup.find(
            'span', class_='d_book').find_all('a')],
        'comments': [comment.find('span').text for comment in soup.find_all(
            class_='texts')],
        'image_url': urljoin(
            source.url, soup.find(class_='bookimage').find('img')['src'])
    }
    return book


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Скачивает обложки книг и сами книги с сайта "tululu.org"')
    parser.add_argument('start_id', default=1, type=int, nargs='?')
    parser.add_argument('end_id', default=10, type=int, nargs='?')
    args = parser.parse_args()
    for book_id in range(args.start_id, args.end_id + 1):
        try:
            params = {'id': book_id}
            response_for_txt = requests.get('https://tululu.org/txt.php',
                                            params=params)
            response_for_txt.raise_for_status()
            check_for_redirect(response_for_txt)
            response_for_info = requests.get(f'https://tululu.org/b{book_id}')
            response_for_info.raise_for_status()
            check_for_redirect(response_for_info)
            book_info = parse_book_page(response_for_info)
            download_image(book_info['image_url'])
            download_txt(response_for_txt,
                         f'{book_id}. {book_info['title']}')
        except HTTPError:
            print(f'Книга под номером {book_id} не найдена')
        except ConnectionError:
            print('Ошибка соеденения. Повторное соеденение')
