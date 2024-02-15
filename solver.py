import requests
from time import sleep
from random import random, shuffle
from itertools import product
from json import loads, dumps
from datetime import datetime


API = 'https://neal.fun/api/infinite-craft/pair'
HEADERS = {'Referer': 'https://neal.fun/infinite-craft/'}  # required to access the API, seems like rudimentary security

# save files
CREATION_TREE = 'creation_tree.json'
TO_TRY = 'to_try.txt'
FIRST_DISCOVERIES = 'first_discoveries.txt'

DELAY = None  # optional delay between requests, in seconds


# ANSI escape codes for colored text
class C:
    YELLOW = '\u001b[33m'
    MAGENTA = '\u001b[35m'
    CYAN = '\u001b[36m'
    GREEN = '\u001b[32m'
    RED = '\u001b[31m'
    BOLD = '\u001b[1m'
    UNDERLINE = '\u001b[4m'
    RESET = '\u001b[0m'


def solve():

    print()
    print(f'{C.BOLD}{C.RED}{C.UNDERLINE}Infinite Crafter{C.RESET}')
    print()
    print('Loading save files...')

    creation_tree, available_items, to_try = load_files()

    print()
    if DELAY is None:
        print(f'{C.CYAN}Running without a delay!{C.RESET}')
    else:
        print(f'{C.RED}Running with a delay of {DELAY} seconds!{C.RESET}')
    print()

    # try every combination of the available items not already tried
    while to_try:
        item1, item2 = to_try.pop()

        if DELAY is not None:
            sleep(random() * DELAY)
        response = requests.get(f'{API}?first={item1}&second={item2}', headers=HEADERS)

        # handle bad response, e.g. ratelimit
        if response.status_code != 200:
            print(f'{C.RED}Error with "{item1}" and "{item2}": {response.status_code}{C.RESET}')

            # try again unless the combination is just invalid (occurs when the item has a bad character, e.g. "+")
            if response.status_code != 500:
                to_try.append((item1, item2))
            continue

        data = response.json()
        emoji = data['emoji']
        is_new = data['isNew']
        result = data['result']

        # log the result
        print(f'{C.YELLOW}{item1}{C.RESET} + {C.YELLOW}{item2}{C.RESET} => {C.MAGENTA}{emoji} {result}{C.RESET}', end='')
        if is_new:  # handle first discovery
            print(f', {C.CYAN}{C.BOLD}{C.UNDERLINE}First Discovery!{C.RESET}')
            if FIRST_DISCOVERIES:
                with open(FIRST_DISCOVERIES, 'a') as f:
                    f.write(f'{datetime.now()} \t->\t {result}\n')
        elif result == 'Nothing':  # handle erroneous result due to server error
            print(f', {C.RED}XXX{C.RESET}')
            continue
        elif result not in available_items:  # handle subjectively new result
            print(f', {C.GREEN}New Item!{C.RESET}')
        else:  # handle known result
            print()

        # invalid result due to bad server generation, won't combine with anything else
        if '+' in result:
            print(f'\t{C.RED}Erroneous result is being omitted from future use...{C.RESET}')
            continue

        # if the result is new, add it to the available items and try it with the other available items
        if result not in available_items:

            # add the result to the creation tree and available items
            available_items.append(result)
            creation_tree[result] = [item1, item2]
            print(f'\tItem {C.GREEN}#{len(available_items)}{C.RESET} @ depth {C.GREEN}{find_depth(creation_tree, result)}{C.RESET}, adding to {C.GREEN}{len(to_try)}{C.RESET} combinations to try')
            if CREATION_TREE:
                with open(CREATION_TREE, 'w') as f:
                    f.write(dumps(creation_tree, indent=2))

            # add the result to the combinations to try
            new_combos = [(result, item) for item in available_items if item != result]
            to_try.extend(new_combos)
            if TO_TRY:
                with open(TO_TRY, 'a') as f:
                    f.write('\n'.join(['\t'.join(combo) for combo in new_combos]) + '\n')
            shuffle(to_try)


def load_files():
    """Load the save files, or create them if they don't exist."""

    creation_tree = {}
    available_items = ['Water', 'Fire', 'Wind', 'Earth']
    try:
        with open(CREATION_TREE, 'r') as f:
            creation_tree = loads(f.read().strip())
            available_items.extend(creation_tree.keys())
        print(f'{C.GREEN}Loaded {CREATION_TREE} with {len(available_items)} items!{C.RESET}')
    except FileNotFoundError:
        print(f'{C.RED}Creation tree save not found, using defaults: {C.YELLOW}{", ".join(available_items)}{C.RESET}')
        with open(CREATION_TREE, 'w') as f:
            f.write(dumps(creation_tree, indent=2))

    to_try = []
    try:
        with open(TO_TRY, 'r') as f:
            to_try = [tuple(combo.split('\t')) for combo in f.read().strip().split('\n')]
            shuffle(to_try)
        print(f'{C.GREEN}Loaded {TO_TRY} with {len(to_try)} combinations!{C.RESET}')
    except FileNotFoundError:
        print(f'{C.RED}to-try save not found, using defaults: {C.YELLOW}<{len(to_try)} items>{C.RESET}')
        to_try = list(product(available_items, repeat=2))
        shuffle(to_try)
        with open(TO_TRY, 'w') as f:
            f.write('\n'.join(['\t'.join(combo) for combo in to_try]) + '\n')

    try:
        with open(FIRST_DISCOVERIES, 'r') as f:
            first_discoveries = f.read().strip().splitlines()
            print(f'{C.GREEN}Loaded {FIRST_DISCOVERIES} with {len(first_discoveries)} first discoveries!{C.RESET}')
    except FileNotFoundError:
        print(f'{C.RED}First discoveries file not found, creating one with the name: "{FIRST_DISCOVERIES}"{C.RESET}')
        open(FIRST_DISCOVERIES, 'w').close()

    return creation_tree, available_items, to_try


def find_depth(creation_tree, result):
    """Find an item's depth through the creation tree."""
    for res, (ingredient_1, ingredient_2) in creation_tree.items():
        if res == result:
            return max(find_depth(creation_tree, ingredient_1), find_depth(creation_tree, ingredient_2)) + 1
    return 0


if __name__ == '__main__':
    solve()
