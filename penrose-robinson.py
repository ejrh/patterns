import sys
import math
import random

class Archetype(object):
    def __init__(self, name, happy_sides, *segments):
        self.name = name
        self.segments = segments
        self.decors = []
        self.subshapes = []
        self.happy_sides = happy_sides
        self.internal_neighbour_rules = []
        self.external_neighbour_rules = {}
        
        self.points = []
        self.polar_points = []
        x = 0.0
        y = 0.0
        angle = 0.0
        for length, delta in self.segments:
            self.points.append((x, y))
            a = math.degrees(math.atan2(y, x))
            m = math.hypot(x, y)
            self.polar_points.append((a, m))
            x += length * math.cos(math.radians(angle))
            y += length * math.sin(math.radians(angle))
            angle += delta
            if angle >= 360.0:
                angle -= 360.0
    
    def reflect_segments(self):
        result = []
        for length, delta in self.segments:
            result.append((length, -delta))
        return result
    
    def generate(self, x, y, angle, scale):
        t = Triangle(self, x, y, angle, scale)
        return t
    
    def render_to_svg(self, args):
        parts = []
        
        args = dict(args)
        for i in range(len(self.points)):
            args['p%d' % i] = '%f,%f' % self.points[i]
        for path_str, decor_args, style_str in self.decors:
            args.update(decor_args)
            part = '<path %s d="%s" />' % (style_str % args, path_str % args)
            parts.append(part)
        
        return ''.join(parts)
    
    def add_decor(self, path_str, args, style_str):
        self.decors.append((path_str, args, style_str))
    
    def add_subshape(self, shape, pt, angle, scale, loneliness_rule=None):
        if loneliness_rule is None:
            loneliness_rule = {}
        self.subshapes.append((shape, pt, angle, scale, loneliness_rule))
    
    def add_internal_neighbour_rule(self, subshape, subshape_side, neighbour_subshape, neighbour_side):
        self.internal_neighbour_rules.append((subshape, subshape_side, neighbour_subshape, neighbour_side))
    
    def add_external_neighbour_rule(self, side, matches, rules):
        if isinstance(matches, Archetype):
            matches = [matches]
        
        for match in matches:
            self.external_neighbour_rules[(side, match)] = rules
    
    def __hash__(self):
        return id(self)
    
    def __eq__(self, other):
        return self == other


