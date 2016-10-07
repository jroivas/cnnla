#!/usr/bin/env python
import pprint
import copy
import string
import sys

def defaultEnv():
    return {
        'nodes': {
            'stdout': StdNode('stdout'),
            'stderr': StdNode('stderr'),
        },
        'blocks': {},
        'connections': []
    }

def mergeEnv(env, src={}):
    for b in src['blocks']:
        env['blocks'][b] = copy.deepcopy(src['blocks'][b])
    for b in src['nodes']:
        env['nodes'][b] = copy.deepcopy(src['nodes'][b])

class Node(object):
    def __init__(self, name, value=0):
        self.name = name
        self.value = value
        self.initted = False
        self.queue = []

    def getValue(self):
        if not self.initted and self.queue:
            self.value = self.queue[0]
            self.queue = self.queue[1:]
        return self.value

    def setValue(self, f):
        if type(f) == 'str':
            f = ord(f)
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
        return '<Node: %s, value: %s>' % (self.name, self.value)

class StdNode(Node):
    def setValue(self, f):
        if type(f) != 'str':
            f = '%s' % f
        if self.name == 'stderr':
            sys.stderr.write(f)
        else:
            sys.stdout.write(f)

class BlockNode(Node):
    def __init__(self, name, value=0):
        super(BlockNode, self).__init__(name, value)
        self.env = defaultEnv()

    def setCode(self, f):
        self.code = f

    def setInterpret(self, intp):
        self.intp = intp

    def setEnv(self, env):
        mergeEnv(self.env, env)

    def reset(self):
        self.setEnv(self.env)

    def setValue(self, v):
        self.env['nodes']['in'] = Node('in', v)
        self.env['nodes']['out'] = Node('out', 0)
        self.intp(self.code, self.env, verb=False)
        self.value = self.env['nodes']['out'].getValue()

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

    if len(l) >= 3 and l[0:2] == '0x':
        return int(l, 16)

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
        elif tmp and stock == 'oper' and c in ['-', '+', '*', '/', '!', '|', '?']:
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
        elif c == '{' and not items['collection']:
            items['collection'] = '{'
        elif c == '}':
            items['collection'] = '}'
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

def buildnet(code, env):
    new_code = []
    collecting = ''

    for c in code:
        if c['collection']:
            if c['collection'] == '{':
                l = c['left']
                collecting = l
                if not collecting in env['blocks']:
                    env['blocks'][collecting] = []
                if l not in env['nodes']:
                    env['nodes'][l] = BlockNode(l)
                    env['nodes'][l].setInterpret(interpret)
            elif c['collection'] == '}':
                env['blocks'][collecting] = buildnet(env['blocks'][collecting], env['nodes'][collecting].env)
                env['nodes'][collecting].setCode(env['blocks'][collecting])
                collecting = ''
            else:
                raise ValueError('Invalid collection: %s' % c['collection'])
            continue
        elif collecting:
            env['blocks'][collecting].append(c)
            env['nodes'][collecting].setCode(env['blocks'][collecting])
            continue

        elif c['oper'] == '->':
            if type(c['left']) == int:
                new_code.append(c)
            else:
                if not c['right'] or not c['left']:
                    raise ValueError('Indvalid connecion: %s -> %s' % (c['left'], c['right']))
                env['connections'].append((c['left'], c['right']))
        else:
            new_code.append(c)

    for b in env['blocks']:
        env['nodes'][b].setEnv(env)

    return new_code

def evaluate(env, val, verb=False):
    for a, b in env['connections']:
        if a != val:
            continue

        if a not in env['nodes']:
            env['nodes'][a] = Node(a)
        if b not in env['nodes']:
            env['nodes'][b] = Node(b)
        env['nodes'][b].setValue(env['nodes'][a].getValue())
        if verb:
            print ('%s = %s (%s)' % (b, a, env['nodes'][a].getValue()))

def interpret(code, env, verb=False):
    collecting = ''
    for c in code:
        r = None
        l = None
        lname = ''
        rname = ''
        l_instant = False
        if verb:
            sys.stderr.write("%s\n" % c)

        if type(c['left']) == int:
            l_instant = True
            l = Node('', c['left'])
        else:
            lname = c['left']
            if lname not in env['nodes']:
                env['nodes'][lname] = Node(lname)
            l = env['nodes'][lname]
        if c['right']:
            rname = c['right']
            if rname not in env['nodes']:
                env['nodes'][rname] = Node(rname)
            r = env['nodes'][rname]

        if not c['oper']:
            pass
        elif c['oper'] == '->':
            if l_instant:
                r.setValue(l.getValue())
                evaluate(env, rname, verb)
        elif c['oper'] == '-!>':
            r.setValue(chr(l.getValue()))
            evaluate(env, rname, verb)
        elif c['oper'] == '-+>':
            r.addValue(l.getValue())
            evaluate(env, rname, verb)
        elif c['oper'] == '-*>':
            r.mulValue(l.getValue())
            evaluate(env, rname, verb)
        elif c['oper'] == '-/>':
            r.divValue(l.getValue())
            evaluate(env, rname, verb)
        elif c['oper'] == '-->':
            r.setValue(int(l.getValue()))
            evaluate(env, rname, verb)
        elif c['oper'] == '-?>':
            v = int(l.getValue())
            if v:
                r.setValue(v)
                evaluate(env, rname, verb)
        elif c['oper'] == '-?!>':
            v = int(l.getValue())
            if not v:
                r.setValue(v)
                evaluate(env, rname, verb)
        elif c['oper'] == '-|>' and not c['right']:
            l.reset()
            if lname:
                evaluate(env, lname, verb)
        elif c['oper'] == '<-' and c['right']:
            env['nodes']['out'] = Node('out', r.getValue())
        else:
            raise ValueError('Invalid operator: %s in %s %s %s' % (c['oper'], c['left'], c['oper'], c['right']))

def cnnla(fname):
    data = readfile(fname)
    code = parse(data)
    env = defaultEnv()
    code = buildnet(code, env)

    interpret(code, env)

if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print ('Usage: %s file.cnnla' % (sys.argv[0]))
        sys.exit(1)

    cnnla(sys.argv[1])
