#!/usr/bin/python
import csv
import os.path
import re
from urllib2 import urlopen

TARGETS = [
    # eater2 variants
    ('$b2obo$b2ob2o2$b2obo$2bo!', '6o$o2bobo$o2bo$6o$o2bo$2obo!'), # canonical
    ('$b2obo$b2obo$5bo$b2obo$2bo!', '5o$o2bobo$o2bobo$5o$o2bo$2obo!'), # smallest bounding box
    ('4bo$b2o2bo$b2obo$4bo$ob2o$bo!', '4o$o2b2o$o2bobo$4obo$bo2b2o$2b3o!'), # hedonismbot
    ('4bo$b2o2bo$b2obo$4bo$b2obo$bo!', '4o$o2b2o$o2bobo$4obo$o2bobo$ob2o!'), # thinker
    ('4bo$b2o2bo$b2obo$4bo$b2obo$2bo!', '4o$o2b2o$o2bobo$4obo$o2bobo$2obo!'), # bored
    ('4bo$b2o2bo$b2obo$4bo$b2obo!', '4o$o2b2o$o2bobo$4obo$o2bobo$b2o!'), # jordan
    ('4bo$b2o2bo$b2obo$4bo$b2o$3bo!', '4o$o2b2o$o2bobo$4obo$o2b2o$b2o!'), # triskelion
    ('$b2obo$b2ob2o2$ob2o$2bo!', '6o$o2bobo$o2bo$6o$bo2bo$bob2o!'), # boulders
    ('$b2obo$b2obo$5bo$ob2o$2bo!', '5o$o2bobo$o2bobo$5o$bo2bo$bob2o!'), # waiter

    # eater2 precursors
    ('$4bo$4b2o2$b2obo$2bo!', '3b3o$3bobo$3bo$6o$o2bo$2obo!'), # canonical
    ('$4bo$4bo$5bo$b2obo$2bo!', '3b2o$3bobo$3bobo$5o$o2bo$2obo!'), # smallest bounding box
    ('4bo$5bo$4bo$4bo$ob2o$bo!', '3bo$3b2o$3bobo$4obo$bo2b2o$2b3o!'), # hedonismbot
    ('4bo$5bo$4bo$4bo$b2obo$bo!', '3bo$3b2o$3bobo$4obo$o2bobo$ob2o!'), # thinker
    ('4bo$5bo$4bo$4bo$b2obo$2bo!', '3bo$3b2o$3bobo$4obo$o2bobo$2obo!'), # bored
    ('4bo$5bo$4bo$4bo$b2obo!', '3bo$3b2o$3bobo$4obo$o2bobo$b2o!'), # jordan
    ('4bo$5bo$4bo$4bo$b2o$3bo!', '3bo$3b2o$3bobo$4obo$o2b2o$b2o!'), # triskelion
    ('$4bo$4b2o2$ob2o$2bo!', '3b3o$3bobo$3bo$6o$bo2bo$bob2o!'), # boulders
    ('$4bo$4bo$5bo$ob2o$2bo!', '3b2o$3bobo$3bobo$5o$bo2bo$bob2o!'), # waiter
]

TRANSFORMATIONS = [
    [1, 0, 0, 1],
    [0, -1, 1, 0],
    [-1, 0, 0, -1],
    [0, 1, -1, 0],
    [-1, 0, 0, 1],
    [0, 1, 1, 0],
    [1, 0, 0, -1],
    [0, -1, -1, 0],
]

def decode_rle(encoded):
    x, y = 0, 0
    pos = 0
    cells = set()
    while pos < len(encoded):
        prev = pos
        while 48 <= ord(encoded[pos]) < 58:
            pos += 1

        n = int(encoded[prev:pos]) if pos > prev else 1
        ch = encoded[pos]
        if ch == '$':
            y += n
            x = 0
        elif ch == 'b':
            x += n
        elif ch == 'o':
            for i in range(0, n):
                cells.add((x, y))
                x += 1

        pos += 1

    return cells

def decode_wechsler(encoded):
    _, encoded = encoded.split('_', 1)

    cells = set()
    x, y = 0, 0
    pos = 0
    while pos < len(encoded):
        ch = encoded[pos]
        if ch == 'w':
            x += 2
        elif ch == 'x':
            x += 3
        elif ch == 'y':
            pos += 1
            x += 4 + int(encoded[pos], 36)
        elif ch == 'z':
            x = 0
            y += 5
        else:
            value = int(ch, 36)
            for n in range(0, 5):
                if value & (1 << n):
                    cells.add((x, y+n))
            x += 1

        pos += 1

    return cells

def match_pattern(pattern, wanted, unwanted):
    for pivot in wanted:
        break
    if not pivot:
        return None

    for x, y in pattern:
        failed = False

        for i, j in wanted:
            if (x+i-pivot[0], y+j-pivot[1]) not in pattern:
                failed = True
                break

        if failed:
            continue

        for i, j in unwanted:
            if (x+i-pivot[0], y+j-pivot[1]) in pattern:
                failed = True
                break

        if failed:
            continue

        return True

    return False

def transform_pattern(pattern, dx, dy, dxx = 1, dxy = 0, dyx = 0, dyy = 1):
    cells = set()
    for x, y in pattern:
        cells.add((x*dxx + y*dxy + dx, x*dyx + y*dyy + dy))
    return cells

def get_patterns():
    if not os.path.exists('census.txt'):
        remote = urlopen('http://catagolue.appspot.com/textcensus/b3s23/C1')
        census = open('census.txt', 'w')
        census.write(remote.read())
        census.close()

    census = open('census.txt', 'r')
    patterns = []
    for row in csv.reader(census):
        if row[0] == 'apgcode':
            continue
        patterns.append(row)
    census.close()
    return patterns

targets = []
for t in TARGETS:
    targets.append((decode_rle(t[0]), decode_rle(t[1])))

for pattern, freq in get_patterns():
    if pattern[:2] != 'xs':
        continue

    decoded = decode_wechsler(pattern)
    for t in TRANSFORMATIONS:
        p = transform_pattern(decoded, 0, 0, *t)
        for target in targets:
            if match_pattern(p, *target):
                print(pattern + " " + freq)
                break
        else:
            continue
        break
