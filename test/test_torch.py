import sys
import math
import random
import torch
import tempfile
import unittest
from itertools import product
from common import TestCase, iter_indices

SIZE = 100

class TestTorch(TestCase):

    def test_dot(self):
        types = {
            'torch.DoubleTensor': 1e-8,
            'torch.FloatTensor': 1e-4,
        }
        for tname, prec in types.items():
            v1 = torch.randn(100).type(tname)
            v2 = torch.randn(100).type(tname)
            res1 = torch.dot(v1,v2)
            res2 = 0
            for i, j in zip(v1, v2):
                res2 += i * j
            self.assertEqual(res1, res2)

    def _testMath(self, torchfn, mathfn):
        size = (10, 5)
        # contiguous
        m1 = torch.randn(*size)
        res1 = torchfn(m1[4])
        res2 = res1.clone().zero_()
        for i, v in enumerate(m1[4]):
            res2[i] = mathfn(v)
        self.assertEqual(res1, res2)

        # non-contiguous
        m1 = torch.randn(*size)
        res1 = torchfn(m1[:,4])
        res2 = res1.clone().zero_()
        for i, v in enumerate(m1[:,4]):
            res2[i] = mathfn(v)
        self.assertEqual(res1, res2)

    def _testMathByName(self, function_name):
        torchfn = getattr(torch, function_name)
        mathfn = getattr(math, function_name)
        self._testMath(torchfn, mathfn)

    def test_sin(self):
        self._testMathByName('sin')

    def test_sinh(self):
        self._testMathByName('sinh')

    def test_asin(self):
        self._testMath(torch.asin, lambda x: math.asin(x) if abs(x) <= 1 else float('nan'))

    def test_cos(self):
        self._testMathByName('cos')

    def test_cosh(self):
        self._testMathByName('cosh')

    def test_acos(self):
        self._testMath(torch.acos, lambda x: math.acos(x) if abs(x) <= 1 else float('nan'))

    def test_tan(self):
        self._testMathByName('tan')

    def test_tanh(self):
        self._testMathByName('tanh')

    def test_atan(self):
        self._testMathByName('atan')

    def test_log(self):
        self._testMath(torch.log, lambda x: math.log(x) if x > 0 else float('nan'))

    def test_sqrt(self):
        self._testMath(torch.sqrt, lambda x: math.sqrt(x) if x > 0 else float('nan'))

    def test_exp(self):
        self._testMathByName('exp')

    def test_floor(self):
        self._testMathByName('floor')

    def test_ceil(self):
        self._testMathByName('ceil')

    def test_rsqrt(self):
        self._testMath(torch.rsqrt, lambda x: 1 / math.sqrt(x) if x > 0 else float('nan'))

    def test_sigmoid(self):
        # TODO: why not simulate math.sigmoid like with rsqrt?
        inputValues = [-1000,-1,0,0.5,1,2,1000]
        expectedOutput = [0.0000, 0.2689, 0.5, 0.6225, 0.7311, 0.8808, 1.000]
        precision_4dps = 0.0002

        def checkType(tensor):
            self.assertEqual(tensor(inputValues).sigmoid(), tensor(expectedOutput), precision_4dps)

        checkType(torch.FloatTensor)
        checkType(torch.DoubleTensor)

    def test_frac(self):
        self._testMath(torch.frac, lambda x: math.fmod(x, 1))

    def test_trunc(self):
        self._testMath(torch.trunc, lambda x: x - math.fmod(x, 1))

    def test_round(self):
        self._testMath(torch.round, round)

    def _testSelection(self, torchfn, mathfn):
        # contiguous
        m1 = torch.randn(100,100)
        res1 = torchfn(m1)
        res2 = m1[0,0]
        for i, j in iter_indices(m1):
            res2 = mathfn(res2, m1[i,j])
        self.assertEqual(res1, res2)

        # non-contiguous
        m1 = torch.randn(10,10,10)
        m2 = m1[:,4]
        res1 = torchfn(m2)
        res2 = m2[0,0]
        for i, j in iter_indices(m2):
            res2 = mathfn(res2, m2[i][j])
        self.assertEqual(res1, res2)

        # with indices
        m1 = torch.randn(100,100)
        res1val, res1ind = torchfn(m1, 1)
        res2val = m1[:,(0,)].clone()
        res2ind = res1ind.clone().fill_(0)
        for i, j in iter_indices(m1):
            if mathfn(res2val[i,0], m1[i,j]) != res2val[i,0]:
                res2val[i,0] = m1[i,j]
                res2ind[i,0] = j

        maxerr = 0
        for i in range(res1val.size(0)):
            maxerr = max(maxerr, abs(res1val[i][0] - res2val[i][0]))
            self.assertEqual(res1ind[i][0], res2ind[i][0])
        self.assertLessEqual(abs(maxerr), 1e-5)

        # NaNs
        for index in (0, 4, 99):
            m1 = torch.randn(100)
            m1[index] = float('nan')
            res1val, res1ind = torch.max(m1, 0)
            self.assertNotEqual(res1val[0], res1val[0])
            self.assertEqual(res1ind[0], index)
            res1val = torchfn(m1)
            self.assertNotEqual(res1val, res1val)

    def test_max(self):
        self._testSelection(torch.max, max)

    def test_min(self):
        self._testSelection(torch.min, min)

    def _testCSelection(self, torchfn, mathfn):
        # Two tensors
        size = (100, 100)
        a = torch.rand(*size)
        b = torch.rand(*size)
        c = torchfn(a, b)
        expected_c = torch.zeros(*size)
        expected_c.map2_(a, b, lambda _, a, b: mathfn(a, b))
        self.assertEqual(expected_c, c, 0)

        # Tensor and scalar
        v = random.random()
        c = torchfn(a, v)
        expected_c.map_(a, lambda _, a: mathfn(a, v))
        self.assertEqual(expected_c, c, 0)

    def test_cmax(self):
        self._testCSelection(torch.cmax, max)

    def test_cmin(self):
        self._testCSelection(torch.cmin, min)

    def test_lerp(self):
        def TH_lerp(a, b, weight):
            return a + weight * (b-a);

        size = (100, 100)
        a = torch.rand(*size)
        b = torch.rand(*size)
        w = random.random()
        result = torch.lerp(a, b, w)
        expected = a.clone()
        expected.map2_(a, b, lambda _, a, b: TH_lerp(a, b, w))
        self.assertEqual(result, expected)

    def test_all_any(self):
        def test(size):
            x = torch.ones(*size).byte()
            self.assertTrue(x.all())
            self.assertTrue(x.any())

            x[3] = 0
            self.assertFalse(x.all())
            self.assertTrue(x.any())

            x.zero_()
            self.assertFalse(x.all())
            self.assertFalse(x.any())

            x.fill_(2)
            self.assertTrue(x.all())
            self.assertTrue(x.any())

        test((10,))
        test((5, 5))

    def test_mv(self):
        m1 = torch.randn(100,100)
        v1 = torch.randn(100)

        res1 = torch.mv(m1,v1)
        res2 = res1.clone().zero_()
        for i, j in iter_indices(m1):
            res2[i] += m1[i][j] * v1[j]

        self.assertEqual(res1, res2)

    def test_add(self):
        # [res] torch.add([res,] tensor1, tensor2)
        m1 = torch.randn(100,100)
        v1 = torch.randn(100)

        # contiguous
        res1 = torch.add(m1[4], v1)
        res2 = res1.clone().zero_()
        for i in range(m1.size(1)):
            res2[i] = m1[4,i] + v1[i]
        self.assertEqual(res1, res2)

        m1 = torch.randn(100,100)
        v1 = torch.randn(100)

        # non-contiguous
        res1 = torch.add(m1[:,4],v1)
        res2 = res1.clone().zero_()
        for i in range(m1.size(0)):
            res2[i] = m1[i,4] + v1[i]
        self.assertEqual(res1, res2)

        # [res] torch.add([res,] tensor, value)
        m1 = torch.randn(10,10)

        # contiguous
        res1 = m1.clone()
        res1[3].add_(2)
        res2 = m1.clone()
        for i in range(m1.size(1)):
            res2[3,i] = res2[3,i] + 2
        self.assertEqual(res1, res2)

        # non-contiguous
        m1 = torch.randn(10,10)
        res1 = m1.clone()
        res1[:,3].add_(2)
        res2 = m1.clone()
        for i in range(m1.size(0)):
            res2[i,3] = res2[i,3] + 2
        self.assertEqual(res1, res2)

        # [res] torch.add([res,] tensor1, value, tensor2)

    def test_csub(self):
        # with a tensor
        a = torch.randn(100,90)
        b = a.clone().normal_()

        res_add = torch.add(a, -1, b)
        res_csub = a.clone()
        res_csub.sub_(b)
        self.assertEqual(res_add, res_csub)

        # with a scalar
        a = torch.randn(100,100)

        scalar = 123.5
        res_add = torch.add(a, -scalar)
        res_csub = a.clone()
        res_csub.sub_(scalar)
        self.assertEqual(res_add, res_csub)

    def test_neg(self):
        a = torch.randn(100,90)
        zeros = torch.Tensor().resizeAs_(a).zero_()

        res_add = torch.add(zeros, -1, a)
        res_neg = a.clone()
        res_neg.neg_()
        self.assertEqual(res_neg, res_add)

    def test_cinv(self):
        a = torch.randn(100,89)
        zeros = torch.Tensor().resizeAs_(a).zero_()

        res_pow = torch.pow(a, -1)
        res_inv = a.clone()
        res_inv.cinv_()
        self.assertEqual(res_inv, res_pow)

    def test_mul(self):
        m1 = torch.randn(10,10)
        res1 = m1.clone()
        res1[:,3].mul_(2)
        res2 = m1.clone()
        for i in range(res1.size(0)):
            res2[i,3] = res2[i,3] * 2
        self.assertEqual(res1, res2)

    def test_div(self):
        m1 = torch.randn(10,10)
        res1 = m1.clone()
        res1[:,3].div_(2)
        res2 = m1.clone()
        for i in range(m1.size(0)):
            res2[i,3] = res2[i,3] / 2
        self.assertEqual(res1, res2)

    def test_fmod(self):
        m1 = torch.Tensor(10,10).uniform_(-10., 10.)
        res1 = m1.clone()
        q = 2.1
        res1[:,3].fmod_(q)
        res2 = m1.clone()
        for i in range(m1.size(1)):
            res2[i,3] = math.fmod(res2[i,3], q)
        self.assertEqual(res1, res2)

    def test_remainder(self):
        m1 = torch.Tensor(10, 10).uniform_(-10., 10.)
        res1 = m1.clone()
        q = 2.1
        res1[:,3].remainder_(q)
        res2 = m1.clone()
        for i in range(m1.size(0)):
            res2[i,3] = res2[i,3] % q
        self.assertEqual(res1, res2)

    def test_mm(self):
        # helper function
        def matrixmultiply(mat1,mat2):
            n = mat1.size(0)
            m = mat1.size(1)
            p = mat2.size(1)
            res = torch.zeros(n,p)
            for i, j in iter_indices(res):
                res[i,j] = sum(mat1[i,k] * mat2[k,j] for k in range(m))
            return res

        # contiguous case
        n, m, p = 10, 10, 5
        mat1 = torch.randn(n,m)
        mat2 = torch.randn(m,p)
        res = torch.mm(mat1,mat2)

        res2 = matrixmultiply(mat1,mat2)
        self.assertEqual(res, res2)

        # non contiguous case 1
        n, m, p = 10, 10, 5
        mat1 = torch.randn(n,m)
        mat2 = torch.randn(p,m).t()
        res = torch.mm(mat1,mat2)

        res2 = matrixmultiply(mat1,mat2)
        self.assertEqual(res, res2)

        # non contiguous case 2
        n, m, p = 10, 10, 5
        mat1 = torch.randn(m,n).t()
        mat2 = torch.randn(m,p)
        res = torch.mm(mat1,mat2)

        res2 = matrixmultiply(mat1,mat2)
        self.assertEqual(res, res2)

        # non contiguous case 3
        n, m, p = 10, 10, 5
        mat1 = torch.randn(m,n).t()
        mat2 = torch.randn(p,m).t()
        res = torch.mm(mat1,mat2)

        res2 = matrixmultiply(mat1,mat2)
        self.assertEqual(res, res2)

        # test with zero stride
        n, m, p = 10, 10, 5
        mat1 = torch.randn(n,m)
        mat2 = torch.randn(m,1).expand(m,p)
        res = torch.mm(mat1,mat2)

        res2 = matrixmultiply(mat1,mat2)
        self.assertEqual(res, res2)

    def test_bmm(self):
        num_batches = 10
        M, N, O = 23, 8, 12
        b1 = torch.randn(num_batches, M, N)
        b2 = torch.randn(num_batches, N, O)
        res = torch.bmm(b1, b2)
        for i in range(num_batches):
            r = torch.mm(b1[i], b2[i])
            self.assertEqual(r, res[i])

    def test_addbmm(self):
        # num_batches = 10
        # M, N, O = 12, 8, 5
        num_batches = 2
        M, N, O = 2, 3, 4
        b1 = torch.randn(num_batches, M, N)
        b2 = torch.randn(num_batches, N, O)
        res = torch.bmm(b1, b2)
        res2 = torch.Tensor().resizeAs_(res[0]).zero_()

        res2.addbmm_(b1,b2)
        self.assertEqual(res2, res.sum(0)[0])

        res2.addbmm_(1,b1,b2)
        self.assertEqual(res2, res.sum(0)[0]*2)

        res2.addbmm_(1.,.5,b1,b2)
        self.assertEqual(res2, res.sum(0)[0]*2.5)

        res3 = torch.addbmm(1,res2,0,b1,b2)
        self.assertEqual(res3, res2)

        res4 = torch.addbmm(1,res2,.5,b1,b2)
        self.assertEqual(res4, res.sum(0)[0]*3)

        res5 = torch.addbmm(0,res2,1,b1,b2)
        self.assertEqual(res5, res.sum(0)[0])

        res6 = torch.addbmm(.1,res2,.5,b1,b2)
        self.assertEqual(res6, res2 * .1 + res.sum(0) * .5)

    def test_baddbmm(self):
        num_batches = 10
        M, N, O = 12, 8, 5
        b1 = torch.randn(num_batches, M, N)
        b2 = torch.randn(num_batches, N, O)
        res = torch.bmm(b1, b2)
        res2 = torch.Tensor().resizeAs_(res).zero_()

        res2.baddbmm_(b1,b2)
        self.assertEqual(res2, res)

        res2.baddbmm_(1,b1,b2)
        self.assertEqual(res2, res*2)

        res2.baddbmm_(1,.5,b1,b2)
        self.assertEqual(res2, res*2.5)

        res3 = torch.baddbmm(1,res2,0,b1,b2)
        self.assertEqual(res3, res2)

        res4 = torch.baddbmm(1,res2,.5,b1,b2)
        self.assertEqual(res4, res*3)

        res5 = torch.baddbmm(0,res2,1,b1,b2)
        self.assertEqual(res5, res)

        res6 = torch.baddbmm(.1,res2,.5,b1,b2)
        self.assertEqual(res6, res2 * .1 + res * .5)

    def test_clamp(self):
        m1 = torch.rand(100).mul(5).add(-2.5)  # uniform in [-2.5, 2.5]
        # just in case we're extremely lucky.
        min_val = -1
        max_val = 1
        m1[1] = min_val
        m1[2] = max_val

        res1 = m1.clone()
        res1.clamp_(min_val, max_val)
        res2 = m1.clone()
        for i in iter_indices(res2):
            res2[i] = max(min_val, min(max_val, res2[i]))
        self.assertEqual(res1, res2)

    def test_pow(self):
        # [res] torch.pow([res,] x)

        # base - tensor, exponent - number
        # contiguous
        m1 = torch.randn(100,100)
        res1 = torch.pow(m1[4], 3)
        res2 = res1.clone().zero_()
        for i in range(res2.size(0)):
            res2[i] = math.pow(m1[4][i], 3)
        self.assertEqual(res1, res2)

        # non-contiguous
        m1 = torch.randn(100,100)
        res1 = torch.pow(m1[:,4], 3)
        res2 = res1.clone().zero_()
        for i in range(res2.size(0)):
            res2[i] = math.pow(m1[i,4], 3)
        self.assertEqual(res1, res2)

        # base - number, exponent - tensor
        # contiguous
        m1 = torch.randn(100,100)
        res1 = torch.pow(3, m1[4])
        res2 = res1.clone().zero_()
        for i in range(res2.size(0)):
            res2[i] = math.pow(3, m1[4,i])
        self.assertEqual(res1, res2)

        # non-contiguous
        m1 = torch.randn(100,100)
        res1 = torch.pow(3, m1[:,4])
        res2 = res1.clone().zero_()
        for i in range(res2.size(0)):
            res2[i] = math.pow(3, m1[i][4])
        self.assertEqual(res1, res2)

    def _test_cop(self, torchfn, mathfn):
        def reference_implementation(res2):
            for i, j in iter_indices(sm1):
                idx1d = i * sm1.size(0) + j
                res2[i,j] = mathfn(sm1[i,j], sm2[idx1d])
            return res2

        # contiguous
        m1 = torch.randn(10, 10, 10)
        m2 = torch.randn(10, 10 * 10)
        sm1 = m1[4]
        sm2 = m2[4]
        res1 = torchfn(sm1, sm2)
        res2 = reference_implementation(res1.clone())
        self.assertEqual(res1, res2)

        # non-contiguous
        m1 = torch.randn(10, 10, 10)
        m2 = torch.randn(10 * 10, 10 * 10)
        sm1 = m1[:,4]
        sm2 = m2[:,4]
        res1 = torchfn(sm1, sm2)
        res2 = reference_implementation(res1.clone())
        self.assertEqual(res1, res2)

    def test_cdiv(self):
        self._test_cop(torch.div, lambda x, y: x / y)

    def test_cfmod(self):
        self._test_cop(torch.fmod, math.fmod)

    def test_cremainder(self):
        self._test_cop(torch.remainder, lambda x, y: x % y)

    def test_cmul(self):
        self._test_cop(torch.mul, lambda x, y: x * y)

    def test_cpow(self):
        self._test_cop(torch.pow, lambda x, y: float('nan') if x < 0 else math.pow(x, y))

    # TODO: these tests only check if it's possible to pass a return value
    # it'd be good to expand them
    def test_sum(self):
        x = torch.rand(100, 100)
        res1 = torch.sum(x, 1)
        res2 = torch.Tensor()
        torch.sum(res2, x, 1)
        self.assertEqual(res1, res2)

    def test_prod(self):
        x = torch.rand(100, 100)
        res1 = torch.prod(x, 1)
        res2 = torch.Tensor()
        torch.prod(res2, x, 1)
        self.assertEqual(res1, res2)

    def test_cumsum(self):
        x = torch.rand(100, 100)
        res1 = torch.cumsum(x, 1)
        res2 = torch.Tensor()
        torch.cumsum(res2, x, 1)
        self.assertEqual(res1, res2)

    def test_cumprod(self):
        x = torch.rand(100, 100)
        res1 = torch.cumprod(x, 1)
        res2 = torch.Tensor()
        torch.cumprod(res2, x, 1)
        self.assertEqual(res1, res2)

    def test_cross(self):
        x = torch.rand(100, 3, 100)
        y = torch.rand(100, 3, 100)
        res1 = torch.cross(x, y)
        res2 = torch.Tensor()
        torch.cross(res2, x, y)
        self.assertEqual(res1, res2)

    def test_zeros(self):
        res1 = torch.zeros(100, 100)
        res2 = torch.Tensor()
        torch.zeros(res2, 100, 100)
        self.assertEqual(res1, res2)

    def test_histc(self):
        x = torch.Tensor((2, 4, 2, 2, 5, 4))
        y = torch.histc(x, 5, 1, 5) # nbins,  min,  max
        z = torch.Tensor((0, 3, 0, 2, 1))
        self.assertEqual(y, z)

    def test_ones(self):
        res1 = torch.ones(100, 100)
        res2 = torch.Tensor()
        torch.ones(res2, 100, 100)
        self.assertEqual(res1, res2)

    def test_diag(self):
        x = torch.rand(100, 100)
        res1 = torch.diag(x)
        res2 = torch.Tensor()
        torch.diag(res2, x)
        self.assertEqual(res1, res2)

    def test_eye(self):
        res1 = torch.eye(100, 100)
        res2 = torch.Tensor()
        torch.eye(res2, 100, 100)
        self.assertEqual(res1, res2)

    def test_renorm(self):
        m1 = torch.randn(10,5)
        res1 = torch.Tensor()

        def renorm(matrix, value, dim, max_norm):
            m1 = matrix.transpose(dim, 0).contiguous()
            # collapse non-dim dimensions.
            m2 = m1.clone().resize_(m1.size(0), int(math.floor(m1.nElement() / m1.size(0))))
            norms = m2.norm(value, 1)
            # clip
            new_norms = norms.clone()
            new_norms[torch.gt(norms, max_norm)] = max_norm
            new_norms.div_(norms.add_(1e-7))
            # renormalize
            m1.mul_(new_norms.expandAs(m1))
            return m1.transpose(dim, 0)

        # note that the axis fed to torch.renorm is different (2~=1)
        maxnorm = m1.norm(2, 1).mean()
        m2 = renorm(m1, 2, 1, maxnorm)
        m1.renorm_(2, 1, maxnorm)
        self.assertEqual(m1, m2, 1e-5)
        self.assertEqual(m1.norm(2, 0), m2.norm(2, 0), 1e-5)

        m1 = torch.randn(3, 4, 5)
        m2 = m1.transpose(1, 2).contiguous().clone().resize_(15, 4)
        maxnorm = m2.norm(2, 0).mean()
        m2 = renorm(m2, 2, 1, maxnorm)
        m1.renorm_(2, 1, maxnorm)
        m3 = m1.transpose(1, 2).contiguous().clone().resize_(15, 4)
        self.assertEqual(m3, m2)
        self.assertEqual(m3.norm(2, 0), m2.norm(2, 0))

    def test_multinomial(self):
        # with replacement
        n_row = 3
        for n_col in range(4, 5+1):
            prob_dist = torch.rand(n_row, n_col)
            prob_dist.select(1, n_col-1).fill_(0) #index n_col shouldn't be sampled
            n_sample = n_col
            sample_indices = torch.multinomial(prob_dist, n_sample, True)
            self.assertEqual(prob_dist.dim(), 2)
            self.assertEqual(sample_indices.size(1), n_sample)
            for index in product(range(n_row), range(n_sample)):
                self.assertNotEqual(sample_indices[index], n_col, "sampled an index with zero probability")

        # without replacement
        n_row = 3
        for n_col in range(4, 5+1):
            prob_dist = torch.rand(n_row, n_col)
            prob_dist.select(1, n_col-1).fill_(0) #index n_col shouldn't be sampled
            n_sample = 3
            sample_indices = torch.multinomial(prob_dist, n_sample, False)
            self.assertEqual(prob_dist.dim(), 2)
            self.assertEqual(sample_indices.size(1), n_sample)
            for i in range(n_row):
                row_samples = {}
                for j in range(n_sample):
                    sample_idx = sample_indices[i,j]
                    self.assertNotEqual(sample_idx, n_col-1,
                            "sampled an index with zero probability")
                    self.assertNotIn(sample_idx, row_samples, "sampled an index twice")
                    row_samples[sample_idx] = True

        # vector
        n_col = 4
        prob_dist = torch.rand(n_col)
        n_sample = n_col
        sample_indices = torch.multinomial(prob_dist, n_sample, True)
        s_dim = sample_indices.dim()
        self.assertEqual(sample_indices.dim(), 1, "wrong number of dimensions")
        self.assertEqual(prob_dist.dim(), 1, "wrong number of prob_dist dimensions")
        self.assertEqual(sample_indices.size(0), n_sample, "wrong number of samples")

    def test_range(self):
        res1 = torch.range(0, 1)
        res2 = torch.Tensor()
        torch.range(res2, 0, 1)
        self.assertEqual(res1, res2, 0)

        # Check range for non-contiguous tensors.
        x = torch.zeros(2, 3)
        torch.range(x.narrow(1, 1, 2), 0, 3)
        res2 = torch.Tensor(((0, 0, 1), (0, 2, 3)))
        self.assertEqual(x, res2, 1e-16)

        # Check negative
        res1 = torch.Tensor((1, 0))
        res2 = torch.Tensor()
        torch.range(res2, 1, 0, -1)
        self.assertEqual(res1, res2, 0)

        # Equal bounds
        res1 = torch.ones(1)
        res2 = torch.Tensor()
        torch.range(res2, 1, 1, -1)
        self.assertEqual(res1, res2, 0)
        torch.range(res2, 1, 1, 1)
        self.assertEqual(res1, res2, 0)

        # FloatTensor
        res1 = torch.range(torch.FloatTensor(), 0.6, 0.9, 0.1)
        self.assertEqual(res1.size(0), 4)
        res1 = torch.range(torch.FloatTensor(), 1, 10, 0.3)
        self.assertEqual(res1.size(0), 31)

        # DoubleTensor
        res1 = torch.range(torch.DoubleTensor(), 0.6, 0.9, 0.1)
        self.assertEqual(res1.size(0), 4)
        res1 = torch.range(torch.DoubleTensor(), 1, 10, 0.3)
        self.assertEqual(res1.size(0), 31)

    def test_randperm(self):
        _RNGState = torch.getRNGState()
        res1 = torch.randperm(100)
        res2 = torch.Tensor()
        torch.setRNGState(_RNGState)
        torch.randperm(res2, 100)
        self.assertEqual(res1, res2, 0)

    def assertIsOrdered(self, order, x, mxx, ixx, task):
        SIZE = 4
        if order == 'descending':
            check_order = lambda a, b: a >= b
        elif order == 'ascending':
            check_order = lambda a, b: a <= b
        else:
            error('unknown order "{}", must be "ascending" or "descending"'.format(order))

        are_ordered = True
        for j, k in product(range(SIZE), range(1, SIZE)):
            self.assertTrue(check_order(mxx[j][k-1], mxx[j][k]),
                    'torch.sort ({}) values unordered for {}'.format(order, task))

        seen = set()
        indicesCorrect = True
        size = x.size(x.dim()-1)
        for k in range(size):
            seen.clear()
            for j in range(size):
                self.assertEqual(x[k][ixx[k][j]], mxx[k][j],
                        'torch.sort ({}) indices wrong for {}'.format(order, task))
                seen.add(ixx[k][j])
            self.assertEqual(len(seen), size)

    def test_sort(self):
        SIZE = 4
        x = torch.rand(SIZE, SIZE)
        res1val, res1ind = torch.sort(x)

        # Test use of result tensor
        res2val = torch.Tensor()
        res2ind = torch.LongTensor()
        torch.sort(res2val, res2ind, x)
        self.assertEqual(res1val, res2val, 0)
        self.assertEqual(res1ind, res2ind, 0)

        # Test sorting of random numbers
        self.assertIsOrdered('ascending', x, res2val, res2ind, 'random')

        # Test simple sort
        self.assertEqual(
            torch.sort(torch.Tensor((50, 40, 30, 20, 10)))[0],
            torch.Tensor((10, 20, 30, 40, 50)),
            0
        )

        # Test that we still have proper sorting with duplicate keys
        x = torch.floor(torch.rand(SIZE, SIZE)*10)
        torch.sort(res2val, res2ind, x)
        self.assertIsOrdered('ascending', x, res2val, res2ind, 'random with duplicate keys')

        # DESCENDING SORT
        x = torch.rand(SIZE, SIZE)
        res1val, res1ind = torch.sort(x, x.dim()-1, True)

        # Test use of result tensor
        res2val = torch.Tensor()
        res2ind = torch.LongTensor()
        torch.sort(res2val, res2ind, x, x.dim()-1, True)
        self.assertEqual(res1val, res2val, 0)
        self.assertEqual(res1ind, res2ind, 0)

        # Test sorting of random numbers
        self.assertIsOrdered('descending', x, res2val, res2ind, 'random')

        # Test simple sort task
        self.assertEqual(
            torch.sort(torch.Tensor((10, 20, 30, 40, 50)), 0, True)[0],
            torch.Tensor((50, 40, 30, 20, 10)),
            0
        )

        # Test that we still have proper sorting with duplicate keys
        self.assertIsOrdered('descending', x, res2val, res2ind, 'random with duplicate keys')

    def test_topk(self):
        def topKViaSort(t, k, dim, dir):
            sorted, indices = t.sort(dim, dir)
            return sorted.narrow(dim, 0, k), indices.narrow(dim, 0, k)

        def compareTensors(t, res1, ind1, res2, ind2, dim):
            # Values should be exactly equivalent
            self.assertEqual(res1, res2, 0)

            # Indices might differ based on the implementation, since there is
            # no guarantee of the relative order of selection
            if not ind1.eq(ind2).all():
                # To verify that the indices represent equivalent elements,
                # gather from the input using the topk indices and compare against
                # the sort indices
                vals = t.gather(dim, ind2)
                self.assertEqual(res1, vals, 0)

        def compare(t, k, dim, dir):
            topKVal, topKInd = t.topk(k, dim, dir, True)
            sortKVal, sortKInd = topKViaSort(t, k, dim, dir)
            compareTensors(t, sortKVal, sortKInd, topKVal, topKInd, dim)

        t = torch.rand(random.randrange(SIZE),
                        random.randrange(SIZE),
                        random.randrange(SIZE))

        for kTries in range(3):
            for dimTries in range(3):
                for transpose in (True, False):
                    for dir in (True, False):
                        testTensor = t
                        if transpose:
                            dim1 = random.randrange(t.nDimension())
                            dim2 = dim1
                            while dim1 == dim2:
                                dim2 = random.randrange(t.nDimension())

                            testTensor = t.transpose(dim1, dim2)

                        dim = random.randrange(testTensor.nDimension())
                        k = random.randint(1, testTensor.size(dim))
                        compare(testTensor, k, dim, dir)

    def test_kthvalue(self):
        SIZE = 50
        x = torch.rand(SIZE, SIZE, SIZE)
        x0 = x.clone()

        k = random.randint(1, SIZE)
        res1val, res1ind = torch.kthvalue(x, k)
        res2val, res2ind = torch.sort(x)

        self.assertEqual(res1val[:,:,0], res2val[:,:,k-1], 0)
        self.assertEqual(res1ind[:,:,0], res2ind[:,:,k-1], 0)
        # test use of result tensors
        k = random.randint(1, SIZE)
        res1val = torch.Tensor()
        res1ind = torch.LongTensor()
        torch.kthvalue(res1val, res1ind, x, k)
        res2val, res2ind = torch.sort(x)
        self.assertEqual(res1val[:,:,0], res2val[:,:,k-1], 0)
        self.assertEqual(res1ind[:,:,0], res2ind[:,:,k-1], 0)

        # test non-default dim
        k = random.randint(1, SIZE)
        res1val, res1ind = torch.kthvalue(x, k, 0)
        res2val, res2ind = torch.sort(x, 0)
        self.assertEqual(res1val[0], res2val[k-1], 0)
        self.assertEqual(res1ind[0], res2ind[k-1], 0)

        # non-contiguous
        y = x.narrow(1, 0, 1)
        y0 = y.contiguous()
        k = random.randint(1, SIZE)
        res1val, res1ind = torch.kthvalue(y, k)
        res2val, res2ind = torch.kthvalue(y0, k)
        self.assertEqual(res1val, res2val, 0)
        self.assertEqual(res1ind, res2ind, 0)

        # check that the input wasn't modified
        self.assertEqual(x, x0, 0)

        # simple test case (with repetitions)
        y = torch.Tensor((3, 5, 4, 1, 1, 5))
        self.assertEqual(torch.kthvalue(y, 3)[0], torch.Tensor((3,)), 0)
        self.assertEqual(torch.kthvalue(y, 2)[0], torch.Tensor((1,)), 0)

    def test_median(self):
        for size in (155, 156):
            x = torch.rand(size, size)
            x0 = x.clone()

            res1val, res1ind = torch.median(x)
            res2val, res2ind = torch.sort(x)
            ind = int(math.floor((size+1)/2) - 1)

            self.assertEqual(res2val.select(1, ind), res1val.select(1, 0), 0)
            self.assertEqual(res2val.select(1, ind), res1val.select(1, 0), 0)

            # Test use of result tensor
            res2val = torch.Tensor()
            res2ind = torch.LongTensor()
            torch.median(res2val, res2ind, x)
            self.assertEqual(res2val, res1val, 0)
            self.assertEqual(res2ind, res1ind, 0)

            # Test non-default dim
            res1val, res1ind = torch.median(x, 0)
            res2val, res2ind = torch.sort(x, 0)
            self.assertEqual(res1val[0], res2val[ind], 0)
            self.assertEqual(res1ind[0], res2ind[ind], 0)

            # input unchanged
            self.assertEqual(x, x0, 0)

    def test_mode(self):
        x = torch.range(1, SIZE * SIZE).clone().resize_(SIZE, SIZE)
        x[:2] = 1
        x[:,:2] = 1
        x0 = x.clone()

        # Pre-calculated results.
        res1val = torch.Tensor(SIZE, 1).fill_(1)
        # The indices are the position of the last appearance of the mode element.
        res1ind = torch.LongTensor(SIZE, 1).fill_(1)
        res1ind[0] = SIZE-1
        res1ind[1] = SIZE-1

        res2val, res2ind = torch.mode(x)

        self.assertEqual(res1val, res2val, 0)
        self.assertEqual(res1ind, res2ind, 0)

        # Test use of result tensor
        res2val = torch.Tensor()
        res2ind = torch.LongTensor()
        torch.mode(res2val, res2ind, x)
        self.assertEqual(res1val, res2val, 0)
        self.assertEqual(res1ind, res2ind, 0)

        # Test non-default dim
        res2val, res2ind = torch.mode(x, 0)
        self.assertEqual(res1val.view(1, SIZE), res2val, 0)
        self.assertEqual(res1ind.view(1, SIZE), res2ind, 0)

        # input unchanged
        self.assertEqual(x, x0, 0)

    def test_tril(self):
        x = torch.rand(SIZE, SIZE)
        res1 = torch.tril(x)
        res2 = torch.Tensor()
        torch.tril(res2, x)
        self.assertEqual(res1, res2, 0)

    def test_triu(self):
        x = torch.rand(SIZE, SIZE)
        res1 = torch.triu(x)
        res2 = torch.Tensor()
        torch.triu(res2, x)
        self.assertEqual(res1, res2, 0)

    def test_cat(self):
        SIZE = 10
        # 2-arg cat
        for dim in range(3):
            x = torch.rand(13, SIZE, SIZE).transpose(0, dim)
            y = torch.rand(17, SIZE, SIZE).transpose(0, dim)
            res1 = torch.cat(x, y, dim)
            self.assertEqual(res1.narrow(dim, 0, 13), x, 0)
            self.assertEqual(res1.narrow(dim, 13, 17), y, 0)

            # Check stateless implementation
            res2 = torch.Tensor()
            torch.cat(res2, x, y, dim)
            self.assertEqual(res1, res2, 0)

        # Check iterables
        for dim in range(3):
            x = torch.rand(13, SIZE, SIZE).transpose(0, dim)
            y = torch.rand(17, SIZE, SIZE).transpose(0, dim)
            z = torch.rand(19, SIZE, SIZE).transpose(0, dim)

            res1 = torch.cat((x, y, z), dim)
            self.assertEqual(res1.narrow(dim, 0, 13), x, 0)
            self.assertEqual(res1.narrow(dim, 13, 17), y, 0)
            self.assertEqual(res1.narrow(dim, 30, 19), z, 0)
            self.assertRaises(ValueError, lambda: torch.cat([]))

            res2 = torch.Tensor()
            torch.cat(res2, (x, y, z), dim)
            self.assertEqual(res1, res2, 0)
            res2 = res2.float()
            torch.cat(res2, (x.float(), y.float(), z.float()), dim)
            self.assertEqual(res1.float(), res2, 0)
            res2 = res2.double()
            torch.cat(res2, (x.double(), y.double(), z.double()), dim)
            self.assertEqual(res1.double(), res2, 0)

    def test_linspace(self):
        _from = random.random()
        to = _from + random.random()
        res1 = torch.linspace(_from, to, 137)
        res2 = torch.Tensor()
        torch.linspace(res2, _from, to, 137)
        self.assertEqual(res1, res2, 0)
        self.assertRaises(RuntimeError, lambda: torch.linspace(0, 1, 1))
        self.assertEqual(torch.linspace(0, 0, 1), torch.zeros(1), 0)

        # Check linspace for generating with start > end.
        self.assertEqual(torch.linspace(2, 0, 3), torch.Tensor((2, 1, 0)), 0)

        # Check linspace for non-contiguous tensors.
        x = torch.zeros(2, 3)
        y = torch.linspace(x.narrow(1, 1, 2), 0, 3, 4)
        self.assertEqual(x, torch.Tensor(((0, 0, 1), (0, 2, 3))), 0)

    def test_logspace(self):
        _from = random.random()
        to = _from + random.random()
        res1 = torch.logspace(_from, to, 137)
        res2 = torch.Tensor()
        torch.logspace(res2, _from, to, 137)
        self.assertEqual(res1, res2, 0)
        self.assertRaises(RuntimeError, lambda: torch.logspace(0, 1, 1))
        self.assertEqual(torch.logspace(0, 0, 1), torch.ones(1), 0)

        # Check logspace_ for generating with start > end.
        self.assertEqual(torch.logspace(1, 0, 2), torch.Tensor((10, 1)), 0)

        # Check logspace_ for non-contiguous tensors.
        x = torch.zeros(2, 3)
        y = torch.logspace(x.narrow(1, 1, 2), 0, 3, 4)
        self.assertEqual(x, torch.Tensor(((0, 1, 10), (0, 100, 1000))), 0)

    def test_rand(self):
        torch.manualSeed(123456)
        res1 = torch.rand(SIZE, SIZE)
        res2 = torch.Tensor()
        torch.manualSeed(123456)
        torch.rand(res2, SIZE, SIZE)
        self.assertEqual(res1, res2)

    def test_randn(self):
        torch.manualSeed(123456)
        res1 = torch.randn(SIZE, SIZE)
        res2 = torch.Tensor()
        torch.manualSeed(123456)
        torch.randn(res2, SIZE, SIZE)
        self.assertEqual(res1, res2)

    @unittest.skipIf(not hasattr(torch, 'gesv'), 'Compiled without gesv')
    def test_gesv(self):
        a = torch.Tensor(((6.80, -2.11,  5.66,  5.97,  8.23),
                        (-6.05, -3.30,  5.36, -4.44,  1.08),
                        (-0.45,  2.58, -2.70,  0.27,  9.04),
                        (8.32,  2.71,  4.35, -7.17,  2.14),
                        (-9.67, -5.14, -7.26,  6.08, -6.87))).t()
        b = torch.Tensor(((4.02,  6.19, -8.22, -7.57, -3.03),
                        (-1.56,  4.00, -8.67,  1.75,  2.86),
                        (9.81, -4.09, -4.57, -8.61,  8.99))).t()

        res1 = torch.gesv(b,a)
        self.assertLessEqual(b.dist(a * res1), 1e-12)
        ta = torch.Tensor()
        tb = torch.Tensor()
        res2 = torch.gesv(tb, ta, b, a)
        res3 = torch.gesv(b, a, b, a)
        self.assertEqual(res1, tb)
        self.assertEqual(res1, b)
        self.assertEqual(res1, res2)
        self.assertEqual(res1, res3)

        # test reuse
        res1 = torch.gesv(b, a)
        ta = torch.Tensor()
        tb = torch.Tensor()
        torch.gesv(tb, ta, b, a)
        self.assertEqual(res1, tb)
        torch.gesv(tb, ta, b, a)
        self.assertEqual(res1, tb)

    @unittest.skipIf(not hasattr(torch, 'trtrs'), 'Compiled without trtrs')
    def test_trtrs(self):
        a = torch.Tensor(((6.80, -2.11,  5.66,  5.97,  8.23),
                        (-6.05, -3.30,  5.36, -4.44,  1.08),
                        (-0.45,  2.58, -2.70,  0.27,  9.04),
                        (8.32,  2.71,  4.35, -7.17,  2.14),
                        (-9.67, -5.14, -7.26,  6.08, -6.87))).t()
        b = torch.Tensor(((4.02,  6.19, -8.22, -7.57, -3.03),
                        (-1.56,  4.00, -8.67,  1.75,  2.86),
                        (9.81, -4.09, -4.57, -8.61,  8.99))).t()

        U = torch.triu(a)
        L = torch.tril(a)

        # solve Ux = b
        x = torch.trtrs(b, U)
        self.assertLessEqual(b.dist(U * x), 1e-12)
        x = torch.trtrs(b, U, 'U', 'N', 'N')
        self.assertLessEqual(b.dist(U * x), 1e-12)

        # solve Lx = b
        x = torch.trtrs(b, L, 'L')
        self.assertLessEqual(b.dist(L * x), 1e-12)
        x = torch.trtrs(b, L, 'L', 'N', 'N')
        self.assertLessEqual(b.dist(L * x), 1e-12)

        # solve U'x = b
        x = torch.trtrs(b, U, 'U', 'T')
        self.assertLessEqual(b.dist(U.t() * x), 1e-12)
        x = torch.trtrs(b, U, 'U', 'T', 'N')
        self.assertLessEqual(b.dist(U.t() * x), 1e-12)

        # solve U'x = b by manual transposition
        y = torch.trtrs(b, U.t(), 'L', 'N')
        self.assertLessEqual(x.dist(y), 1e-12)

        # solve L'x = b
        x = torch.trtrs(b, L, 'L', 'T')
        self.assertLessEqual(b.dist(L.t() * x), 1e-12)
        x = torch.trtrs(b, L, 'L', 'T', 'N')
        self.assertLessEqual(b.dist(L.t() * x), 1e-12)

        # solve L'x = b by manual transposition
        y = torch.trtrs(b, L.t(), 'U', 'N')
        self.assertLessEqual(x.dist(y), 1e-12)

        # test reuse
        res1 = torch.trtrs(b,a)
        ta = torch.Tensor()
        tb = torch.Tensor()
        torch.trtrs(tb,ta,b,a)
        self.assertEqual(res1, tb, 0)
        tb.zero_()
        torch.trtrs(tb,ta,b,a)
        self.assertEqual(res1, tb, 0)

    @unittest.skipIf(not hasattr(torch, 'gels'), 'Compiled without gels')
    def test_gels(self):
        def _test(a, b, expectedNorm):
            a_copy = a.clone()
            b_copy = b.clone()
            res1 = torch.gels(b, a)
            self.assertEqual(a, a_copy, 0)
            self.assertEqual(b, b_copy, 0)
            self.assertEqual((a * res1 - b).norm(), expectedNorm, 1e-8)

            ta = torch.Tensor()
            tb = torch.Tensor()
            res2 = torch.gels(tb, ta, b, a)
            self.assertEqual(a, a_copy, 0)
            self.assertEqual(b, b_copy, 0)
            self.assertEqual((a * res1 - b).norm(), expectedNorm, 1e-8)

            res3 = torch.gels(b, a, b, a)
            self.assertEqual((a_copy * b - b_copy).norm(), expectedNorm, 1e-8)
            self.assertEqual(res1, tb, 0)
            self.assertEqual(res1, b, 0)
            self.assertEqual(res1, res2, 0)
            self.assertEqual(res1, res3, 0)

        # basic test
        expectedNorm = 0
        a = torch.Tensor(((1.44, -9.96, -7.55,  8.34),
                        (-7.84, -0.28,  3.24,  8.09),
                        (-4.39, -3.24,  6.27,  5.28),
                        (4.53,  3.83, -6.64,  2.06))).t()
        b = torch.Tensor(((8.58,  8.26,  8.48, -5.28),
                        (9.35, -4.43, -0.70, -0.26))).t()
        _test(a, b, expectedNorm)

        # test overderemined
        expectedNorm = 17.390200628863
        a = torch.Tensor(((1.44, -9.96, -7.55,  8.34,  7.08, -5.45),
                        (-7.84, -0.28,  3.24,  8.09,  2.52, -5.70),
                        (-4.39, -3.24,  6.27,  5.28,  0.74, -1.19),
                        (4.53,  3.83, -6.64,  2.06, -2.47,  4.70))).t()
        b = torch.Tensor(((8.58,  8.26,  8.48, -5.28,  5.72,  8.93),
                        (9.35, -4.43, -0.70, -0.26, -7.36, -2.52))).t()
        _test(a, b, expectedNorm)

        # test underdetermined
        expectedNorm = 0
        a = torch.Tensor(((1.44, -9.96, -7.55),
                        (-7.84, -0.28,  3.24),
                        (-4.39, -3.24,  6.27),
                        (4.53,  3.83, -6.64))).t()
        b = torch.Tensor(((8.58,  8.26,  8.48),
                        (9.35, -4.43, -0.70))).t()
        _test(a, b, expectedNorm)

        # test reuse
        expectedNorm = 0
        a = torch.Tensor(((1.44, -9.96, -7.55,  8.34),
                        (-7.84, -0.28,  3.24,  8.09),
                        (-4.39, -3.24,  6.27,  5.28),
                        (4.53,  3.83, -6.64,  2.06))).t()
        b = torch.Tensor(((8.58,  8.26,  8.48, -5.28),
                        (9.35, -4.43, -0.70, -0.26))).t()
        ta = torch.Tensor()
        tb = torch.Tensor()
        torch.gels(tb, ta, b, a)
        self.assertEqual((a * tb - b).norm(), expectedNorm, 1e-8)
        torch.gels(tb, ta, b, a)
        self.assertEqual((a * tb - b).norm(), expectedNorm, 1e-8)
        torch.gels(tb, ta, b, a)
        self.assertEqual((a * tb - b).norm(), expectedNorm, 1e-8)

    @unittest.skipIf(not hasattr(torch, 'eig'), 'Compiled without eig')
    def test_eig(self):
        a = torch.Tensor(((1.96,  0.00,  0.00,  0.00,  0.00),
                        (-6.49,  3.80,  0.00,  0.00,  0.00),
                        (-0.47, -6.39,  4.17,  0.00,  0.00),
                        (-7.20,  1.50, -1.51,  5.70,  0.00),
                        (-0.65, -6.34,  2.67,  1.80, -7.10))).t().contiguous()
        e = torch.eig(a)
        ee, vv = torch.eig(a, 'V')
        te = torch.Tensor()
        tv = torch.Tensor()
        eee, vvv = torch.eig(te, tv, a, 'V')
        self.assertEqual(e, ee, 1e-12)
        self.assertEqual(ee, eee, 1e-12)
        self.assertEqual(ee, te, 1e-12)
        self.assertEqual(vv, vvv, 1e-12)
        self.assertEqual(vv, tv, 1e-12)

        # test reuse
        X = torch.randn(4,4)
        X = X.t() * X
        e, v = torch.zeros(4,2), torch.zeros(4,4)
        torch.eig(e, v, X, 'V')
        Xhat = v * torch.diag(e.select(1, 0)) * v.t()
        self.assertEqual(X, Xhat, 1e-8, 'VeV\' wrong')
        self.assertFalse(v.isContiguous(), 'V is contiguous')

        torch.eig(e, v, X, 'V')
        Xhat = torch.mm(v, torch.mm(e.select(1, 0).diag(), v.t()))
        self.assertEqual(X, Xhat, 1e-8, 'VeV\' wrong')
        self.assertFalse(v.isContiguous(), 'V is contiguous')

        # test non-contiguous
        X = torch.randn(4, 4)
        X = X.t() * X
        e = torch.zeros(4, 2, 2)[:,2]
        v = torch.zeros(4, 2, 4)[:,2]
        self.assertFalse(v.isContiguous(), 'V is contiguous')
        self.assertFalse(e.isContiguous(), 'E is contiguous')
        torch.eig(e, v, X, 'V')
        Xhat = v * torch.diag(e.select(1, 0)) * v.t()
        self.assertEqual(X, Xhat, 1e-8, 'VeV\' wrong')

    @unittest.skipIf(not hasattr(torch, 'symeig'), 'Compiled without symeig')
    def test_symeig(self):
        xval = torch.rand(100,3)
        cov = torch.mm(xval.t(), xval)
        rese = torch.zeros(3)
        resv = torch.zeros(3,3)

        # First call to symeig
        self.assertTrue(resv.isContiguous(), 'resv is not contiguous')
        torch.symeig(rese, resv, cov.clone(), 'V')
        ahat = resv * torch.diag(rese) * resv.t()
        self.assertEqual(cov, ahat, 1e-8, 'VeV\' wrong')

        # Second call to symeig
        self.assertFalse(resv.isContiguous(), 'resv is contiguous')
        torch.symeig(rese, resv, cov.clone(), 'V')
        ahat = torch.mm(torch.mm(resv, torch.diag(rese)), resv.t())
        mytester.assertTensorEq(cov, ahat, 1e-8, 'VeV\' wrong')

        # test non-contiguous
        X = torch.rand(5, 5)
        X = X.t() * X
        e = torch.zeros(4, 2).select(1, 1)
        v = torch.zeros(4, 2, 4)[:,1]
        self.assertFalse(v.isContiguous(), 'V is contiguous')
        self.assertFalse(e.isContiguous(), 'E is contiguous')
        torch.symeig(e, v, X, 'V')
        Xhat = v * torch.diag(e) * v.t()
        self.assertEqual(X, Xhat, 1e-8, 'VeV\' wrong')

    @unittest.skipIf(not hasattr(torch, 'svd'), 'Compiled without svd')
    def test_svd(self):
        a=torch.Tensor(((8.79,  6.11, -9.15,  9.57, -3.49,  9.84),
                        (9.93,  6.91, -7.93,  1.64,  4.02,  0.15),
                        (9.83,  5.04,  4.86,  8.83,  9.80, -8.99),
                        (5.45, -0.27,  4.85,  0.74, 10.00, -6.02),
                        (3.16,  7.98,  3.01,  5.80,  4.27, -5.31))).t().clone()
        u, s, v = torch.svd(a)
        uu = torch.Tensor()
        ss = torch.Tensor()
        vv = torch.Tensor()
        uuu, sss, vvv = torch.svd(uu, ss, vv, a)
        self.assertEqual(u, uu, 0, 'torch.svd')
        self.assertEqual(u, uuu, 0, 'torch.svd')
        self.assertEqual(s, ss, 0, 'torch.svd')
        self.assertEqual(s, sss, 0, 'torch.svd')
        self.assertEqual(v, vv, 0, 'torch.svd')
        self.assertEqual(v, vvv, 0, 'torch.svd')

        # test reuse
        X = torch.randn(4, 4)
        U, S, V = torch.svd(X)
        Xhat = torch.mm(U, torch.mm(S.diag(), V.t()))
        mytester.assertEqual(X, Xhat, 1e-8, 'USV\' wrong')

        self.assertFalse(U.isContiguous(), 'U is contiguous')
        torch.svd(U, S, V, X)
        Xhat = torch.mm(U, torch.mm(S.diag(), V.t()))
        self.assertEqual(X, Xhat, 1e-8, 'USV\' wrong')

        # test non-contiguous
        X = torch.randn(5, 5)
        U = torch.zeros(5, 2, 5)[:,1]
        S = torch.zeros(5, 2)[:,2]
        V = torch.zeros(5, 2, 5)[:,2]

        self.assertFalse(U.isContiguous(), 'U is contiguous')
        self.assertFalse(S.isContiguous(), 'S is contiguous')
        self.assertFalse(V.isContiguous(), 'V is contiguous')
        torch.svd(U, S, V, X)
        Xhat = torch.mm(U, torch.mm(S.diag(), V.t()))
        self.assertEqual(X, Xhat, 1e-8, 'USV\' wrong')

    @unittest.skipIf(not hasattr(torch, 'inverse'), 'Compiled without inverse')
    def test_inverse(self):
        M = torch.randn(5,5)
        MI = torch.inverse(M)
        E = torch.eye(5)
        self.assertFalse(MI.isContiguous(), 'MI is contiguous')
        self.assertEqual(E, torch.mm(M, MI), 1e-8, 'inverse value')
        self.assertEqual(E, torch.mm(MI, M), 1e-8, 'inverse value')

        MII = torch.Tensor(5, 5)
        torch.inverse(MII, M)
        self.assertFalse(MII.isContiguous(), 'MII is contiguous')
        self.assertEqual(MII, MI, 0, 'inverse value in-place')
        # second call, now that MII is transposed
        torch.inverse(MII, M)
        self.assertFalse(MII.isContiguous(), 'MII is contiguous')
        self.assertEqual(MII, MI, 0, 'inverse value in-place')

    @unittest.skip("Not implemented yet")
    def test_conv2(self):
        x = torch.rand(math.floor(torch.uniform(50, 100)), math.floor(torch.uniform(50, 100)))
        k = torch.rand(math.floor(torch.uniform(10, 20)), math.floor(torch.uniform(10, 20)))
        imvc = torch.conv2(x, k)
        imvc2 = torch.conv2(x, k, 'V')
        imfc = torch.conv2(x, k, 'F')

        ki = k.clone()
        ks = k.storage()
        kis = ki.storage()
        for i in range(ks.size()-1, 0, -1):
            kis[ks.size()-i+1] = ks[i]
        #for i=ks.size(), 1, -1 do kis[ks.size()-i+1]=ks[i] end
        imvx = torch.xcorr2(x, ki)
        imvx2 = torch.xcorr2(x, ki, 'V')
        imfx = torch.xcorr2(x, ki, 'F')

        self.assertEqual(imvc, imvc2, 0, 'torch.conv2')
        self.assertEqual(imvc, imvx, 0, 'torch.conv2')
        self.assertEqual(imvc, imvx2, 0, 'torch.conv2')
        self.assertEqual(imfc, imfx, 0, 'torch.conv2')
        self.assertLessEqual(math.abs(x.dot(x) - torch.xcorr2(x, x)[0][0]), 1e-10, 'torch.conv2')

        xx = torch.Tensor(2, x.size(1), x.size(2))
        xx[1].copy_(x)
        xx[2].copy_(x)
        kk = torch.Tensor(2, k.size(1), k.size(2))
        kk[1].copy_(k)
        kk[2].copy_(k)

        immvc = torch.conv2(xx, kk)
        immvc2 = torch.conv2(xx, kk, 'V')
        immfc = torch.conv2(xx, kk, 'F')

        self.assertEqual(immvc[0], immvc[1], 0, 'torch.conv2')
        self.assertEqual(immvc[0], imvc, 0, 'torch.conv2')
        self.assertEqual(immvc2[0], imvc2, 0, 'torch.conv2')
        self.assertEqual(immfc[0], immfc[1], 0, 'torch.conv2')
        self.assertEqual(immfc[0], imfc, 0, 'torch.conv2')

    @unittest.skip("Not implemented yet")
    def test_conv3(self):
        x = torch.rand(math.floor(torch.uniform(20, 40)),
                math.floor(torch.uniform(20, 40)),
                math.floor(torch.uniform(20, 40)))
        k = torch.rand(math.floor(torch.uniform(5, 10)),
                math.floor(torch.uniform(5, 10)),
                math.floor(torch.uniform(5, 10)))
        imvc = torch.conv3(x, k)
        imvc2 = torch.conv3(x, k, 'V')
        imfc = torch.conv3(x, k, 'F')

        ki = k.clone();
        ks = k.storage()
        kis = ki.storage()
        for i in range(ks.size()-1, 0, -1):
            kis[ks.size()-i+1] = ks[i]
        imvx = torch.xcorr3(x, ki)
        imvx2 = torch.xcorr3(x, ki, 'V')
        imfx = torch.xcorr3(x, ki, 'F')

        self.assertEqual(imvc, imvc2, 0, 'torch.conv3')
        self.assertEqual(imvc, imvx, 0, 'torch.conv3')
        self.assertEqual(imvc, imvx2, 0, 'torch.conv3')
        self.assertEqual(imfc, imfx, 0, 'torch.conv3')
        self.assertLessEqual(math.abs(x.dot(x) - torch.xcorr3(x, x)[0][0][0]), 4e-10, 'torch.conv3')

        xx = torch.Tensor(2, x.size(1), x.size(2), x.size(3))
        xx[1].copy_(x)
        xx[2].copy_(x)
        kk = torch.Tensor(2, k.size(1), k.size(2), k.size(3))
        kk[1].copy_(k)
        kk[2].copy_(k)

        immvc = torch.conv3(xx, kk)
        immvc2 = torch.conv3(xx, kk, 'V')
        immfc = torch.conv3(xx, kk, 'F')

        self.assertEqual(immvc[0], immvc[1], 0, 'torch.conv3')
        self.assertEqual(immvc[0], imvc, 0, 'torch.conv3')
        self.assertEqual(immvc2[0], imvc2, 0, 'torch.conv3')
        self.assertEqual(immfc[0], immfc[1], 0, 'torch.conv3')
        self.assertEqual(immfc[0], imfc, 0, 'torch.conv3')

    @unittest.skip("Not implemented yet")
    def _test_conv_corr_eq(self, fn, fn_2_to_3):
        ix = math.floor(random.randint(20, 40))
        iy = math.floor(random.randint(20, 40))
        iz = math.floor(random.randint(20, 40))
        kx = math.floor(random.randint(5, 10))
        ky = math.floor(random.randint(5, 10))
        kz = math.floor(random.randint(5, 10))

        x = torch.rand(ix, iy, iz)
        k = torch.rand(kx, ky, kz)

        o3 = fn(x, k)
        o32 = torch.zeros(o3.size())
        fn_2_to_3(x, k, o3, o32)
        self.assertEqual(o3, o32)

    @unittest.skip("Not implemented yet")
    def test_xcorr3_xcorr2_eq(self):
        def reference(x, k, o3, o32):
            for i in range(o3.size(1)):
                for j in range(k.size(1)):
                    o32[i].add(torch.xcorr2(x[i+j-1], k[j]))
        self._test_conv_corr_eq(lambda x, k: torch.xcorr3(x, k), reference)

    @unittest.skip("Not implemented yet")
    def test_xcorr3_xcorr2_eq(self):
        def reference(x, k, o3, o32):
            for i in range(x.size(1)):
                for j in range(k.size(1)):
                    o32[i].add(torch.xcorr2(x[i], k[k.size(1) - j + 1], 'F'))
        self._test_conv_corr_eq(lambda x, k: torch.xcorr3(x, k, 'F'), reference)

    @unittest.skip("Not implemented yet")
    def test_conv3_conv2_eq(self):
        def reference(x, k, o3, o32):
            for i in range(o3.size(1)):
                for j in range(k.size(1)):
                    o32[i].add(torch.conv2(x[i+j-1], k[k.size(1)-j+1]))
        self._test_conv_corr_eq(lambda x, k: torch.conv3(x, k), reference)

    @unittest.skip("Not implemented yet")
    def test_fconv3_fconv2_eq(self):
        def reference(x, k, o3, o32):
            for i in range(o3.size(1)):
                for j in range(k.size(1)):
                    o32[i+j-1].add(torch.conv2(x[i], k[j], 'F'))
        self._test_conv_corr_eq(lambda x, k: torch.conv3(x, k, 'F'), reference)

    def test_logical(self):
        x = torch.rand(100, 100) * 2 - 1;
        xx = x.clone()

        xgt = torch.gt(x, 1)
        xlt = torch.lt(x, 1)

        xeq = torch.eq(x, 1)
        xne = torch.ne(x, 1)

        neqs = xgt + xlt
        all = neqs + xeq
        self.assertEqual(neqs.sum(), xne.sum(), 0)
        self.assertEqual(x.nElement(), all.sum())

    def test_RNGState(self):
        state = torch.getRNGState()
        stateCloned = state.clone()
        before = torch.rand(1000)

        self.assertEqual(state.ne(stateCloned).long().sum(), 0, 0)

        torch.setRNGState(state)
        after = torch.rand(1000)
        self.assertEqual(before, after, 0)

    @unittest.skip("Not implemented yet")
    def test_RNGStateAliasing(self):
        # Fork the random number stream at this point
        gen = torch.Generator()
        torch.setRNGState(gen, torch.getRNGState())

        target_value = torch.rand(1000)
        # Dramatically alter the internal state of the main generator
        _ = torch.rand(100000)
        forked_value = torch.rand(gen, 1000)
        self.assertEqual(target_value, forked_value, 0, "RNG has not forked correctly.")

    def test_boxMullerState(self):
        torch.manualSeed(123)
        odd_number = 101
        seeded = torch.randn(odd_number)
        state = torch.getRNGState()
        midstream = torch.randn(odd_number)
        torch.setRNGState(state)
        repeat_midstream = torch.randn(odd_number)
        torch.manualSeed(123)
        reseeded = torch.randn(odd_number)
        self.assertEqual(midstream, repeat_midstream, 0,
                'getRNGState/setRNGState not generating same sequence of normally distributed numbers')
        self.assertEqual(seeded, reseeded, 0,
                'repeated calls to manualSeed not generating same sequence of normally distributed numbers')

    @unittest.skip("Not implemented yet")
    def test_cholesky(self):
        x = torch.rand(10, 10)
        A = x * x.t()

        # default Case
        C = torch.potrf(A)
        B = C.t() * C
        self.assertEqual(A, B, 1e-14)

        # test Upper Triangular
        U = torch.potrf(A, 'U')
        B = U.t() * U
        self.assertEqual(A, B, 1e-14, 'potrf (upper) did not allow rebuilding the original matrix')

        # test Lower Triangular
        L = torch.potrf(A, 'L')
        B = L * L.t()
        self.assertEqual(A, B, 1e-14, 'potrf (lower) did not allow rebuilding the original matrix')

    @unittest.skipIf(not hasattr(torch, 'potrs'), 'Compiled without potrs')
    def test_potrs(self):
        a=torch.Tensor(((6.80, -2.11,  5.66,  5.97,  8.23),
                        (-6.05, -3.30,  5.36, -4.44,  1.08),
                        (-0.45,  2.58, -2.70,  0.27,  9.04),
                        (8.32,  2.71,  4.35, -7.17,  2.14),
                        (-9.67, -5.14, -7.26,  6.08, -6.87))).t()
        b=torch.Tensor(((4.02,  6.19, -8.22, -7.57, -3.03),
                        (-1.56,  4.00, -8.67,  1.75,  2.86),
                        (9.81, -4.09, -4.57, -8.61,  8.99))).t()

        # make sure 'a' is symmetric PSD
        a = a * a.t()

        # upper Triangular Test
        U = torch.potrf(a, 'U')
        x = torch.potrs(b, U, 'U')
        self.assertLessEqual(b.dist(a * x), 1e-12)

        # lower Triangular Test
        L = torch.potrf(a, 'L')
        x = torch.potrs(b, L, 'L')
        self.assertLessEqual(b.dist(a * x), 1e-12)

    @unittest.skipIf(not hasattr(torch, 'potri'), 'Compiled without potri')
    def tset_potri(self):
        a=torch.Tensor(((6.80, -2.11,  5.66,  5.97,  8.23),
                        (-6.05, -3.30,  5.36, -4.44,  1.08),
                        (-0.45,  2.58, -2.70,  0.27,  9.04),
                        (8.32,  2.71,  4.35, -7.17,  2.14),
                        (-9.67, -5.14, -7.26,  6.08, -6.87))).t()

        # make sure 'a' is symmetric PSD
        a = a * a.t()

        # compute inverse directly
        inv0 = torch.inverse(a)

        # default case
        chol = torch.potrf(a)
        inv1 = torch.potri(chol)
        self.assertLessEqual(inv0.dist(inv1), 1e-12)

        # upper Triangular Test
        chol = torch.potrf(a, 'U')
        inv1 = torch.potri(chol, 'U')
        self.assertLessEqual(inv0.dist(inv1), 1e-12)

        # lower Triangular Test
        chol = torch.potrf(a, 'L')
        inv1 = torch.potri(chol, 'L')
        self.assertLessEqual(inv0.dist(inv1), 1e-12)

    @unittest.skip("Not implemented yet")
    def test_pstrf(self):
        def checkPsdCholesky(a, uplo, inplace):
            if inplace:
                u = torch.Tensor(a.size())
                piv = torch.IntTensor(a.size(0))
                args = [u, piv, a]
            else:
                args = [a]

            if uplo is not None:
                args += [uplo]

            u, piv = torch.pstrf(*args)

            if uplo == 'L':
                a_reconstructed = u * u.t()
            else:
                a_reconstructed = u.t() * u

            piv = piv.long()
            a_permuted = a.index(0, piv-1).index(1, piv-1)
            self.assertTensorEq(a_permuted, a_reconstructed, 1e-14)

        dimensions = ((5, 1), (5, 3), (5, 5), (10, 10))
        for dim in dimensions:
            m = torch.Tensor(*dim).uniform_()
            a = m * m.t()
            # add a small number to the diagonal to make the matrix numerically positive semidefinite
            for i in range(m.size(0)):
                a[i][i] = a[i][i] + 1e-7
            checkPsdCholesky(a, None, False)
            checkPsdCholesky(a, 'U', False)
            checkPsdCholesky(a, 'L', False)
            checkPsdCholesky(a, None, True)
            checkPsdCholesky(a, 'U', True)
            checkPsdCholesky(a, 'L', True)

    def test_numel(self):
        b = torch.ByteTensor(3, 100, 100)
        self.assertEqual(b.nElement(), 3*100*100)
        self.assertEqual(b.numel(), 3*100*100)

    def _consecutive(self, size, start=1):
        sequence = torch.ones(int(torch.Tensor(size).prod(0)[0])).cumsum(0)
        sequence.add_(start - 1)
        return sequence.resize_(*size)

    def test_index(self):
        reference = self._consecutive((3, 3, 3))
        self.assertEqual(reference[0], self._consecutive((3, 3)), 0)
        self.assertEqual(reference[1], self._consecutive((3, 3), 10), 0)
        self.assertEqual(reference[2], self._consecutive((3, 3), 19), 0)
        self.assertEqual(reference[(0,)], self._consecutive((1, 3, 3)), 0)
        self.assertEqual(reference[(1,)], self._consecutive((1, 3, 3), 10), 0)
        self.assertEqual(reference[(2,)], self._consecutive((1, 3, 3), 19), 0)
        self.assertEqual(reference[0, 1], self._consecutive((3,), 4), 0)
        self.assertEqual(reference[0:2], self._consecutive((2, 3, 3)), 0)
        self.assertEqual(reference[2, 2, 2], 27, 0)
        self.assertEqual(reference[:], self._consecutive((3, 3, 3)), 0)

        self.assertRaises(RuntimeError, lambda: reference[1, 1, 1, 1])
        self.assertRaises(RuntimeError, lambda: reference[1, 1, 1, 1:1])
        self.assertRaises(RuntimeError, lambda: reference[3, 3, 3, 3, 3, 3, 3, 3])

    def test_newindex(self):
        reference = self._consecutive((3, 3, 3))
        # This relies on __index__() being correct - but we have separate tests for that
        def checkPartialAssign(index):
            reference = torch.zeros(3, 3, 3)
            reference[index] = self._consecutive((3, 3, 3))[index]
            self.assertEqual(reference[index], self._consecutive((3, 3, 3))[index], 0)
            reference[index] = 0
            self.assertEqual(reference, torch.zeros(3, 3, 3), 0)

        checkPartialAssign(0)
        checkPartialAssign(1)
        checkPartialAssign(2)
        checkPartialAssign((0, 1))
        checkPartialAssign((1, 2))
        checkPartialAssign((0, 2))

        with self.assertRaises(RuntimeError):
            reference[1, 1, 1, 1] = 1
        with self.assertRaises(RuntimeError):
            reference[1, 1, 1, (1, 1)] = 1
        with self.assertRaises(RuntimeError):
            reference[3, 3, 3, 3, 3, 3, 3, 3] = 1

    def test_indexCopy(self):
        num_copy, num_dest = 3, 20
        dest = torch.randn(num_dest, 4, 5)
        src = torch.randn(num_copy, 4, 5)
        idx = torch.randperm(num_dest).narrow(0, 0, num_copy).long()
        dest2 = dest.clone()
        dest.indexCopy_(0, idx, src)
        for i in range(idx.size(0)):
            dest2[idx[i]].copy_(src[i])
        self.assertEqual(dest, dest2, 0)

        dest = torch.randn(num_dest)
        src = torch.randn(num_copy)
        idx = torch.randperm(num_dest).narrow(0, 0, num_copy).long()
        dest2 = dest.clone()
        dest.indexCopy_(0, idx, src)
        for i in range(idx.size(0)):
            dest2[idx[i]] = src[i]
        self.assertEqual(dest, dest2, 0)

    def test_indexAdd(self):
        num_copy, num_dest = 3, 3
        dest = torch.randn(num_dest, 4, 5)
        src = torch.randn(num_copy, 4, 5)
        idx = torch.randperm(num_dest).narrow(0, 0, num_copy).long()
        dest2 = dest.clone()
        dest.indexAdd_(0, idx, src)
        for i in range(idx.size(0)):
            dest2[idx[i]].add_(src[i])
        self.assertEqual(dest, dest2)

        dest = torch.randn(num_dest)
        src = torch.randn(num_copy)
        idx = torch.randperm(num_dest).narrow(0, 0, num_copy).long()
        dest2 = dest.clone()
        dest.indexAdd_(0, idx, src)
        for i in range(idx.size(0)):
            dest2[idx[i]] = dest2[idx[i]] + src[i]
        self.assertEqual(dest, dest2)

    # Fill idx with valid indices.
    def _fill_indices(self, idx, dim, dim_size, elems_per_row, m, n, o):
        for i in range(1 if dim == 0 else m):
            for j in range(1 if dim == 1 else n):
                for k in range(1 if dim == 2 else o):
                    ii = [i, j, k]
                    ii[dim] = (0, idx.size(dim))
                    idx[tuple(ii)] = torch.randperm(dim_size)[1:elems_per_row+1]

    def test_gather(self):
        m, n, o = random.randint(10, 20), random.randint(10, 20), random.randint(10, 20)
        elems_per_row = random.randint(1, 10)
        dim = random.randrange(3)

        src = torch.randn(m, n, o)
        idx_size = [m, n, o]
        idx_size[dim] = elems_per_row
        idx = torch.LongTensor().resize_(*idx_size)
        self._fill_indices(idx, dim, src.size(dim), elems_per_row, m, n, o)

        actual = torch.gather(src, dim, idx)
        expected = torch.Tensor().resize_(*idx_size)
        for i in range(idx_size[0]):
            for j in range(idx_size[1]):
                for k in range(idx_size[2]):
                    ii = [i, j, k]
                    ii[dim] = idx[i,j,k]
                    expected[i,j,k] = src[tuple(ii)]
        self.assertEqual(actual, expected, 0)

        idx[0][0][0] = 23
        self.assertRaises(RuntimeError, lambda: torch.gather(src, dim, idx))

        src = torch.randn(3, 4, 5)
        expected, idx = src.max(2)
        actual = torch.gather(src, 2, idx)
        self.assertEqual(actual, expected, 0)

    def test_scatter(self):
        m, n, o = random.randint(10, 20), random.randint(10, 20), random.randint(10, 20)
        elems_per_row = random.randint(1, 10)
        dim = random.randrange(3)

        idx_size = [m, n, o]
        idx_size[dim] = elems_per_row
        idx = torch.LongTensor().resize_(*idx_size)
        self._fill_indices(idx, dim, ([m, n, o])[dim], elems_per_row, m, n, o)
        src = torch.Tensor().resize_(*idx_size).normal_()

        actual = torch.zeros(m, n, o).scatter_(dim, idx, src)
        expected = torch.zeros(m, n, o)
        for i in range(idx_size[0]):
            for j in range(idx_size[1]):
                for k in range(idx_size[2]):
                    ii = [i, j, k]
                    ii[dim] = idx[i,j,k]
                    expected[tuple(ii)] = src[i,j,k]
        self.assertEqual(actual, expected, 0)

        idx[0][0][0] = 34
        self.assertRaises(RuntimeError, lambda: torch.zeros(m, n, o).scatter_(dim, idx, src))

    def test_scatterFill(self):
        m, n, o = random.randint(10, 20), random.randint(10, 20), random.randint(10, 20)
        elems_per_row = random.randint(1, 10)
        dim = random.randrange(3)

        val = random.random()
        idx_size = [m, n, o]
        idx_size[dim] = elems_per_row
        idx = torch.LongTensor().resize_(*idx_size)
        self._fill_indices(idx, dim, ([m, n, o])[dim], elems_per_row, m, n, o)

        actual = torch.zeros(m, n, o).scatter_(dim, idx, val)
        expected = torch.zeros(m, n, o)
        for i in range(idx_size[0]):
            for j in range(idx_size[1]):
                for k in range(idx_size[2]):
                    ii = [i, j, k]
                    ii[dim] = idx[i,j,k]
                    expected[tuple(ii)] = val
        self.assertEqual(actual, expected, 0)

        idx[0][0][0] = 28
        self.assertRaises(RuntimeError, lambda: torch.zeros(m, n, o).scatter_(dim, idx, val))

    def test_maskedCopy(self):
        num_copy, num_dest = 3, 10
        dest = torch.randn(num_dest)
        src = torch.randn(num_copy)
        mask = torch.ByteTensor((0, 0, 0, 0, 1, 0, 1, 0, 1, 0))
        dest2 = dest.clone()
        dest.maskedCopy_(mask, src)
        j = 0
        for i in range(num_dest):
            if mask[i]:
                dest2[i] = src[j]
                j += 1
        self.assertEqual(dest, dest2, 0)

        # make source bigger than number of 1s in mask
        src = torch.randn(num_dest)
        dest.maskedCopy_(mask, src)

        # make src smaller. this should fail
        src = torch.randn(num_copy - 1)
        with self.assertRaises(RuntimeError):
            dest.maskedCopy_(mask, src)

    def test_maskedSelect(self):
        num_src = 10
        src = torch.randn(num_src)
        mask = torch.rand(num_src).mul(2).floor().byte()
        dst = src.maskedSelect(mask)
        dst2 = []
        for i in range(num_src):
            if mask[i]:
                dst2 += [src[i]]
        self.assertEqual(dst, torch.Tensor(dst2), 0)

    def test_maskedFill(self):
        num_dest = 10
        dst = torch.randn(num_dest)
        mask = torch.rand(num_dest).mul(2).floor().byte()
        val = random.random()
        dst2 = dst.clone()
        dst.maskedFill_(mask, val)
        for i in range(num_dest):
            if mask[i]:
                dst2[i] = val
        self.assertEqual(dst, dst2, 0)

    def test_abs(self):
        size = 1000
        max_val = 1000
        original = torch.rand(size).mul(max_val)
        # Tensor filled with values from {-1, 1}
        switch = torch.rand(size).mul(2).floor().mul(2).add(-1)

        types = ['torch.DoubleTensor', 'torch.FloatTensor', 'torch.LongTensor', 'torch.IntTensor']
        for t in types:
            data = original.type(t)
            switch = switch.type(t)
            res = torch.mul(data, switch)
            self.assertEqual(res.abs(), data, 1e-16)

        # Checking that the right abs function is called for LongTensor
        bignumber = 2^31 + 1
        res = torch.LongTensor((-bignumber,))
        self.assertGreater(res.abs()[0], 0)

    def test_view(self):
        tensor = torch.rand(15)
        template = torch.rand(3, 5)
        target = template.size().tolist()
        self.assertEqual(tensor.viewAs(template).size().tolist(), target)
        self.assertEqual(tensor.view(3, 5).size().tolist(), target)
        self.assertEqual(tensor.view(torch.LongStorage((3, 5))).size().tolist(), target)
        self.assertEqual(tensor.view(-1, 5).size().tolist(), target)
        self.assertEqual(tensor.view(3, -1).size().tolist(), target)
        tensor_view = tensor.view(5, 3)
        tensor_view.fill_(random.uniform(0, 1))
        self.assertEqual((tensor_view-tensor).abs().max(), 0)

    def test_expand(self):
        result = torch.Tensor()
        tensor = torch.rand(8, 1)
        template = torch.rand(8, 5)
        target = template.size().tolist()
        self.assertEqual(tensor.expandAs(template).size().tolist(), target)
        self.assertEqual(tensor.expand(8, 5).size().tolist(), target)
        self.assertEqual(tensor.expand(torch.LongStorage((8, 5))).size().tolist(), target)

    def test_repeatTensor(self):
        result = torch.Tensor()
        tensor = torch.rand(8, 4)
        size = (3, 1, 1)
        sizeStorage = torch.LongStorage(size)
        target = [3, 8, 4]
        self.assertEqual(tensor.repeatTensor(*size).size().tolist(), target, 'Error in repeatTensor')
        self.assertEqual(tensor.repeatTensor(sizeStorage).size().tolist(), target, 'Error in repeatTensor using LongStorage')
        result = tensor.repeatTensor(*size)
        self.assertEqual(result.size().tolist(), target, 'Error in repeatTensor using result')
        result = tensor.repeatTensor(sizeStorage)
        self.assertEqual(result.size().tolist(), target, 'Error in repeatTensor using result and LongStorage')
        self.assertEqual((result.mean(0).view(8, 4)-tensor).abs().max(), 0, 'Error in repeatTensor (not equal)')

    def test_isSameSizeAs(self):
        t1 = torch.Tensor(3, 4, 9, 10)
        t2 = torch.Tensor(3, 4)
        t3 = torch.Tensor(1, 9, 3, 3)
        t4 = torch.Tensor(3, 4, 9, 10)

        self.assertFalse(t1.isSameSizeAs(t2))
        self.assertFalse(t1.isSameSizeAs(t3))
        self.assertTrue(t1.isSameSizeAs(t4))

    def test_isSetTo(self):
        t1 = torch.Tensor(3, 4, 9, 10)
        t2 = torch.Tensor(3, 4, 9, 10)
        t3 = torch.Tensor().set_(t1)
        t4 = t3.clone().resize_(12, 90)
        self.assertFalse(t1.isSetTo(t2))
        self.assertTrue(t1.isSetTo(t3))
        self.assertTrue(t3.isSetTo(t1), "isSetTo should be symmetric")
        self.assertFalse(t1.isSetTo(t4))
        self.assertFalse(torch.Tensor().isSetTo(torch.Tensor()),
                "Tensors with no storages should not appear to be set "
                "to each other")

    def test_equal(self):
        # Contiguous, 1D
        t1 = torch.Tensor((3, 4, 9, 10))
        t2 = t1.contiguous()
        t3 = torch.Tensor((1, 9, 3, 10))
        t4 = torch.Tensor((3, 4, 9))
        t5 = torch.Tensor()
        self.assertTrue(t1.equal(t2))
        self.assertFalse(t1.equal(t3))
        self.assertFalse(t1.equal(t4))
        self.assertFalse(t1.equal(t5))
        self.assertTrue(torch.equal(t1, t2))
        self.assertFalse(torch.equal(t1, t3))
        self.assertFalse(torch.equal(t1, t4))
        self.assertFalse(torch.equal(t1, t5))

        # Non contiguous, 2D
        s = torch.Tensor(((1, 2, 3, 4), (5, 6, 7, 8)))
        s1 = s[:,1:3]
        s2 = s1.clone()
        s3 = torch.Tensor(((2, 3), (6, 7)))
        s4 = torch.Tensor(((0, 0), (0, 0)))

        self.assertFalse(s1.isContiguous())
        self.assertTrue(s1.equal(s2))
        self.assertTrue(s1.equal(s3))
        self.assertFalse(s1.equal(s4))
        self.assertTrue(torch.equal(s1, s2))
        self.assertTrue(torch.equal(s1, s3))
        self.assertFalse(torch.equal(s1, s4))

    def test_isSize(self):
        t1 = torch.Tensor(3, 4, 5)
        s1 = torch.LongStorage((3, 4, 5))
        s2 = torch.LongStorage((5, 4, 3))

        self.assertTrue(t1.isSize(s1))
        self.assertFalse(t1.isSize(s2))
        self.assertTrue(t1.isSize(t1.size()))

    def test_elementSize(self):
        byte   =   torch.ByteStorage().elementSize()
        char   =   torch.CharStorage().elementSize()
        short  =  torch.ShortStorage().elementSize()
        int    =    torch.IntStorage().elementSize()
        long   =   torch.LongStorage().elementSize()
        float  =  torch.FloatStorage().elementSize()
        double = torch.DoubleStorage().elementSize()

        self.assertEqual(byte,   torch.ByteTensor().elementSize())
        self.assertEqual(char,   torch.CharTensor().elementSize())
        self.assertEqual(short,  torch.ShortTensor().elementSize())
        self.assertEqual(int,    torch.IntTensor().elementSize())
        self.assertEqual(long,   torch.LongTensor().elementSize())
        self.assertEqual(float,  torch.FloatTensor().elementSize())
        self.assertEqual(double, torch.DoubleTensor().elementSize())

        self.assertGreater(byte, 0)
        self.assertGreater(char, 0)
        self.assertGreater(short, 0)
        self.assertGreater(int, 0)
        self.assertGreater(long, 0)
        self.assertGreater(float, 0)
        self.assertGreater(double, 0)

        # These tests are portable, not necessarily strict for your system.
        self.assertEqual(byte, 1)
        self.assertEqual(char, 1)
        self.assertGreaterEqual(short, 2)
        self.assertGreaterEqual(int, 2)
        self.assertGreaterEqual(int, short)
        self.assertGreaterEqual(long, 4)
        self.assertGreaterEqual(long, int)
        self.assertGreaterEqual(double, float)

    def test_split(self):
        tensor = torch.rand(7, 4)
        split_size = 3
        dim = 0
        target_sizes = ([3, 4], [3, 4], [1, 4])
        splits = tensor.split(split_size, dim)
        start = 0
        for target_size, split in zip(target_sizes, splits):
            self.assertEqual(split.size().tolist(), target_size)
            self.assertEqual(tensor.narrow(dim, start, target_size[dim]), split, 0)
            start = start + target_size[dim]

    def test_chunk(self):
        tensor = torch.rand(4, 7)
        num_chunks = 3
        dim = 1
        target_sizes = ([4, 3], [4, 3], [4, 1])
        splits = tensor.chunk(num_chunks, dim)
        start = 0
        for target_size, split in zip(target_sizes, splits):
            self.assertEqual(split.size().tolist(), target_size)
            self.assertEqual(tensor.narrow(dim, start, target_size[dim]), split, 0)
            start = start + target_size[dim]

    def test_tolist(self):
        list0D = []
        tensor0D = torch.Tensor(list0D)
        self.assertEqual(tensor0D.tolist(), list0D)

        table1D = [1, 2, 3]
        tensor1D = torch.Tensor(table1D)
        storage = torch.Storage(table1D)
        self.assertEqual(tensor1D.tolist(), table1D)
        self.assertEqual(storage.tolist(), table1D)
        self.assertEqual(tensor1D.tolist(), table1D)
        self.assertEqual(storage.tolist(), table1D)

        table2D = [[1, 2], [3, 4]]
        tensor2D = torch.Tensor(table2D)
        self.assertEqual(tensor2D.tolist(), table2D)

        tensor3D = torch.Tensor([[[1, 2], [3, 4]], [[5, 6], [7, 8]]])
        tensorNonContig = tensor3D.select(1, 1)
        self.assertFalse(tensorNonContig.isContiguous())
        self.assertEqual(tensorNonContig.tolist(), [[3, 4], [7, 8]])

    def test_permute(self):
        orig = [1, 2, 3, 4, 5, 6, 7]
        perm = list(torch.randperm(7).long())
        x = torch.Tensor(*orig).fill_(0)
        new = list(map(lambda x: x - 1, x.permute(*perm).size()))
        self.assertEqual(perm, new)
        self.assertEqual(x.size().tolist(), orig)

    def test_storageview(self):
        s1 = torch.LongStorage((3, 4, 5))
        s2 = torch.LongStorage(s1, 1)

        self.assertEqual(s2.size(), 2)
        self.assertEqual(s2[0], s1[1])
        self.assertEqual(s2[1], s1[2])

        s2[1] = 13
        self.assertEqual(13, s1[2])

    def test_nonzero(self):
        num_src = 12

        types = [
            'torch.ByteTensor',
            'torch.CharTensor',
            'torch.ShortTensor',
            'torch.IntTensor',
            'torch.FloatTensor',
            'torch.DoubleTensor',
            'torch.LongTensor',
        ]

        shapes = [
            torch.LongStorage((12,)),
            torch.LongStorage((12, 1)),
            torch.LongStorage((1, 12)),
            torch.LongStorage((6, 2)),
            torch.LongStorage((3, 2, 2)),
        ]

        for t in types:
            tensor = torch.rand(num_src).mul(2).floor().type(t)
            for shape in shapes:
                tensor = tensor.clone().resize_(shape)
                dst1 = torch.nonzero(tensor)
                dst2 = tensor.nonzero()
                dst3 = torch.LongTensor()
                torch.nonzero(dst3, tensor)
                if shape.size() == 1:
                    dst = []
                    for i in range(num_src):
                        if tensor[i] != 0:
                            dst += [i]

                    self.assertEqual(dst1.select(1, 0), torch.LongTensor(dst), 0)
                    self.assertEqual(dst2.select(1, 0), torch.LongTensor(dst), 0)
                    self.assertEqual(dst3.select(1, 0), torch.LongTensor(dst), 0)
                elif shape.size() == 2:
                    # This test will allow through some False positives. It only checks
                    # that the elements flagged positive are indeed non-zero.
                    for i in range(dst1.size(0)):
                        self.assertNotEqual(tensor[dst1[i,0], dst1[i,1]], 0)
                elif shape.size() == 3:
                # This test will allow through some False positives. It only checks
                # that the elements flagged positive are indeed non-zero.
                    for i in range(dst1.size(0)):
                        self.assertNotEqual(tensor[dst1[i,0], dst1[i,1], dst1[i,2]], 0)

    def test_deepcopy(self):
        from copy import deepcopy
        a = torch.randn(5, 5)
        b = torch.randn(5, 5)
        c = a.view(25)
        q = [a, [a.storage(), b.storage()], b, c]
        w = deepcopy(q)
        self.assertEqual(w[0], q[0], 0)
        self.assertEqual(w[1][0], q[1][0], 0)
        self.assertEqual(w[1][1], q[1][1], 0)
        self.assertEqual(w[1], q[1], 0)
        self.assertEqual(w[2], q[2], 0)

        # Check that deepcopy preserves sharing
        w[0].add_(1)
        for i in range(a.numel()):
            self.assertEqual(w[1][0][i], q[1][0][i] + 1)
        self.assertEqual(w[3], c + 1)
        w[2].sub_(1)
        for i in range(a.numel()):
            self.assertEqual(w[1][1][i], q[1][1][i] - 1)

    def test_copy(self):
        from copy import copy
        a = torch.randn(5, 5)
        a_clone = a.clone()
        b = copy(a)
        b.fill_(1)
        self.assertEqual(a, a_clone)

    def test_pickle(self):
        if sys.version_info[0] == 2:
            import cPickle as pickle
        else:
            import pickle
        a = torch.randn(5, 5)
        serialized = pickle.dumps(a)
        b = pickle.loads(serialized)
        self.assertEqual(a, b)

    def test_bernoulli(self):
        t = torch.ByteTensor(10, 10)

        def isBinary(t):
            return torch.ne(t, 0).mul_(torch.ne(t, 1)).sum() == 0

        p = 0.5
        t.bernoulli_(p)
        self.assertTrue(isBinary(t))

        p = torch.rand(SIZE)
        t.bernoulli_(p)
        self.assertTrue(isBinary(t))

    def test_serialization(self):
        a = [torch.randn(5, 5).float() for i in range(2)]
        b = [a[i % 2] for i in range(4)] + [a[0].storage()]
        with tempfile.NamedTemporaryFile() as f:
            torch.save(b, f)
            f.seek(0)
            c = torch.load(f)
        self.assertEqual(b, c, 0)
        self.assertTrue(isinstance(c[0], torch.FloatTensor))
        self.assertTrue(isinstance(c[1], torch.FloatTensor))
        self.assertTrue(isinstance(c[2], torch.FloatTensor))
        self.assertTrue(isinstance(c[3], torch.FloatTensor))
        self.assertTrue(isinstance(c[4], torch.FloatStorage))
        c[0].fill_(10)
        self.assertEqual(c[0], c[2], 0)
        self.assertEqual(c[4], torch.FloatStorage(25).fill_(10), 0)
        c[1].fill_(20)
        self.assertEqual(c[1], c[3], 0)

if __name__ == '__main__':
    unittest.main()
