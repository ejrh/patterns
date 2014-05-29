import sys
import math
import tokenize
from StringIO import StringIO

def translate(p, a, l):
    x,y = p
    return x + math.cos(a) * l, y + math.sin(a) * l


def polygon(pt, num, layers=[0]):
    x,y,a,z = pt
    pts = []
    params = [[] for offset in layers]
    da = math.pi*2.0 / num
    f = 1/math.cos(da/2.0)
    for i in range(num):
        pts.append((x,y,a+math.pi,z))
        x,y = (translate((x,y), a+math.pi/2.0, z*0.5))
        j = 0
        for offset in layers:
            params[j].append(translate((x,y), a - da/2.0, f*offset))
            j += 1
        a -= da
        x,y = (translate((x,y), a+math.pi/2.0, z*0.5))
    ps = []
    for param in params:
        ps.append('M %s Z' % ' '.join(['%f,%f' % p for p in param]))
    print """<path fill-rule="evenodd" d="%s" />""" % ' '.join(ps)
    return pts

def p4(pt):
    return polygon(pt, 4, [0, 0.1, 0.5, 1.0])

def p6(pt):
    return polygon(pt, 6, [0, 0.1, 0.5, 1.0])

def p8(pt):
    return polygon(pt, 8, [0, 0.1, 0.5, 1.0])

def e(pt):
    x,y,a,z = pt
    x1,y1 = translate(translate((x,y), a+math.pi/2.0, z*0.5), a, 1.0)
    x2,y2 = translate(translate((x,y), a-math.pi/2.0, z*0.5), a, 1.0)
    #print """<path stroke="black" d="M %f,%f L %f,%f" />""" % (x1,y1,x2,y2)
    return []

def s(pt):
    x,y,a,z = pt
    x1,y1 = translate((x,y), a+math.pi/2.0, z*0.5)
    x2,y2 = translate((x,y), a-math.pi/2.0, z*0.5)
    #print """<path stroke="silver" d="M %f,%f L %f,%f" />""" % (x1,y1,x2,y2)
    return []

def draw_shape(points, shape_data, functions):
    points = points[:]
    outpoints = []
    instrs = tokenize.generate_tokens(StringIO(shape_data).next)
    stack = [None]
    for type,instr,start,end,line in instrs:
        #print >>sys.stderr, 'instr:', instr
        if instr == '(':
            stack.append(points)
            points = outpoints
            outpoints = []
        elif instr == ')' or instr == '':
            while len(outpoints) > 0:
                if len(outpoints) == num_outpoints:
                    f = functions['s']
                else:
                    f = functions['e']
                inpoint = outpoints.pop(0)
                f(inpoint)
            while len(points) > 0:
                f = functions['e']
                inpoint = points.pop(0)
                f(inpoint)
            outpoints = points
            points = stack.pop()
        else:
            while len(outpoints) > 0:
                if len(outpoints) == num_outpoints:
                    f = functions['s']
                else:
                    f = functions['e']
                inpoint = outpoints.pop(0)
                f(inpoint)
            f = functions[instr]
            inpoint = points.pop(0)
            outpoints = f(inpoint)
            num_outpoints = len(outpoints)

print """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg width="100%" height="100%" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">"""
point = 0.0,0.0,0.0,10.0
cube_data = """p4(p4 p4(s e p4 e) p4 p4)"""
orange_data1 = """p8(p4(s e p8(s e p4 e p4 p6)) p6 p4(s e p8(s e p4 e p4 p6)) p6 p4(s e p8(s e p4 e p4 p6)) p6 p4(s e p8(s e p4 e p4(s e p8) p6)) p6)"""
orange_data2 = """p4(p6(s e p4 p6) p6(s e p4 p6) p6(s e p4 p6) p6(s e p4 p6(s e e p4)))"""

draw_shape([point], orange_data2, locals())
print """</svg>"""