class Triangle(object):
    def __init__(self, archetype, x, y, angle, scale):
        self.archetype = archetype
        self.x = x
        self.y = y
        self.angle = angle
        self.scale = scale
        self.neighbours = [None] * len(self.archetype.happy_sides)
        self.subtriangles = []
    
    def get_points(self):
        points = []
        for a,m in self.archetype.polar_points:
            px = self.x + self.scale * m * math.cos(math.radians(self.angle + a))
            py = self.y + self.scale * m * math.sin(math.radians(self.angle + a))
            points.append((px, py))
        return points
    
    def get_centre(self):
        points = self.get_points()
        sx = 0.0
        sy = 0.0
        for px, py in points:
            sx += px
            sy += py
        
        return sx/len(points), sy/len(points)
    
    def within(self, x1, y1, x2, y2):
        #for px,py in self.get_points():
        #    if px < x1 or py < y1 or px > x2 or py > x2:
        #        return False
        #return True
        for px,py in self.get_points():
            if px >= x1 and py >= y1 and px <= x2 and py <= x2:
                return True
        return False
    
    def is_lonely(self):
        for i in range(len(self.neighbours)):
            if self.neighbours[i] is None and not self.archetype.happy_sides[i]:
                return True
        return False

    def add_neighbour(self, side, neighbour, neighbour_side):
        self.neighbours[side] = (neighbour, neighbour_side)
    
    def deflate(self):
        for shape, pt, angle, scale, loneliness_rule in self.archetype.subshapes:
            a, m = self.archetype.polar_points[pt]
            x = self.x + self.scale * m * math.cos(math.radians(self.angle + a))
            y = self.y + self.scale * m * math.sin(math.radians(self.angle + a))
            t = shape.generate(x, y, self.angle + angle, self.scale * scale)
            self.subtriangles.append(t)
        
        return self.subtriangles
    
    def find_neighbours(self):
        for subshape, subshape_side, neighbour_subshape, neighbour_side in self.archetype.internal_neighbour_rules:
            self.subtriangles[subshape].add_neighbour(subshape_side, self.subtriangles[neighbour_subshape], neighbour_side)
            self.subtriangles[neighbour_subshape].add_neighbour(neighbour_side, self.subtriangles[subshape], subshape_side)
        
        for side in range(len(self.neighbours)):
            n = self.neighbours[side]
            if n is None:
                continue
            neighbour, neighbour_side = n
            
            if (side, neighbour.archetype) not in self.archetype.external_neighbour_rules:
                print >> sys.stderr, 'No matching rules for %s side %d meets %s' % (self.archetype.name, side, neighbour.archetype.name)
                continue
            
            rules = self.archetype.external_neighbour_rules[(side, neighbour.archetype)]
            
            for from_tuple, to_tuple in rules.items():
                from_shape, from_side = from_tuple
                to_shape, to_side = to_tuple
                
                self.subtriangles[from_shape].add_neighbour(from_side, neighbour.subtriangles[to_shape], to_side)
    
    def render_to_svg(self):
        args = {}
        args['colour'] = '#%02x%02x%02x' % self.colour
        
        if self.is_lonely():
            extra = """opacity="0.25" """
        else:
            extra = ""
        s = """<g transform="translate(%f, %f) rotate(%f) scale(%f)" %s>%s</g>""" % (self.x, self.y, self.angle, self.scale, extra, self.archetype.render_to_svg(args))
        #~ for n in self.neighbours:
            #~ if n is not None:
                #~ neighbour, neighbour_side = n
                #~ cx, cy = self.get_centre()
                #~ nx, ny = neighbour.get_centre()
                #~ if cx > nx:
                    #~ colour = 'red'
                #~ else:
                    #~ colour = 'orange'
                #~ xadj = (cy-ny)/20.0
                #~ yadj = (nx-cx)/20.0
                #~ p1 = '%f,%f' % (cx+xadj, cy+yadj)
                #~ p2 = '%f,%f' % (nx+xadj, ny+yadj)
                #~ s += """<path stroke="%s" stroke-width="2" d="M%s L%s" />""" % (colour, p1, p2)
        return s
    
    def set_colour(self, colour):
        self.colour = colour
        for n, h in zip(self.neighbours, self.archetype.happy_sides):
            if n is None:
                continue
            neighbour, side = n
            if neighbour is not None and not h:
                neighbour.colour = colour
    
    def __repr__(self):
        return 'Triangle<%x>' % id(self)


def random_colour():
    x = random.randrange(-100, 100)
    if x < 0:
        return (255+x, 0, 0)
    else:
        return (255, x, x)


class Board(object):
    def __init__(self, x1, y1, x2, y2):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        
        self.triangles = set()
        self.old_triangles = set()
    
    def add(self, triangle):
        if not triangle.within(self.x1, self.y1, self.x2, self.y2):
            return
        
        self.triangles.add(triangle)
        #print triangle, triangle.neighbours
    
    def deflate(self):
        #print 'Deflating %d triangles' % len(self.triangles)
        
        new_triangles = []
        
        for t in self.triangles:
            new_triangles.extend(t.deflate())
            self.old_triangles.add(t)
        
        for t in self.triangles:
            t.find_neighbours()
        
        self.triangles = set()
        for t in new_triangles:
            self.add(t)
            t.set_colour(random_colour())
        
        for t in self.old_triangles:
            t.x -= 75.0
            t.scale *= 0.75
            t.x *= 0.75
            t.y *= 0.75
    
    def render_to_svg(self):
        parts = []
        for t in self.triangles:
            parts.append(t.render_to_svg())
        #for t in board.old_triangles:
        #    parts.append(t.render_to_svg())
        content = '\n'.join(parts)
        svg = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg width="100%%" height="100%%" viewBox="0 0 %f %f" xmlns="http://www.w3.org/2000/svg"> 
