import operator
from functools import reduce
from collections import namedtuple
from copy import deepcopy
#import numpy

# http://web.eecs.utk.edu/~jplank/plank/papers/CS-96-332.html
#   http://web.eecs.utk.edu/~jplank/plank/papers/CS-96-332.pdf
#   http://web.eecs.utk.edu/~jplank/plank/papers/CS-03-504.pdf
# https://www.cs.rutgers.edu/~venugopa/parallel_summer2012/ge.htmlg

# FD=C
# AD=E

class GF():

    def __init__(self, w=4, n=0, m=0):
        self.gflog, self.gfilog = self.setup_tables(w)
        self.NW = (1 << w) - 1
        self.n = n
        self.m = m
        self.F = self.setup_F()
        self.A = self.setup_A()

    @staticmethod
    def setup_tables(w):
        """
        >>> gflog, gfilog = GF.setup_tables(4)
        >>> gflog
        [None, 0, 1, 4, 2, 8, 5, 10, 3, 14, 9, 7, 6, 13, 11, 12]
        >>> gfilog
        [1, 2, 4, 8, 3, 6, 12, 11, 5, 10, 7, 14, 15, 13, 9, None]
        """
        prim_poly = {
            4: 0o23,  # Question: why are these Octals? they were octals in the original C code. But why?
            8: 0o435,
            16: 0o210013,
        }[w]

        x_to_w = 1 << w  # 4->16 8->255 16->65536

        gflog = [None]*x_to_w
        gfilog = [None]*x_to_w

        b = 1
        for log in range(x_to_w - 1):
            gflog[b] = log
            gfilog[log] = b
            b = b << 1
            if (b & x_to_w):
                b = b ^ prim_poly
        return (gflog, gfilog)

    def mult(self, *args):
        """
        >>> gf = GF(w=4)
        >>> gf.mult(3, 7)
        9
        >>> gf.mult(13, 10)
        11
        >>> gf.mult(3, 3)
        5
        """
        if not all(args):
            return 0
        #if (a == 0 or b == 0):
        #    return 0
        #sum_log = self.gflog[a] + self.gflog[b]
        sum_log = sum(map(self.gflog.__getitem__, args))
        if sum_log >= self.NW:
            sum_log -= self.NW
        return self.gfilog[sum_log]

    def div(self, a, b):
        """
        >>> gf = GF(w=4)
        >>> gf.div(13, 10)
        3
        
        The example below was corrected in the errata from 14 to 10
        >>> gf.div(3, 7)
        10
        """
        if a == 0:
            return 0
        if b == 0:
            return -1  # Can't devide by 0
        diff_log = self.gflog[a] - self.gflog[b]
        if diff_log < 0:
            diff_log += self.NW
        return self.gfilog[diff_log]
    
    def pow(self, i, p):
        """
        >>> gf = GF(w=4)
        >>> gf.pow(3,2)
        5
        >>> gf.pow(2,1)
        2
        >>> gf.pow(1,0)
        1
        """
        return self.mult(*(i,)*p) or 1

    def setup_F(self):
        """
        generate vandermonde matrix
        m = recovery points
        n = data points

        1^0 2^0 3^3   1 1 1
        1^1 2^1 3^1 = 1 2 3
        1^2 2^2 3^2   1 4 5

        >>> gf = GF(w=4, n=3, m=3)
        >>> gf.F
        [[1, 1, 1], [1, 2, 3], [1, 4, 5]]

        This test is a guess based on my current understanding
        [1, 8, 15, 12] seem pauseable
        >>> gf = GF(w=4, n=4, m=4)
        >>> gf.F
        [[1, 1, 1, 1], [1, 2, 3, 4], [1, 4, 5, 3], [1, 8, 15, 12]]
        """
        return [
            [self.pow(_n,_m) for _n in range(1,self.n+1)]
            for _m in range(0, self.m)
        ]
    def setup_A(self):
        """
        A = I(dentify matrix) on_top_of F(vandermod matrix)
        >>> gf = GF(w=4, n=3, m=2)
        >>> gf.A
        [[1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 1, 1], [1, 2, 3]]
        """
        return [  # Create the identity matrix
            [1 if n1 == n2 else 0 for n1 in range(self.n)]
            for n2 in range(self.n)
        ] + self.F

    def dot_product(self, matrixA, matrixB):
        """
        """
        assert len(matrixB) == self.n
        #assert len(matrixA) == self.n  #???
        #assert len(matrixA[0]) == self.m  #??
        return [
            reduce(operator.xor, #"+".join(   # used this for testing visually
                (
                    self.mult(matrixA[_n][_m], matrixB[_m])  #f'{matrixA[_n][_m]}x{matrixB[_m]}'
                    for _m in range(0, self.m)
                )
            )
            for _n in range(0, self.n)
        ]

    def C(self, D):
        """
        C(hecksum)
        >>> gf = GF(w=4, n=3, m=3)
        >>> gf.C(D=[3, 13, 9])
        [7, 2, 9]
        """
        return self.dot_product(self.F, D)

    def E(self, D):
        """
        E = D(ata) on_top_of C(ecksum)
        >>> gf = GF(w=4, n=3, m=3)
        >>> gf.E(D=[3, 13, 9])
        [3, 13, 9, 7, 2, 9]
        >>> gf.E(D=[3, 1, 9])
        [3, 1, 9, 11, 9, 12]
        """
        return D + self.C(D)
    
    def invert(self, A):
        """
        >>> gf = GF(w=4)
        >>> gf.invert([[1, 0, 0], [1, 1, 1], [1, 2, 3]])
        [[1, 0, 0], [2, 3, 1], [3, 2, 1]]
        """
        return [[1, 0, 0], [2, 3, 1], [3, 2, 1]]
        raise NotImplemented()

    def recover(self, E):
        """
        >>> gf = GF(w=4, n=3, m=3)
        >>> E = [3, None, None, 11, 9, None]
        >>> gf.recover(E)
        [3, 1, 9, 11, 9, 12]
        """
        A_ = self.invert([
            self.A[i]
            for i, e in enumerate(E)
            if e
        ])
        DC_ = [e for e in E if e]
        D = self.dot_product(A_, DC_)
        return self.E(D)
