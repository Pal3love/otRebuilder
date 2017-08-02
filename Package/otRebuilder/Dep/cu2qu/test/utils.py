from __future__ import print_function, division, absolute_import
from cu2qu.test import CUBIC_GLYPHS
try:
    from ufoLib.pointPen import PointToSegmentPen, SegmentToPointPen
except ImportError:
    from robofab.pens.adapterPens import PointToSegmentPen, SegmentToPointPen
import unittest


class BaseDummyPen(object):
    """Base class for pens that record the commands they are called with."""

    def __init__(self, *args, **kwargs):
        self.commands = []

    def __str__(self):
        """Return the pen commands as a string of python code."""
        return _repr_pen_commands(self.commands)

    def addComponent(self, glyphName, transformation, **kwargs):
        self.commands.append(('addComponent', (glyphName, transformation), kwargs))


class DummyPen(BaseDummyPen):
    """A SegmentPen that records the commands it's called with."""

    def moveTo(self, pt):
        self.commands.append(('moveTo', (pt,), {}))

    def lineTo(self, pt):
        self.commands.append(('lineTo', (pt,), {}))

    def curveTo(self, *points):
        self.commands.append(('curveTo', points, {}))

    def qCurveTo(self, *points):
        self.commands.append(('qCurveTo', points, {}))

    def closePath(self):
        self.commands.append(('closePath', tuple(), {}))

    def endPath(self):
        self.commands.append(('endPath', tuple(), {}))


class DummyPointPen(BaseDummyPen):
    """A PointPen that records the commands it's called with."""

    def beginPath(self, **kwargs):
        self.commands.append(('beginPath', tuple(), kwargs))

    def endPath(self):
        self.commands.append(('endPath', tuple(), {}))

    def addPoint(self, pt, segmentType=None, smooth=False, name=None, **kwargs):
        kwargs['segmentType'] = segmentType
        kwargs['smooth'] = smooth
        kwargs['name'] = name
        self.commands.append(('addPoint', (pt,), kwargs))


class DummyGlyph(object):
    """Provides a minimal interface for storing a glyph's outline data in a
    SegmentPen-oriented way. The glyph's outline consists in the list of
    SegmentPen commands required to draw it.
    """

    # the SegmentPen class used to draw on this glyph type
    DrawingPen = DummyPen

    def __init__(self, glyph=None):
        """If another glyph (i.e. any object having a 'draw' method) is given,
        its outline data is copied to self.
        """
        self._pen = self.DrawingPen()
        self.outline = self._pen.commands
        if glyph:
            self.appendGlyph(glyph)

    def appendGlyph(self, glyph):
        """Copy another glyph's outline onto self."""
        glyph.draw(self._pen)

    def getPen(self):
        """Return the SegmentPen that can 'draw' on this glyph."""
        return self._pen

    def getPointPen(self):
        """Return a PointPen adapter that can 'draw' on this glyph."""
        return PointToSegmentPen(self._pen)

    def draw(self, pen):
        """Use another SegmentPen to replay the glyph's outline commands."""
        if self.outline:
            for cmd, args, kwargs in self.outline:
                getattr(pen, cmd)(*args, **kwargs)

    def drawPoints(self, pointPen):
        """Use another PointPen to replay the glyph's outline commands,
        indirectly through an adapter.
        """
        pen = SegmentToPointPen(pointPen)
        self.draw(pen)

    def __eq__(self, other):
        """Return True if 'other' glyph's outline is the same as self."""
        if hasattr(other, 'outline'):
            return self.outline == other.outline
        elif hasattr(other, 'draw'):
            return self.outline == self.__class__(other).outline
        return NotImplemented

    def __ne__(self, other):
        """Return True if 'other' glyph's outline is different from self."""
        return not (self == other)

    def __str__(self):
        """Return commands making up the glyph's outline as a string."""
        return str(self._pen)


