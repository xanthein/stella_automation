#!/usr/bin/env python3

import apt
import argparse
import logging
import json
import requests
from requests.exceptions import HTTPError

LOGFILE='/tmp/check_wallpaper.log'

def send_to_mm(mm_webhook:str, data: str):
    headers = {
        "Content-Type": "application/json",
    }

    json_data = json.dumps({'text': data})
    try:
        response = requests.post(mm_webhook, data=json_data, headers=headers)
        response.raise_for_status()
    except HTTPError as http_err:
        # This catches 4xx (Client Error) and 5xx (Server Error) status codes
        logging.error(f"HTTP error occurred: {http_err} (Status Code: {response.status_code})")

def check_wallpaper(exclude: list) -> list:
    cache = apt.Cache()

    logging.info('Start checking wallpaper')
    factory_meta_packages = []
    for pkg in cache.keys():
        if 'oem-stella-factory' in pkg:
            factory_meta_packages.append(pkg)

    failed_list = []
    for meta in factory_meta_packages:
        pkg = cache[meta]
        candidate_version = pkg.candidate
        if candidate_version:
            recommended_packages = candidate_version.recommends

            has_wallpaper = False
            for recommend in recommended_packages:
                if 'wallpaper' in recommend.rawstr:
                    has_wallpaper = True
            if not has_wallpaper and meta not in exclude:
                failed_list.append(meta)
                logging.info(f'{meta} did not recommend wallpaper')
    return failed_list

if __name__ == '__main__':
    logging.basicConfig(
        filename=LOGFILE,
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s'
    )

    parser = argparse.ArgumentParser()
    parser.add_argument('--exclude', dest='exclude_file', action='store', help='File store the exclude platforms')
    parser.add_argument('--mm_webhook', dest='mm_webhook', action='store', help='Mattermost WEB hook')
    args = parser.parse_args()

    exclude_list = []
    if args.exclude_file:
        logging.info(f'Use {args.exclude_file} as exclude file')
        try:
            with open(args.exclude_file, "r") as fd:
                exclude_list += fd.read().split()
        except FileNotFoundError:
            logging.error(f'{args.exclude_file} was not found.')

    failed_list = check_wallpaper(exclude_list)

    if len(failed_list) > 0:
        data = "Meta package not recommends wallpaper\n" + "\n".join(failed_list)
        send_to_mm(args.mm_webhook, data)

