import math
import random
import time
import heapq


def line_intersection(p0_x, p0_y, p1_x, p1_y, p2_x, p2_y, p3_x, p3_y):
    """"Returns 1 if the lines intersect, otherwise 0. In addition, if the lines 
    intersect the intersection point may be stored in the floats i_x and i_y.
    Translated from C, original at http://stackoverflow.com/a/14795484/63991"""
    s10_x = p1_x - p0_x
    s10_y = p1_y - p0_y
    s32_x = p3_x - p2_x
    s32_y = p3_y - p2_y

    denom = s10_x * s32_y - s32_x * s10_y
    if denom == 0.0:
        return None # Collinear
    denomPositive = denom > 0

    s02_x = p0_x - p2_x
    s02_y = p0_y - p2_y
    s_numer = s10_x * s02_y - s10_y * s02_x
    if (s_numer < 0) == denomPositive:
        return None # No collision

    t_numer = s32_x * s02_y - s32_y * s02_x
    if (t_numer < 0) == denomPositive:
        return None # No collision

    if (s_numer > denom) == denomPositive or (t_numer > denom) == denomPositive:
        return 0 # No collision
    
    # Collision detected
    t = t_numer / denom
    i_x = p0_x + (t * s10_x)
    i_y = p0_y + (t * s10_y)

    return i_x, i_y


class QuadTree(object):
    SPLIT_THRESHOLD = 8
    
    def __init__(self, x1, y1, x2, y2):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.mpx = (x1 + x2) / 2
        self.mpy = (y1 + y2) / 2
        self.points = []
        self.quads = [None,None,None,None]
    
    def add(self, point):
        if len(self.points) < QuadTree.SPLIT_THRESHOLD:
            self.points.append(point)
            return
        
        quad = self.get_quad(point)
        quad.add(point)
    
    def get_quad(self, point):
        if point.y < self.mpy:
            if point.x < self.mpx:
                quad_pos = 0
            else:
                quad_pos = 1
        else:
            if point.x < self.mpx:
                quad_pos = 2
            else:
                quad_pos = 3
        
        if self.quads[quad_pos] is None:
            bounds = self.get_quad_bounds(quad_pos)
            self.quads[quad_pos] = QuadTree(*bounds)
        
        return self.quads[quad_pos]
    
    def get_quad_bounds(self, pos):
        if pos == 0:
            return self.x1, self.y1, self.mpx, self.mpy
        elif pos == 1:
            return self.mpx, self.y1, self.x2, self.mpy
        elif pos == 2:
            return self.x1, self.mpy, self.mpx, self.y2
        else:
            return self.mpx, self.mpy, self.x2, self.y2
    
    def find(self, x1, y1, x2, y2):
        if x1 > self.x2 or y1 > self.y2 or x2 < self.x1 or y2 < self.y1:
            return []
        
        points = [p for p in self.points if p.x >= x1 and p.y >= y1 and p.x <= x2 and p.y <= y2]
        
        for quad in self.quads:
            if quad is not None:
                points.extend(quad.find(x1, y1, x2, y2))
        
        return points
    
    def find_all(self):
        return self.find(self.x1, self.y1, self.x2, self.y2)


class TileError(Exception):
    pass


class EdgeType(object):
    def __init__(self, name, length, *matches):
        self.name = name
        self.length = length
        self.matches = set(matches)
        for m in self.matches:
            m.matches.add(self)
        self.colour = 'black'
    
    def set_colour(self, colour):
        self.colour = colour
        return self
    
    def __repr__(self):
        return "EdgeType(%s, %s, %s)" % (repr(self.name), repr(self.length), repr([m.name for m in self.matches]))


class Shape(object):
    def __init__(self, name, *types_and_angles):
        self.name = name
        self.edges = []
        types = types_and_angles[0::2]
        angles = types_and_angles[1::2]
        for t, a in zip(types, angles):
            self.edges.append((t, a))


