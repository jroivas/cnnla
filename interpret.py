#!/usr/bin/env python
import copy
import string
import sys

class Node(object):
    def __init__(self, name, value=0):
        self.name = name
        self.value = value
        self.queue = []
        self.initted = False

    def dequeue(self):
        if self.queue:
            self.value = self.queue[0]
            self.queue = self.queue[1:]

    def _getValue(self):
        if not self.initted:
            self.dequeue()
            self.initted = True
        r = self.value
        self.dequeue()
        return r

    def getValue(self):
        return self._getValue()

    def setValue(self, f):
        self.queue.append(f)

    def solveValue(self, f):
        if type(f) == int:
            return f
        else:
            return ord(f)

    def addValue(self, f):
        self.value += self.solveValue(f)

    def mulValue(self, f):
        self.value *= self.solveValue(f)

    def divValue(self, f):
        v = self.solveValue(f)
        d = self.getValue()
        if v == 0:
            self.value = 0
        else:
            self.value /= v

    def reset(self):
        self.value = 0

    def __repr__(self):
        return '<Node: %s, value: %s, queue: %s>' % (self.name, self.value, len(self.queue))

class StdNode(Node):
    def setValue(self, f):
        if type(f) != 'str':
            f = '%s' % f
        if self.name == 'stderr':
            sys.stderr.write(f)
        else:
            sys.stdout.write(f)

class BlockNode(Node):
    def setCode(self, f):
        self.code = f

    def setEnv(self, env):
        #self.env = env
        self.env = {}

    def setInterpret(self, intp):
        self.intp = intp

    def setBlocks(self, b):
        self.blocks = b

    def reset(self):
        self.env = {}

    def setValue(self, v):
        env = self.env
        self.env['in'] = Node('in', v)
        self.env['out'] = Node('out', 0)
        self.intp(self.code, self.env, self.blocks, verb=False)
        self.value = self.env['out'].getValue()

def readfile(fname):
    with open(fname, 'r') as fd:
        return [x.strip() for x in fd.readlines()]
    return []

def solveLeft(l):
    l = l.strip()
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
        elif ret and c != ' ' and c != '\t':
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
        if items['oper'] != '<-' and not items['collection']:
            items['left'] = solveLeft(items['left'])
    except:
        print ('ERROR: %s' % items)
        sys.exit(2)

    items['right'] = items['right'].strip()
    return items

def parse(data):
    code = []
    for line in data:
        r = parseLine(line)
        if r is not None:
            code.append(r)
    return code

def interpret(code, env, blocks, verb=False):
    collecting = ''
    for c in code:
        r = None
        l = None
        if verb:
            sys.stderr.write("%s\n" % c)

        if c['collection']:
            if c['collection'] == '@':
                l = c['left']
                collecting = l
                if not collecting in blocks:
                    blocks[collecting] = []
                if l not in env:
                    env[l] = BlockNode(l)
                    env[l].setEnv(env)
                    env[l].setInterpret(interpret)
                    env[l].setBlocks(blocks)
            elif c['collection'] == '@@':
                collecting = ''
            else:
                raise ValueError('Invalid collection: %s' % c['collection'])
            continue
        elif collecting:
            blocks[collecting].append(c)
            env[collecting].setCode(blocks[collecting])
            continue

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
            if verb:
                print '%s = %s %s' % (r.name, l.name, l)
                print '%s = %s' % (r.name, l.getValue())
            r.setValue(l.getValue())
            if verb:
                print '%s = %s' % (r.name, r)
        elif c['oper'] == '-!>':
            r.setValue(chr(l.getValue()))
        elif c['oper'] == '-+>':
            r.addValue(l.getValue())
        elif c['oper'] == '-*>':
            r.mulValue(l.getValue())
        elif c['oper'] == '-/>':
            r.divValue(l.getValue())
        elif c['oper'] == '-->':
            r.setValue(int(l.getValue()))
        elif c['oper'] == '-|>' and not c['right']:
            l.reset()
        elif c['oper'] == '<-' and c['right']:
            env['out'] = Node('out', r.getValue())
        else:
            raise ValueError('Invalid operator: %s in %s %s %s' % (c['oper'], c['left'], c['oper'], c['right']))
        #if verb:
        #    sys.stderr.write("%s\n" % env)

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
    interpret(code, env=defaultEnv(), blocks={})

if __name__ == '__main__':
    esola()