class DummyPointGlyph(DummyGlyph):
    """Provides a minimal interface for storing a glyph's outline data in a
    PointPen-oriented way. The glyph's outline consists in the list of
    PointPen commands required to draw it.
    """

    # the PointPen class used to draw on this glyph type
    DrawingPen = DummyPointPen

    def appendGlyph(self, glyph):
        """Copy another glyph's outline onto self."""
        glyph.drawPoints(self._pen)

    def getPen(self):
        """Return a SegmentPen adapter that can 'draw' on this glyph."""
        return SegmentToPointPen(self._pen)

    def getPointPen(self):
        """Return the PointPen that can 'draw' on this glyph."""
        return self._pen

    def draw(self, pen):
        """Use another SegmentPen to replay the glyph's outline commands,
        indirectly through an adapter.
        """
        pointPen = PointToSegmentPen(pen)
        self.drawPoints(pointPen)

    def drawPoints(self, pointPen):
        """Use another PointPen to replay the glyph's outline commands."""
        if self.outline:
            for cmd, args, kwargs in self.outline:
                getattr(pointPen, cmd)(*args, **kwargs)


def _repr_pen_commands(commands):
    """
    >>> print(_repr_pen_commands([
    ...     ('moveTo', tuple(), {}),
    ...     ('lineTo', ((1.0, 0.1),), {}),
    ...     ('curveTo', ((1.0, 0.1), (2.0, 0.2), (3.0, 0.3)), {})
    ... ]))
    pen.moveTo()
    pen.lineTo((1, 0.1))
    pen.curveTo((1, 0.1), (2, 0.2), (3, 0.3))

    >>> print(_repr_pen_commands([
    ...     ('beginPath', tuple(), {}),
    ...     ('addPoint', ((1.0, 0.1),),
    ...      {"segmentType":"line", "smooth":True, "name":"test", "z":1}),
    ... ]))
    pen.beginPath()
    pen.addPoint((1, 0.1), name='test', segmentType='line', smooth=True, z=1)

    >>> print(_repr_pen_commands([
    ...    ('addComponent', ('A', (1, 0, 0, 1, 0, 0)), {})
    ... ]))
    pen.addComponent('A', (1, 0, 0, 1, 0, 0))
    """
    s = []
    for cmd, args, kwargs in commands:
        if args:
            if isinstance(args[0], tuple):
                # cast float to int if there're no digits after decimal point
                args = [tuple((int(v) if int(v) == v else v) for v in pt)
                        for pt in args]
            args = ", ".join(repr(a) for a in args)
        if kwargs:
            kwargs = ", ".join("%s=%r" % (k, v)
                               for k, v in sorted(kwargs.items()))
        if args and kwargs:
            s.append("pen.%s(%s, %s)" % (cmd, args, kwargs))
        elif args:
            s.append("pen.%s(%s)" % (cmd, args))
        elif kwargs:
            s.append("pen.%s(%s)" % (cmd, kwargs))
        else:
            s.append("pen.%s()" % cmd)
    return "\n".join(s)


class TestDummyGlyph(unittest.TestCase):

    def test_equal(self):
        # verify that the copy and the copy of the copy are equal to
        # the source glyph's outline, as well as to each other
        source = CUBIC_GLYPHS['a']
        copy = DummyGlyph(source)
        copy2 = DummyGlyph(copy)
        self.assertEqual(source, copy)
        self.assertEqual(source, copy2)
        self.assertEqual(copy, copy2)
        # assert equality doesn't hold any more after modification
        copy.outline.pop()
        self.assertNotEqual(source, copy)
        self.assertNotEqual(copy, copy2)


class TestDummyPointGlyph(unittest.TestCase):

    def test_equal(self):
        # same as above but using the PointPen protocol
        source = CUBIC_GLYPHS['a']
        copy = DummyPointGlyph(source)
        copy2 = DummyPointGlyph(copy)
        self.assertEqual(source, copy)
        self.assertEqual(source, copy2)
        self.assertEqual(copy, copy2)
        copy.outline.pop()
        self.assertNotEqual(source, copy)
        self.assertNotEqual(copy, copy2)


if __name__ == "__main__":
    unittest.main()