<g transform="translate(%f, %f)">
%s
</g>
</svg>
""" % (self.x2 - self.x1, self.y2 - self.y1, -self.x1, -self.y1, content)
        return svg


class P2Tiling(object):
    def __init__(self):
        phi = (1 + math.sqrt(5.0)) / 2.0
        
        len1 = 1.0
        len2 = len1/phi
        len3 = len1 - len2
        len4 = len2/phi
        len5 = len2 - len4
        thread_width = 0.06
        knot_gap = 0.01
        knot_adj = (thread_width + knot_gap) / 2.0
        circ_adj = 0.2
        circ_adj2 = 0.1
        shape1a = Archetype('semikite-cw', (False, True, True),
                (len2-knot_adj, 90.0), (circ_adj, -90.0), (2*knot_adj, -90.0), (circ_adj, 90.0), (len3-knot_adj, 108.0),
                (len4, 90.0), (circ_adj, -180.0), (circ_adj, 90.0), (len5, 108.0),
                (len4, 90.0), (circ_adj, -180.0), (circ_adj, 90.0), (len5, 0.0), (len3, 144.0))
        shape1b = Archetype('semikite-ccw', (False, True, True), *shape1a.reflect_segments())
        shape2a = Archetype('semidart-cw', (False, True, True),
                (len5-knot_adj, 90.0), (circ_adj2, -90.0), (2*knot_adj, -90.0), (circ_adj2, 90.0), (len4-knot_adj, 144.0),
                (len4, 90.0), (circ_adj2, -180.0), (circ_adj2, 90.0), (len5, 0.0), (len4, 144.0),
                (len4, 90.0), (circ_adj, -180.0), (circ_adj, 90.0), (len5, 72.0))
        shape2b = Archetype('semidart-ccw', (False, True, True), *shape2a.reflect_segments())
        
        shapes1 = [shape1a, shape1b]
        shapes2 = [shape2a, shape2b]
        
        def add_rules1(s):
            s.add_internal_neighbour_rule(0, 0, 1, 0)
            s.add_internal_neighbour_rule(1, 1, 2, 2)
            
            s.add_external_neighbour_rule(0, shapes1, {(0, 1): (0, 1), (2, 1): (2, 1)})
            s.add_external_neighbour_rule(1, shapes1, {(0, 2): (0, 2)})
            s.add_external_neighbour_rule(1, shapes2, {(0, 2): (1, 1)})
            s.add_external_neighbour_rule(2, shapes1, {(1, 2): (1, 2), (2, 0): (2, 0)})
            s.add_external_neighbour_rule(2, shapes2, {(1, 2): (0, 2), (2, 0): (1, 0)})

        def add_rules2(s):
            s.add_internal_neighbour_rule(0, 1, 1, 2)

            s.add_external_neighbour_rule(0, shapes2, {(0, 0): (0, 0)})
            s.add_external_neighbour_rule(1, shapes1, {(0, 2): (1, 2), (1, 0): (2, 0)})
            s.add_external_neighbour_rule(1, shapes2, {(0, 2): (0, 2), (1, 0): (1, 0)})
            s.add_external_neighbour_rule(2, shapes1, {(1, 1): (0, 2)})

        shape1a.add_decor("M%(p5)s L%(p9)s L%(p0)s", {}, """stroke="none" stroke-width="0.01" stroke-linecap="round" stroke-linejoin="round" fill="%(colour)s" """)
    #    shape1a.add_decor("M%(p0)s L%(p5)s", {}, """stroke="black" stroke-width="0.005" stroke-linecap="round" stroke-linejoin="round" """)
        shape1a.add_decor("M%(p4)s C%(p3)s %(p11)s %(p10)s", {}, """stroke="gold" stroke-width="%f" fill="none" """ % thread_width)
        shape1a.add_decor("M%(p1)s C%(p2)s %(p7)s %(p6)s", {}, """stroke="silver" stroke-width="%f" fill="none" """ % thread_width)
        shape1a.add_subshape(shape1a, 9, 252, len2/len1, {0: 1, 1: 2})
        shape1a.add_subshape(shape1b, 9, 252, len2/len1, {2: 2})
        shape1a.add_subshape(shape2a, 13, 216, len2/len1, {0: 1, 2: 0})
        add_rules1(shape1a)
        
        shape1b.add_decor("M%(p5)s L%(p9)s L%(p0)s", {}, """stroke="none" stroke-width="0.01" stroke-linecap="round" stroke-linejoin="round" fill="%(colour)s" """)
    #    shape1b.add_decor("M%(p0)s L%(p5)s", {}, """stroke="black" stroke-width="0.005" stroke-linecap="round" stroke-linejoin="round" """)
        shape1b.add_decor("M%(p1)s C%(p2)s %(p7)s %(p6)s", {'rads': '%f,%f' % (len4+knot_adj, len4+knot_adj)}, """stroke="silver" stroke-width="%f" fill="none" """ % thread_width)
        shape1b.add_decor("M%(p4)s C%(p3)s %(p11)s %(p10)s", {'rads': '%f,%f' % (len2+knot_adj, len2+knot_adj)}, """stroke="gold" stroke-width="%f" fill="none" """ % thread_width)
        shape1b.add_subshape(shape1b, 9, -252, len2/len1, {0: 1, 1: 2})
        shape1b.add_subshape(shape1a, 9, -252, len2/len1, {2: 2})
        shape1b.add_subshape(shape2b, 13, -216, len2/len1, {0: 1, 2: 0})
        add_rules1(shape1b)

        shape2a.add_decor("M%(p5)s L%(p10)s L%(p0)s", {}, """stroke="none" stroke-width="0.01" stroke-linecap="round" stroke-linejoin="round" fill="%(colour)s" """)
    #    shape2a.add_decor("M%(p0)s L%(p5)s", {}, """stroke="black" stroke-width="0.005" stroke-linecap="round" stroke-linejoin="round" """)
        shape2a.add_decor("M%(p1)s C%(p2)s %(p7)s %(p6)s", {}, """stroke="gold" stroke-width="%f" fill="none" """ % thread_width)
        shape2a.add_decor("M%(p4)s C%(p3)s %(p12)s %(p11)s", {}, """stroke="silver" stroke-width="%f" fill="none" """ % thread_width)
        shape2a.add_subshape(shape1b, 5, -180, len2/len1, {0: 0, 1: 2})
        shape2a.add_subshape(shape2a, 9, -216, len2/len1, {1: 0, 2: 1})
        add_rules2(shape2a)

        shape2b.add_decor("M%(p5)s L%(p10)s L%(p0)s", {}, """stroke="none" stroke-width="0.01" stroke-linecap="round" stroke-linejoin="round" fill="%(colour)s" """)
    #    shape2b.add_decor("M%(p0)s L%(p5)s", {}, """stroke="black" stroke-width="0.005" stroke-linecap="round" stroke-linejoin="round" """)
        shape2b.add_decor("M%(p4)s C%(p3)s %(p12)s %(p11)s", {}, """stroke="silver" stroke-width="%f" fill="none" """ % thread_width)
        shape2b.add_decor("M%(p1)s C%(p2)s %(p7)s %(p6)s", {}, """stroke="gold" stroke-width="%f" fill="none" """ % thread_width)
        shape2b.add_subshape(shape1a, 5, 180, len2/len1, {0: 0, 1: 2})
        shape2b.add_subshape(shape2b, 9, 216, len2/len1, {1: 0, 2: 1})
        add_rules2(shape2b)
        
        self.shape1a = shape1a
        self.shape1b = shape1b
        self.shape2a = shape2a
        self.shape2b = shape2b


    def create_circle(self, board, cx, cy, angle, scale):
        triangles = []
        
        for i in range(5):
            a = i*72.0
            t1 = self.shape1b.generate(cx, cy, angle + a, scale)
            board.add(t1)
            t2 = self.shape1a.generate(cx, cy, angle + a, scale)
            board.add(t2)
            triangles.append(t1)
            triangles.append(t2)
        
        for i in range(len(triangles)):
            next = (i + 1) % len(triangles)
            prev = (i - 1) % len(triangles)
            if i % 2 == 0:
                triangles[i].add_neighbour(0, triangles[next], 0)
                triangles[i].add_neighbour(2, triangles[prev], 2)
            else:
                triangles[i].add_neighbour(0, triangles[prev], 0)
                triangles[i].add_neighbour(2, triangles[next], 2)
        
        for t in triangles:
            t.set_colour(random_colour())
        
        return triangles


def main():
    board = Board(-410.0, -410.0, 410.0, 410.0)
    
    tiling = P2Tiling()
    
    #t1 = shape1a.generate(-400.0, 0.0, -18.0, 800.0)
    #board.add(t1)
    
    scale = 400.0
    tiling.create_circle(board, 0.0, 0.0, -90.0, scale)
    
    for i in range(5):
        scale = 400.0
        
        #a = i*72.0 - 90.0
        #x = scale * len2 * math.cos(math.radians(a + 36.0))
        #y = scale * len2 * math.sin(math.radians(a + 36.0))
        #t1 = shape2a.generate(x, y, a + 216.0, scale)
        #board.add(t1)
        #t2 = shape2b.generate(x, y, a + 216.0, scale)
        #board.add(t2)
    
    for i in range(5):
        f = open('penrose-robinson-%02d.svg' % i, 'wt')
        f.write(board.render_to_svg())
        f.close()
        board.deflate()


if __name__ == '__main__':
    main()
