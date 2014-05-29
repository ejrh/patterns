from unittest import TestCase

from penrose import QuadTree

class Point(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def __repr__(self):
        return 'Point(%s, %s)' % (repr(self.x), repr(self.y))

class QuadTreeTests(TestCase):
    def testEmpty(self):
        qt = QuadTree(0, 0, 100, 100)
        self.assertEqual(qt.find_all(), [])

    def testSingleInsertion(self):
        qt = QuadTree(0, 0, 100, 100)
        pt = Point(50, 50)
        qt.add(pt)
        self.assertEqual(qt.find_all(), [pt])
        self.assertEqual(qt.find(40, 40, 60, 60), [pt])
        self.assertEqual(qt.find(10, 10, 30, 30), [])

    def testDuplicate(self):
        qt = QuadTree(0, 0, 100, 100)
        pt1 = Point(50, 50)
        pt2 = Point(50, 50)
        qt.add(pt1)
        qt.add(pt2)
        self.assertEqual(qt.find_all(), [pt1, pt2])
        self.assertEqual(qt.find(40, 40, 60, 60), [pt1, pt2])
