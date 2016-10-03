#!/usr/bin/env python
import string
import sys

class Node:
    def __init__(self, name, value=0):
        self.name = name
        self.value = value
        self.queue = []
        self.initted = False

    def dequeue(self):
        if self.queue:
            self.value = self.queue[0]
            self.queue = self.queue[1:]

    def getValue(self):
        if not self.initted:
            self.dequeue()
            self.initted = True
        r = self.value
        self.dequeue()
        return r

    def setValue(self, f):
        self.queue.append(f)

class StdNode(Node):
    def setValue(self, f):
        if type(f) != 'str':
            f = '%s' % f
        if self.name == 'stderr':
            sys.stderr.write(f)
        else:
            sys.stdout.write(f)

def readfile(fname):
    with open(fname, 'r') as fd:
        return [x.strip() for x in fd.readlines()]
    return []

def solveLeft(l):
    if not l:
        raise ValueError('Invalid empty left value')
    if l[0] == '\'':
        v = l
        v = v.replace('\\n', '\n')
        v = v.replace('\\t', '\t')
        v = v.replace('\\r', '\r')
        v = v[1:-1]
        if len(v) != 1:
            raise ValueError('Invalid input: %s' % l)
        return ord(v)

    if l[0] == '-' or l[0].isdigit():
        return int(l)

    return l

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
            return None
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
        elif expect_end:
            tmp += c
        elif c == ' ' or c == '\t':
            pass
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
    try:
        items['left'] = solveLeft(items['left'])
    except:
        print 'ERROR: %s' % items
        sys.exit(2)
    return items

def parse(data):
    code = []
    for line in data:
        r = parseLine(line)
        if r is not None:
            code.append(r)
    return code

def interpret(code, env):
    for c in code:
        r = None
        l = None

        if type(c['left']) == int:
            l = Node('', c['left'])
        else:
            l = c['left']
            if l not in env:
                env[l] = Node(l)
            l = env[l]
        if c['right']:
            r = c['right']
            if r not in env:
                env[r] = Node(r)
            r = env[r]

        if c['oper'] == '->':
            r.setValue(l.getValue())
        elif c['oper'] == '-!>':
            r.setValue(chr(l.getValue()))
        elif c['oper'] == '-->':
            r.setValue(int(l.getValue()))

def defaultEnv():
    return {
        'stdout': StdNode('stdout'),
        'stderr': StdNode('stderr'),
    }

def esola():
    if len(sys.argv) <= 1:
        print 'Usage: %s file.esola' % (sys.argv[0])
        sys.exit(1)

    data = readfile(sys.argv[1])
    code = parse(data)
    interpret(code, env=defaultEnv())

if __name__ == '__main__':
    esola()