class Anchor(object):
    def __init__(self, x, y, angle, edge_type):
        self.x = x
        self.y = y
        self.angle = angle
        self.edge_type = edge_type
        self.piece = None
        self.twin = None
    
    def get_twin(self):
        if self.twin is not None:
            return self.twin
        
        x2 = self.x + self.edge_type.length * math.cos(math.radians(self.angle))
        y2 = self.y + self.edge_type.length * math.sin(math.radians(self.angle))
        angle2 = self.angle + 180.0
        if angle2 >= 360.0:
            angle2 -= 360.0
        type2 = list(self.edge_type.matches)[0]
        self.twin = Anchor(x2, y2, angle2, type2)
        self.twin.twin = self
        
        return self.twin
    
    def __repr__(self):
        return "Anchor(%f, %f, %f, '%s')" % (self.x, self.y, self.angle, self.edge_type.name)


class Piece(object):
    def __init__(self, shape):
        self.shape = shape
        self.anchors = []

i = 0

class Board(object):
    def __init__(self):
        self.anchors = QuadTree(0.0, 0.0, 100.0, 100.0)
        self.anchor_queue = []
        self.pieces = []
    
    def add_anchor(self, anchor):
        def get_priority(p):
            #return (50 - p.x) * (50 - p.x) + (50 - p.y) * (50 - p.y)
            global i
            i += 1
            return i
        
        self.anchors.add(anchor)
        priority = get_priority(anchor)
        heapq.heappush(self.anchor_queue, (priority, anchor))
        
        twin = anchor.get_twin()
        self.anchors.add(twin)
        priority = get_priority(twin)
        heapq.heappush(self.anchor_queue, (priority, twin))
        
        print anchor
    
    def get_next_anchor(self):
        #print '\n'.join(str(x) for x in self.anchor_queue[:10])
        if len(self.anchor_queue) == 0:
            return None
        anchor = heapq.heappop(self.anchor_queue)[1]
        #print 'picked', anchor
        return anchor
    
    def find_anchor(self, x, y, angle):
        candidates = self.anchors.find(x - 1.0, y - 1.0, x + 1.0, y + 1.0)
        for c in candidates:
            if angle - 10 < c.angle < angle + 10:
                return c
        return None
    
    def check_collisions(self, x, y, angle, length):
        candidates = self.anchors.find(x - length, y - length, x + length, y + length)
        x2 = x + length * math.cos(math.radians(angle)) * 0.95
        y2 = y + length * math.sin(math.radians(angle)) * 0.95
        x = x + length * math.cos(math.radians(angle)) * 0.05
        y = y + length * math.sin(math.radians(angle)) * 0.05
        for c in candidates:
            adiff = abs(angle - c.angle)
            if adiff < 10.0 or adiff >= 350.0:
                continue
            cx2 = c.x + c.edge_type.length * math.cos(math.radians(c.angle))
            cy2 = c.y + c.edge_type.length * math.sin(math.radians(c.angle))
            if line_intersection(x, y, x2, y2, c.x, c.y, cx2, cy2):
                #print 'collision', x, y, x2, y2, c.x, c.y, cx2, cy2
                return True
        return False
    
    def place_piece(self, piece, anchor):
        if anchor.piece is not None:
            raise TileError('Cannot place a piece on an anchor that already has one')
        
        edges = piece.shape.edges
        
        start_pos = None
        for i in range(len(edges)):
            if edges[i][1] == anchor.edge_type:
                start_pos = i + 1
                end_pos = start_pos + len(edges) - 1
                break
        
        if start_pos is None:
            raise TileError('Cannot place a %s piece on an anchor of type %s' % (piece.shape.name, anchor.edge_type.name))
        
        anchors = [anchor]
        new_anchors = []
        x = anchor.x
        y = anchor.y
        angle = anchor.angle
        prev_edge_type = anchor.edge_type
        for i in range(start_pos, end_pos):
            pos = i % len(edges)
            edge_angle, edge_type = edges[pos]
            
            print 'prev', prev_edge_type, 'edge_angle', edge_angle, 'edge_type', edge_type
            # First move along the existing edge
            x += prev_edge_type.length * math.cos(math.radians(angle))
            y += prev_edge_type.length * math.sin(math.radians(angle))
            # Then turn the angle
            angle += edge_angle
            if angle >= 360.0:
                angle -= 360.0
            
            # Check for collisions
            if self.check_collisions(x, y, angle, edge_type.length):
                raise TileError('Cannot place piece that collides with another')
            
            # Find or create the new anchor
            new_anchor = self.find_anchor(x, y, angle)
            if new_anchor is None:
                new_anchor = Anchor(x, y, angle, edge_type)
                new_anchors.append(new_anchor)
            elif new_anchor.piece is not None:
                raise TileError('Cannot reuse anchor that already has a piece')
            if new_anchor.edge_type != edge_type:
                raise TileError('Cannot place piece against an incompatible anchor')
            anchors.append(new_anchor)
            
            prev_edge_type = edge_type
        
        for a in anchors:
            a.piece = piece
        for a in new_anchors:
            self.add_anchor(a)
        piece.anchors = anchors
        self.pieces.append(piece)
        
        return anchors


