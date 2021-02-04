import operator
from functools import reduce
from collections import namedtuple
#import numpy

# http://web.eecs.utk.edu/~jplank/plank/papers/CS-96-332.pdf
# http://web.eecs.utk.edu/~jplank/plank/papers/CS-03-504.pdf


# FD=C
# AD=E

class GF():

    def __init__(self, w):
        """
        >>> gf = GF(4)
        >>> gf.gflog
        [None, 0, 1, 4, 2, 8, 5, 10, 3, 14, 9, 7, 6, 13, 11, 12]
        >>> gf.gfilog
        [1, 2, 4, 8, 3, 6, 12, 11, 5, 10, 7, 14, 15, 13, 9, None]
        """
        prim_poly = {
            4: 0o23,  # Question: why are these Octals? they were octals in the original C code. But why?
            8: 0o435,
            16: 0o210013,
        }[w]

        x_to_w = 1 << w  # 4->16 8->255 16->65536
        self.NW = x_to_w - 1

        self.gflog = [None]*x_to_w
        self.gfilog = [None]*x_to_w

        b = 1
        for log in range(x_to_w - 1):
            self.gflog[b] = log
            self.gfilog[log] = b
            b = b << 1
            if (b & x_to_w):
                b = b ^ prim_poly

    def mult(self, *args):
        """
        >>> gf = GF(4)
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
        >>> gf = GF(4)
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
        >>> gf = GF(4)
        >>> gf.pow(3,2)
        5
        >>> gf.pow(2,1)
        2
        >>> gf.pow(1,0)
        1
        """
        return self.mult(*(i,)*p) or 1

    def F(self, m, n):
        """
        vandermonde matrix
        m = recovery points
        n = data points

        1^0 2^0 3^3   1 1 1
        1^1 2^1 3^1 = 1 2 3
        1^2 2^2 3^2   1 4 5

        >>> gf = GF(4)
        >>> gf.F(3, 3)
        [[1, 1, 1], [1, 2, 3], [1, 4, 5]]

        This test is a guess based on my current understanding
        [1, 8, 15, 12] seem pauseable
        >>> gf.F(4, 4)
        [[1, 1, 1, 1], [1, 2, 3, 4], [1, 4, 5, 3], [1, 8, 15, 12]]
        """
        return [
            [self.pow(_n,_m) for _n in range(1,n+1)]
            for _m in range(0, m)
        ]

    def C(self, D, m):
        """
        >>> gf = GF(4)
        >>> gf.C(D=[3, 13, 9], m=3)
        [7, 2, 9]
        """
        n = len(D)
        F = self.F(m, n)
        return [
            #"+".join([   # used this for testing visually
            #f'{F[_n][_m]}x{D[_m]}'
            reduce(
                operator.xor, 
                (
                    self.mult(F[_n][_m], D[_m])
                    for _m in range(0, m)
                )
            )
            for _n in range(0, n)
        ]