#!/usr/bin/env python
import string
import sys

class Node:
    def __init__(self, name, value=0):
        self.name = name
        self.value = value

def readfile(fname):
    with open(fname, 'r') as fd:
        return [x.strip() for x in fd.readlines()]
    return []

def parseLine(line):
    if not line.strip():
        return
    items = {
        'left': '',
        'right': '',
        'oper': '',
        'collection': ''
    }
    tmp = ''
    p = 1
    expect_end = False
    ret = False
    stock = 'left'
    for c in line:
        if c == '#':
            break
        elif c == ' ' or c == '\t':
            pass
        elif ret and c == '-':
            tmp += c
        elif ret:
            items[stock] = tmp
            stock = 'right'
            tmp = c
            items[stock] = tmp
            ret = False
        elif stock == 'left' and not tmp and c == '\'':
            tmp += c
            expect_end = True
        elif expect_end and c == '\'':
            tmp += c
            expect_end = False
        elif (not tmp and c in string.letters + '-') or (c in string.letters + string.digits):
            tmp += c
        elif tmp and c == '-' and stock == 'left':
            items[stock] = tmp
            stock = 'oper'
            tmp = c
        elif tmp and stock == 'oper' and c in ['-', '+', '*', '/', '!', '|']:
            tmp += c
        elif c == '<':
            items[stock] = tmp
            stock = 'oper'
            tmp += c
            ret = True
        elif tmp and stock == 'oper' and c == '>':
            items[stock] = tmp + c
            stock = 'right'
            tmp = ''
        elif c == '@' and not items['collection']:
            items['collection'] = '@'
        elif c == '@' and items['collection'] == '@':
            items['collection'] = '@@'
        else:
            print 'STOCK %s' % stock
            raise ValueError('Invalid input %s at %s ("%s")' % (line, p, c))
        p += 1
    items[stock] = tmp
    print items

def parse(data):
    for line in data:
        parseLine(line)

def esola():
    if len(sys.argv) <= 1:
        print 'Usage: %s file.esola' % (sys.argv[0])
        sys.exit(1)

    data = readfile(sys.argv[1])
    parse(data)

if __name__ == '__main__':
    esola()