def board_to_svg(board):
    content = ''
    for p in board.anchors.find_all():
        if p.piece is None:
            content = content + """<g transform="translate(%f, %f) rotate(%f)">
<circle fill="blue" cx="0" cy="0" r="%f" />
<line stroke="%s" stroke-width="0.15" x1="0" y1="0.25" x2="%f" y2="0.25" />
<line stroke="blue" stroke-width="0.15" x1="%f" y1="%f" x2="%f" y2="0.25" />
</g>\n""" % (p.x, p.y, p.angle, 0.25, p.edge_type.colour, p.edge_type.length, p.edge_type.length/2, p.edge_type.length/4, p.edge_type.length/2)
        else:
            content = content + """<g transform="translate(%f, %f) rotate(%f)">
<line stroke="silver" stroke-width="0.1" x1="0" y1="0.0" x2="%f" y2="0.0" />
</g>\n""" % (p.x, p.y, p.angle, p.edge_type.length)

    for p in board.pieces:
        avgx = sum(p.x for p in p.anchors) / len(p.anchors)
        avgy = sum(p.y for p in p.anchors) / len(p.anchors)
        content = content + """<g transform="translate(%f, %f) rotate(%f)">
<circle fill="blue" cx="0" cy="0" r="%f" />
</g>\n""" % (avgx, avgy, 0.0, 0.5)
    
    svg = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg width="100%%" height="100%%" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
%s</svg>
""" % content
    return svg
    

def add_random_piece(board, shapes):
    while True:
        anchor = board.get_next_anchor()
        if anchor is None:
            return
        if anchor.piece is None:
            break
    
    random.shuffle(shapes)
    for shape in shapes:
        piece = Piece(shape)
        try:
            board.place_piece(piece, anchor)
            return
        except TileError:
            pass
    print 'failed to place!'
    #for i in range(100):
    #    shape = random.choice(shapes)
    #    piece = Piece(shape)
    #    try:
    #        board.place_piece(piece, anchor)
    #        break
    #    except TileError:
    #        pass


def main():
    s = int(time.time())
    s = 1399633315
    print 'seed', s
    random.seed(s)
    
    # Thin and thick rhombi
    #edge1 = EdgeType('spike-blue', 5.0).set_colour('blue')
    #edge2 = EdgeType('blue-dip', 5.0, edge1).set_colour('darkblue')
    #edge3 = EdgeType('spike-red', 5.0).set_colour('red')
    #edge4 = EdgeType('red-dip', 5.0, edge3).set_colour('darkred')
    #shape1 = Shape('thin-rhomb', 144.0, edge1, 36.0, edge2, 144.0, edge3, 36.0, edge4)
    #shape2 = Shape('thick-rhomb', 108.0, edge2, 72.0, edge4, 108.0, edge3, 72.0, edge1)
    
    # Kite and dart
    phi = (1 + math.sqrt(5.0)) / 2.0
    edge1 = EdgeType('green-right', 10.0).set_colour('green')
    edge2 = EdgeType('red-left', 10.0/phi).set_colour('red')
    edge3 = EdgeType('red-right', 10.0/phi, edge2).set_colour('darkred')
    edge4 = EdgeType('green-left', 10.0, edge1).set_colour('darkgreen')
    shape1 = Shape('kite', 108.0, edge1, 108.0, edge2, 36.0, edge3, 108.0, edge4)
    shape2 = Shape('dart', -36.0, edge3, 144.0, edge1, 108.0, edge4, 144.0, edge2)
    
    board = Board()
    
    seed = Anchor(50.0, 50.0, 0.0, edge1)
    board.add_anchor(seed)
    
    for i in range(100):
        add_random_piece(board, [shape1, shape2])
    
    f = open('penrose.svg', 'wt')
    f.write(board_to_svg(board))
    f.close()


if __name__ == '__main__':
    main()
