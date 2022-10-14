import math
import random
import unittest
from copy import deepcopy

import torch
import torch.legacy.nn as nn
from common_nn import NNTestCase, ModuleTest, CriterionTest, iter_tensors, module_tests, criterion_tests, TEST_CUDA, PRECISION
from common import to_gpu

class OldModuleTest(ModuleTest):
    def __init__(self, *args, **kwargs):
        super(OldModuleTest, self).__init__(*args, **kwargs)
        self.check_inplace = kwargs.get('check_inplace', False)

    def _do_test(self, test_case, module, input):
        # TODO: check update parameters
        # TODO: test IO
        module.training()
        test_case.check_jacobian(module, input, self.jacobian_input)
        module.evaluate()
        test_case.check_jacobian(module, input, self.jacobian_input)

        # Test .type()
        module.float().double().forward(input)

        # Test .clearState()
        module.clearState()

        if self.check_inplace:
            input2 = deepcopy(input)
            module_ip = self.constructor(*self.constructor_args, inplace=True)
            output = module.forward(input)
            test_case.assertEqual(input, input2)
            output2 = module_ip.forward(input2)
            test_case.assertNotEqual(input, input2)
            test_case.assertEqual(output, input2)

# TODO: hessian tests
tests = [
    OldModuleTest(nn.Add,
                    (torch.LongStorage([5, 4]),),
                    input_size=(3, 5, 4),
                    desc='3D'),
    OldModuleTest(nn.Add,
                    (1, True),
                    input_size=(3, 1, 4),
                    desc='scalar'),
    OldModuleTest(nn.AddConstant,
                    (3.5,),
                    input_size=(3, 5, 4),
                    reference_fn=lambda i,_: i + 3.5,
                    check_inplace=True),
    OldModuleTest(nn.CMul,
                    (5, 6),
                    input_size=(10, 5, 6),
                    desc='3D'),
    OldModuleTest(nn.CMul,
                    (50, 4),
                    input_size=(1, 50, 4),
                    desc='3D_single_example'),
    OldModuleTest(nn.CMul,
                    (1, 5),
                    input=torch.randn(10, 3, 5)[:,1],
                    desc='3D_noncontiguous'),
    OldModuleTest(nn.Exp,
                    input_size=(2, 3, 4),
                    reference_fn=lambda i,_: i.exp()),
    OldModuleTest(nn.Log,
                    input=torch.rand(2, 3, 2) + 0.1,
                    reference_fn=lambda i,_: i.log()),
    OldModuleTest(nn.LogSigmoid,
                    input_size=(2, 3, 4),
                    reference_fn=lambda i,_: i.sigmoid().log()),
    OldModuleTest(nn.SoftMin,
                    input_size=(10, 20)),
    OldModuleTest(nn.SoftPlus,
                    input_size=(10, 20),
                    reference_fn=lambda i,_: torch.log(1 + torch.exp(i))),
    OldModuleTest(nn.SoftPlus,
                    (2,),
                    input_size=(10, 20),
                    reference_fn=lambda i,_: 1. / 2. * torch.log(1 + torch.exp(2 * i)),
                    desc='beta'),
    OldModuleTest(nn.Clamp,
                    (-2., 5.),
                    input=torch.randn(3, 2, 50) * 6,
                    reference_fn=lambda i,_: i.clamp(-2, 5)),
    OldModuleTest(nn.Abs,
                    input_size=(3, 20, 5),
                    reference_fn=lambda i,_: i.abs()),
    OldModuleTest(nn.ELU,
                    (2.,),
                    input_size=(3, 2, 5),
                    check_inplace=True),
    # TODO implement
    # OldModuleTest(nn.RReLU,
                    # input_size=(4, 2, 5),
                    # check_inplace=True),
    # OldModuleTest(nn.RReLU,
                    # (0.1, 0.9),
                    # input_size=(4, 4, 5),
                    # check_inplace=True,
                    # desc='with_up_down'),
    OldModuleTest(nn.SoftShrink,
                    input_size=(3, 2, 5)),
    OldModuleTest(nn.SoftShrink,
                    (1,),
                    input_size=(3, 2, 5),
                    desc='lambda'),
    OldModuleTest(nn.SoftSign,
                    input_size=(3, 2, 5),
                    reference_fn=lambda i,_: i.div(1 + torch.abs(i))),
    OldModuleTest(nn.LeakyReLU,
                    input_size=(3, 2, 5),
                    check_inplace=True),
    OldModuleTest(nn.LeakyReLU,
                    (0.5,),
                    input_size=(3, 2, 5),
                    check_inplace=True,
                    desc='with_negval'),
    OldModuleTest(nn.Bilinear,
                    (2, 3, 10),
                    input_size=[(4, 2), (4, 3)]),
    OldModuleTest(nn.Bilinear,
                    (5, 4, 2),
                    input_size=[(2, 5), (2, 4)],
                    desc='small_output'),
    OldModuleTest(nn.Euclidean,
                    (5, 7),
                    input_size=(10, 5)),
    OldModuleTest(nn.WeightedEuclidean,
                    (5, 7),
                    input_size=(10, 5)),
    OldModuleTest(nn.Cosine,
                    (5, 7),
                    input_size=(10, 5)),
    OldModuleTest(nn.CAddTable,
                    input_size=[(5, 7), (5, 7)]),
    OldModuleTest(nn.CSubTable,
                    input_size=[(5, 7), (5, 7)]),
    OldModuleTest(nn.CDivTable,
                    input=[torch.randn(1, 7), torch.rand(1, 7) + 0.1]),
    OldModuleTest(nn.CMulTable,
                    input_size=[(5, 7), (5, 7)]),
    OldModuleTest(nn.Square,
                    input_size=(10, 2, 4),
                    reference_fn=lambda i,_: i.mul(i)),
    OldModuleTest(nn.Sqrt,
                    input=torch.rand(10, 2, 4)+0.01,
                    reference_fn=lambda i,_: i.sqrt()),
    OldModuleTest(nn.Squeeze,
                    input_size=(2, 1, 1, 4, 5),
                    reference_fn=lambda i,_: i.squeeze()),
    # TODO: should squeeze work inplace?
    # OldModuleTest(nn.Squeeze,
                    # (1,),
                    # input_size=(2, 1, 1, 4, 5),
                    # reference_fn=lambda i,_: i.squeeze(1),
                    # desc='dim'),
    OldModuleTest(nn.Unsqueeze,
                    (1,),
                    input_size=(2, 4, 5),
                    reference_fn=lambda i,_: i.view(2, 1, 4, 5)),
    OldModuleTest(nn.Unsqueeze,
                    (0,),
                    input_size=(2, 4, 5),
                    reference_fn=lambda i,_: i.view(1, 2, 4, 5),
                    desc='fist_dim'),
    OldModuleTest(nn.Unsqueeze,
                    (3,),
                    input_size=(2, 4, 5),
                    reference_fn=lambda i,_: i.view(2, 4, 5, 1),
                    desc='last_dim'),
    OldModuleTest(nn.View,
                    (-1, 2, 20),
                    input_size=(2, 2, 4, 5),
                    reference_fn=lambda i,_: i.view(-1, 2, 20),
                    desc='infer_batch'),
    OldModuleTest(nn.View,
                    (2, 2, 2, 5),
                    input_size=(2, 4, 5),
                    reference_fn=lambda i,_: i.view(2, 2, 2, 5),
                    desc='split_dim'),
    OldModuleTest(nn.View,
                    (2, -1, 2, 5),
                    input_size=(2, 4, 5),
                    reference_fn=lambda i,_: i.view(2, -1, 2, 5),
                    desc='infer_middle'),
    OldModuleTest(nn.Sum,
                    (1,),
                    input_size=(2, 4, 5),
                    reference_fn=lambda i,_: i.sum(1)),
    OldModuleTest(nn.Sum,
                    (1, True),
                    input_size=(2, 4, 5),
                    reference_fn=lambda i,_: i.sum(1).div(i.size(1)),
                    desc='sizeAverage'),
    OldModuleTest(nn.Mean,
                    (1,),
                    input_size=(2, 4, 5),
                    reference_fn=lambda i,_: torch.mean(i, 1)),
    # TODO: reference function
    OldModuleTest(nn.HardShrink,
                    (2.,),
                    input_size=(4, 3, 2, 4)),
    OldModuleTest(lambda: nn.Sequential().add(nn.GradientReversal()).add(nn.GradientReversal()),
                    input_size=(4, 3, 2, 2),
                    fullname='GradientReversal'),
    OldModuleTest(nn.Identity,
                    input_size=(4, 3, 2, 4),
                    reference_fn=lambda i,_: i),
    OldModuleTest(nn.DotProduct,
                    input_size=[(10, 4), (10, 4)],
                    reference_fn=lambda i,_: torch.Tensor(list(
                        a.dot(b) for a, b in zip(i[0], i[1])))
                    ),
    OldModuleTest(nn.CosineDistance,
                    input_size=[(10, 4), (10, 4)],
                    reference_fn=lambda i,_: torch.Tensor(list(
                        a.dot(b) / (a.norm(2) * b.norm(2)) for a, b in zip(i[0], i[1])))
                    ),
    OldModuleTest(nn.JoinTable,
                    (0,),
                    input_size=[(10, 4), (10, 4)],
                    reference_fn=lambda i,_: torch.cat(i, 0),
                    desc='first_dim'),
    OldModuleTest(nn.JoinTable,
                    (2,),
                    input_size=[(2, 4, 2), (2, 4, 2)],
                    reference_fn=lambda i,_: torch.cat(i, 2),
                    desc='positive_dim_index'),
    OldModuleTest(nn.JoinTable,
                    (-1,),
                    input_size=[(2, 4, 2, 4), (2, 4, 2, 4)],
                    reference_fn=lambda i,_: torch.cat(i, 3),
                    desc='negative_dim_index'),
    OldModuleTest(nn.MM,
                    input_size=[(4, 5, 3), (4, 3, 2)],
                    reference_fn=lambda i,_: torch.bmm(*i)),
    OldModuleTest(nn.MV,
                    input_size=[(4, 5, 3), (4, 3)],
                    reference_fn=lambda i,_: torch.bmm(i[0], i[1].view(i[1].size(0), i[1].size(1), 1)).squeeze()),
    OldModuleTest(nn.Max,
                    input_size=(4, 5, 3),
                    reference_fn=lambda i,_: torch.max(i, 0)[0].squeeze()),
    OldModuleTest(nn.Max,
                    (1,),
                    input_size=(4, 5, 3),
                    reference_fn=lambda i,_: torch.max(i, 1)[0].squeeze(),
                    desc='with_dimension'),
    OldModuleTest(nn.Min,
                    input_size=(4, 5, 3),
                    reference_fn=lambda i,_: torch.min(i, 0)[0].squeeze()),
    OldModuleTest(nn.Min,
                    (1,),
                    input_size=(4, 5, 3),
                    reference_fn=lambda i,_: torch.min(i, 1)[0].squeeze(),
                    desc='with_dimension'),
    OldModuleTest(nn.MixtureTable,
                    tuple(),
                    input_size=[(5, 3), (5, 3, 6)]),
    OldModuleTest(nn.LookupTable,
                    (4, 3),
                    input=torch.randperm(2).repeatTensor(1, 2),
                    jacobian_input=False),
    OldModuleTest(nn.Mul,
                    input_size=(2, 3, 4, 2),
                    reference_fn=lambda i,p: i * p[0][0]),
    OldModuleTest(nn.MulConstant,
                    (4,),
                    input_size=(2, 3, 4, 2),
                    reference_fn=lambda i,_: i * 4,
                    check_inplace=True),
    OldModuleTest(nn.Narrow,
                    (0, 0),
                    input_size=(2, 3, 4, 2),
                    reference_fn=lambda i,_: i.narrow(0, 0, 1)),
    OldModuleTest(nn.Narrow,
                    (1, 1, 2),
                    input_size=(2, 3, 4, 2),
                    reference_fn=lambda i,_: i.narrow(1, 1, 2),
                    desc='length'),
    OldModuleTest(nn.PReLU,
                    input_size=(2, 3, 4, 5)),
    OldModuleTest(nn.PReLU,
                    (3,),
                    input_size=(2, 3, 4, 5),
                    desc='multiparam'),
    OldModuleTest(nn.TanhShrink,
                    input_size=(2, 3, 4, 5)),
    OldModuleTest(nn.Transpose,
                    ((1, 2), (1, 3)),
                    input_size=(2, 3, 4, 5),
                    reference_fn=lambda i,_: i.transpose(1, 2).transpose(1, 3)),
    OldModuleTest(nn.Transpose,
                    ((1, 2),),
                    input_size=(2, 3, 4, 5),
                    reference_fn=lambda i,_: i.transpose(1, 2),
                    desc='single_arg'),
    # TODO: this seems to be very slow
    OldModuleTest(nn.Replicate,
                    (2, 1),
                    input_size=(10, 3, 4, 5),
                    reference_fn=lambda i,_: i.view(10, 1, 3, 4, 5).expand(10, 2, 3, 4, 5)),
    OldModuleTest(nn.Padding,
                    (0, 2, -10),
                    input_size=(2, 3, 4, 5)),
    OldModuleTest(nn.Padding,
                    (0, 2, -10, 1),
                    input_size=(2, 3, 4, 5),
                    desc='index'),
    OldModuleTest(nn.Padding,
                    (0, -2, -10, 1),
                    input_size=(2, 3, 4, 5),
                    desc='negative_pad'),
    OldModuleTest(nn.PartialLinear,
                    (5, 6),
                    input_size=(4, 5)),
    OldModuleTest(lambda: nn.PartialLinear(5, 6).setPartition(torch.Tensor((2, 4))),
                    input_size=(4, 5),
                    fullname='PartialLinear_setPartition'),
    OldModuleTest(nn.Power,
                    (2,),
                    input_size=(2, 3, 4, 5)),
    OldModuleTest(nn.Power,
                    (1.5,),
                    input=torch.rand(3, 4, 5),
                    desc='fractional'),
    OldModuleTest(nn.Reshape,
                    (4, 5),
                    input_size=(3, 4*5),
                    desc='add_dim'),
    OldModuleTest(nn.Reshape,
                    (4*5,),
                    input_size=(3, 4, 5),
                    desc='squash_dim'),
    OldModuleTest(nn.Select,
                    (1, 2),
                    input_size=(3, 4, 5),
                    reference_fn=lambda i,_: i.select(1, 2)),
    OldModuleTest(nn.SelectTable,
                    (1,),
                    input_size=[(1,), (2,), (3,), (4,)],
                    reference_fn=lambda i,_: i[1]),
    OldModuleTest(nn.SpatialAdaptiveMaxPooling,
                    (4, 4),
                    input_size=(2, 3, 8, 8)),
    OldModuleTest(nn.SpatialAdaptiveMaxPooling,
                    (4, 4),
                    input_size=(2, 3, 7, 11),
                    desc='irregular'),
                    # TODO: enable after implementing MaxPooling
                    # reference_fn=lambda i,_: nn.SpatialMaxPooling(2, 2).forward(i)),
    OldModuleTest(nn.SpatialAveragePooling,
                    (2, 2),
                    input_size=(2, 3, 6, 6)),
    OldModuleTest(nn.SpatialAveragePooling,
                    (2, 2, 2, 2),
                    input_size=(2, 3, 6, 6),
                    desc='stride'),
    OldModuleTest(nn.SpatialAveragePooling,
                    (2, 2, 2, 2, 1, 1),
                    input_size=(2, 3, 6, 6),
                    desc='stride_pad'),
    OldModuleTest(nn.SpatialBatchNormalization,
                    (3,),
                    input_size=(2, 3, 6, 6)),
    OldModuleTest(nn.SpatialBatchNormalization,
                    (3, 1e-3, 0.8),
                    input_size=(2, 3, 6, 6),
                    desc='momentum'),
    OldModuleTest(nn.SpatialBatchNormalization,
                    (3, 1e-3, 0.8, False),
                    input_size=(2, 3, 6, 6),
                    desc='no_affine'),
    OldModuleTest(nn.SpatialConvolutionLocal,
                    (3, 2, 4, 4, 2, 2),
                    input_size=(1, 3, 4, 4)),
    OldModuleTest(nn.SpatialConvolutionLocal,
                    (3, 2, 6, 6, 2, 2, 2, 2),
                    input_size=(2, 3, 6, 6),
                    desc='stride'),
    OldModuleTest(nn.SpatialConvolutionLocal,
                    (3, 2, 6, 6, 2, 2, 2, 2, 1, 1),
                    input_size=(2, 3, 6, 6),
                    desc='stride_pad'),
    # TODO FIX THIS
    # OldModuleTest(nn.SpatialCrossMapLRN,
                    # (3,),
                    # input_size=(2, 3, 6, 6)),
    OldModuleTest(nn.SpatialDivisiveNormalization,
                    (3,),
                    input_size=(2, 3, 8, 8)),
    OldModuleTest(nn.SpatialContrastiveNormalization,
                    (3,),
                    input_size=(2, 3, 8, 8)),
    OldModuleTest(nn.SpatialDilatedConvolution,
                    (3, 2, 3, 3, 2, 2, 1, 1, 2, 2),
                    input_size=(2, 3, 8, 8)),
    OldModuleTest(nn.SpatialDilatedConvolution,
                    (3, 2, 3, 3, 2, 2, 1, 1, 2, 2),
                    input_size=(2, 3, 8, 8),
                    desc='stride_pad'),
    OldModuleTest(nn.SpatialReflectionPadding,
                    (1, 2, 3, 4),
                    input_size=(2, 3, 8, 8)),
    OldModuleTest(nn.SpatialReplicationPadding,
                    (1, 2, 3, 4),
                    input_size=(2, 3, 4, 4)),
    OldModuleTest(nn.SpatialZeroPadding,
                    (1, 2, 3, 4),
                    input_size=(2, 3, 4, 4)),
    OldModuleTest(nn.SpatialConvolutionMap,
                    (nn.SpatialConvolutionMap.maps.oneToOne(3), 3, 3),
                    input_size=(3, 5, 5),
                    desc='oneToOne'),
    OldModuleTest(nn.SpatialConvolutionMap,
                    (nn.SpatialConvolutionMap.maps.oneToOne(3), 3, 3, 2, 2),
                    input_size=(3, 5, 5),
                    desc='oneToOne_stride'),
    OldModuleTest(nn.SpatialConvolutionMap,
                    (nn.SpatialConvolutionMap.maps.full(3, 4), 3, 3),
                    input_size=(3, 5, 5),
                    desc='full'),
    OldModuleTest(nn.SpatialFullConvolutionMap,
                    (nn.SpatialConvolutionMap.maps.oneToOne(3), 3, 3),
                    input_size=(3, 5, 5),
                    desc='oneToOne'),
    OldModuleTest(nn.SpatialFullConvolutionMap,
                    (nn.SpatialConvolutionMap.maps.oneToOne(3), 3, 3, 2, 2),
                    input_size=(3, 5, 5),
                    desc='oneToOne_stride'),
    OldModuleTest(nn.SpatialFullConvolutionMap,
                    (nn.SpatialConvolutionMap.maps.full(3, 4), 3, 3),
                    input_size=(3, 5, 5),
                    desc='full'),
    # TODO: test CUDA
    OldModuleTest(lambda: nn.SpatialFractionalMaxPooling(2, 2, 0.5, 0.5).fixPoolingRegions(),
                    input_size=(1, 3, 5, 5),
                    fullname='SpatialFractionalMaxPooling_ratio',
                    test_cuda=False),
    OldModuleTest(lambda: nn.SpatialFractionalMaxPooling(2, 2, 4, 4).fixPoolingRegions(),
                    input_size=(1, 3, 7, 7),
                    fullname='SpatialFractionalMaxPooling_size',
                    test_cuda=False),
    OldModuleTest(nn.SpatialFullConvolution,
                    (3, 4, 3, 3, 2, 2, 1, 1, 1, 1),
                    input_size=(1, 3, 7, 7)),
    OldModuleTest(nn.SpatialLPPooling,
                    (3, 2, 2, 2, 2, 2),
                    input_size=(1, 3, 7, 7)),
    OldModuleTest(nn.SpatialSubSampling,
                    (3, 3, 3, 2, 2),
                    input_size=(1, 3, 7, 7)),
    OldModuleTest(nn.SpatialSubtractiveNormalization,
                    (3,),
                    input_size=(1, 3, 7, 7)),
    OldModuleTest(nn.SpatialSubtractiveNormalization,
                    (3, torch.rand(3)),
                    input_size=(1, 3, 7, 7),
                    desc='kernel'),
    OldModuleTest(nn.SpatialUpSamplingNearest,
                    (2,),
                    input_size=(1, 3, 4, 4)),

    OldModuleTest(nn.TemporalConvolution,
                    (4, 5, 3),
                    input_size=(2, 10, 4)),
    OldModuleTest(nn.TemporalConvolution,
                    (4, 5, 3, 2),
                    input_size=(2, 10, 4),
                    desc='stride'),
    # TODO: this runs in non-batch mode only
    OldModuleTest(nn.TemporalSubSampling,
                    (4, 3),
                    input_size=(10, 4)),
    OldModuleTest(nn.TemporalSubSampling,
                    (4, 3, 2),
                    input_size=(10, 4),
                    desc='stride'),
    OldModuleTest(nn.TemporalMaxPooling,
                    (4,),
                    input_size=(2, 10, 4)),
    OldModuleTest(nn.TemporalMaxPooling,
                    (4, 4),
                    input_size=(2, 10, 4),
                    desc='stride'),

    OldModuleTest(nn.VolumetricAveragePooling,
                    (2, 2, 2),
                    input_size=(2, 3, 4, 4, 4)),
    OldModuleTest(nn.VolumetricAveragePooling,
                    (2, 2, 2, 2, 2, 2),
                    input_size=(2, 3, 5, 5, 5),
                    desc='stride'),
    OldModuleTest(nn.VolumetricBatchNormalization,
                    (3,),
                    input_size=(2, 3, 4, 4, 4)),
    OldModuleTest(nn.VolumetricBatchNormalization,
                    (3, 1e-3, 0.7),
                    input_size=(2, 3, 4, 4, 4),
                    desc='momentum'),
    OldModuleTest(nn.VolumetricBatchNormalization,
                    (3, 1e-3, 0.7, False),
                    input_size=(2, 3, 4, 4, 4),
                    desc='no_affine'),
    OldModuleTest(nn.VolumetricConvolution,
                    (3, 4, 2, 2, 2),
                    input_size=(2, 3, 3, 3, 3)),
    OldModuleTest(nn.VolumetricConvolution,
                    (3, 4, 2, 2, 2, 2, 2, 2),
                    input_size=(2, 3, 5, 5, 5),
                    desc='stride'),
    OldModuleTest(nn.VolumetricConvolution,
                    (3, 4, 2, 2, 2, 2, 2, 2, 1, 1, 1),
                    input_size=(2, 3, 5, 5, 5),
                    desc='stride_padding'),
    OldModuleTest(nn.VolumetricFullConvolution,
                    (2, 3, 2, 2, 2),
                    input_size=(1, 2, 4, 4, 4)),
    OldModuleTest(nn.VolumetricMaxPooling,
                    (2, 2, 2),
                    input_size=(2, 3, 5, 5, 5)),
    OldModuleTest(nn.VolumetricMaxPooling,
                    (2, 2, 2, 2, 2, 2),
                    input_size=(2, 3, 5, 5, 5),
                    desc='stride'),
    OldModuleTest(nn.VolumetricMaxPooling,
                    (2, 2, 2, 2, 2, 2, 1, 1, 1),
                    input_size=(2, 3, 5, 5, 5),
                    desc='stride_padding'),
    OldModuleTest(nn.VolumetricReplicationPadding,
                    (1, 2, 3, 4, 5, 6),
                    input_size=(2, 3, 5, 5, 5)),

    CriterionTest(nn.BCECriterion,
                        input=torch.rand(15, 10).clamp_(1e-2, 1 - 1e-2),
                        target=torch.randn(15, 10).gt(0).double()
                    ),
    CriterionTest(nn.BCECriterion,
                        (torch.rand(10),),
                        input=torch.rand(15, 10).clamp_(1e-2, 1 - 1e-2),
                        target=torch.randn(15, 10).gt(0).double(),
                        desc='weights'),
    CriterionTest(nn.CrossEntropyCriterion,
                        input=torch.randn(15, 10),
                        target=torch.Tensor(15).uniform_().mul(10).floor()),
    CriterionTest(nn.CrossEntropyCriterion,
                        (torch.rand(10),),
                        input=torch.randn(15, 10),
                        target=torch.Tensor(15).uniform_().mul(10).floor(),
                        desc='weights'),
    CriterionTest(nn.CosineEmbeddingCriterion,
                        input=[torch.rand(15, 10), torch.rand(15, 10)],
                        target=torch.randn(15).sign()),
    CriterionTest(nn.CosineEmbeddingCriterion,
                        (0.5,),
                        input=[torch.rand(15, 10), torch.rand(15, 10)],
                        target=torch.randn(15).sign(),
                        desc='margin'),
    CriterionTest(nn.DistKLDivCriterion,
                        input=torch.rand(10, 10).log(),
                        target=torch.rand(10, 10)),
    CriterionTest(nn.HingeEmbeddingCriterion,
                        input=torch.rand(10),
                        target=torch.randn(10).gt(0).double().mul_(2).sub(1)),
    CriterionTest(nn.HingeEmbeddingCriterion,
                        (0.5,),
                        input=torch.rand(10),
                        target=torch.randn(10).gt(0).double().mul_(2).sub(1),
                        desc='margin'),
    CriterionTest(nn.L1Cost,
                        input=torch.randn(2, 3, 4, 5),
                        target=None),
    CriterionTest(nn.L1HingeEmbeddingCriterion,
                        input=[torch.randn(2, 3, 4, 5), torch.randn(2, 3, 4, 5)],
                        target=1),
    CriterionTest(nn.L1HingeEmbeddingCriterion,
                        (2,),
                        input=[torch.randn(2, 3, 4, 5), torch.randn(2, 3, 4, 5)],
                        target=1,
                        desc='margin'),
    CriterionTest(nn.MSECriterion,
                        input=torch.randn(2, 3, 4, 5),
                        target=torch.randn(2, 3, 4, 5),
                        reference_fn=lambda i,t,_: (i-t).abs().pow(2).sum() / i.numel()),
    CriterionTest(nn.WeightedMSECriterion,
                        (torch.rand(3, 4, 5),),
                        input=torch.randn(2, 3, 4, 5),
                        target=torch.randn(2, 3, 4, 5)),
    CriterionTest(nn.MarginCriterion,
                        input_size=(5, 10),
                        target=torch.randn(5, 10).sign()),
    CriterionTest(nn.MarginRankingCriterion,
                        input=[torch.randn(50).mul(10), torch.randn(50).mul(10)],
                        target=torch.randn(50).sign()),
    CriterionTest(nn.MarginRankingCriterion,
                        (2,),
                        input=[torch.randn(50).mul(10), torch.randn(50).mul(10)],
                        target=torch.randn(50).sign(),
                        desc='margin'),
    CriterionTest(nn.ClassSimplexCriterion,
                        (30,),
                        input=torch.randn(5, 30).mul(10).renorm(2, 0, 1),
                        target=torch.rand(5).mul(30).floor().long(),
                        desc='margin'),
    CriterionTest(nn.MultiLabelMarginCriterion,
                        input_size=(5, 10),
                        target=torch.rand(5, 10).mul(10).floor()),
    CriterionTest(nn.MultiLabelSoftMarginCriterion,
                        input_size=(5, 10),
                        target=torch.rand(5, 10).mul(2).floor()),
    CriterionTest(nn.MultiLabelSoftMarginCriterion,
                        (torch.rand(10),),
                        input_size=(5, 10),
                        target=torch.rand(5, 10).mul(2).floor(),
                        desc='weights'),
    CriterionTest(nn.MultiMarginCriterion,
                        input_size=(5, 10),
                        target=torch.rand(5).mul(8).floor()),
    CriterionTest(nn.SmoothL1Criterion,
                        input_size=(5, 10),
                        target=torch.randn(5, 10)),
    CriterionTest(nn.SoftMarginCriterion,
                        input_size=(5, 5),
                        target=torch.randn(5, 5).sign()),
    CriterionTest(nn.SpatialClassNLLCriterion,
                        input_size=(2, 3, 5, 5),
                        target=torch.rand(2, 5, 5).mul(3).floor()),
]
# TODO: FlattenTable gradient
# TODO: NarrowTable gradient
# TODO: CriterionTable
# TODO: MultiCriterion
# TODO: SplitTable

for p in (1, 2, 1.5):
    tests.append(
        OldModuleTest(nn.Normalize,
                        (p,),
                        input_size=(4, 5),
                        # Eh, we need to use p as a default, so it's passed by value
                        reference_fn=lambda i,_,p=p: i.div(i.norm(p, 1).expandAs(i)),
                        desc=str(p)),
    )
for p in range(1, 4+1):
    tests.append(
        OldModuleTest(nn.PairwiseDistance,
                        (p,),
                        input_size=[(4, 10), (4, 10)],
                        desc=str(p))
    )

def build_spatial_unpooling_net():
    pool = nn.SpatialMaxPooling(2, 2, 2, 2)
    unpool = nn.SpatialMaxUnpooling(pool)
    return nn.Sequential().add(pool).add(unpool)

tests.append(
        OldModuleTest(build_spatial_unpooling_net,
            input_size=(1, 3, 10, 10),
            desc='SpatialMaxUnpooling')
        )

def build_volumetric_unpooling_net():
    pool = nn.VolumetricMaxPooling(2, 2, 2, 2)
    unpool = nn.VolumetricMaxUnpooling(pool)
    return nn.Sequential().add(pool).add(unpool)

tests.append(
        OldModuleTest(build_volumetric_unpooling_net,
            input_size=(1, 3, 10, 10),
            desc='VolumetricMaxUnpooling')
        )

def prepare_tests():
    def add_test(test):
        test_name = test.get_name()
        cuda_test_name = test_name + '_cuda'
        if hasattr(TestNN, test_name):
            raise RuntimeError('Found two tests with the same name: ' + test_name)
        if hasattr(TestNN, cuda_test_name):
            raise RuntimeError('Found two tests with the same name: ' + cuda_test_name)
        setattr(TestNN, test_name, lambda self,test=test: test(self))
        setattr(TestNN, cuda_test_name, lambda self,test=test: test.test_cuda(self))
    name_remap = {
        'Conv2d': 'SpatialConvolution',
        'MaxPooling2d': 'SpatialMaxPooling',
        'Softmax': 'SoftMax',
        'Softmax2d': 'SpatialSoftMax',
        'LogSoftmax': 'LogSoftMax',
        'BatchNorm': 'BatchNormalization',
    }
    for test in tests:
        add_test(test)
    for test_params in module_tests:
        test_params = deepcopy(test_params)
        name = test_params.pop('module_name')
        name = name_remap.get(name, name)
        test_params['constructor'] = getattr(nn, name)
        test = OldModuleTest(**test_params)
        add_test(test)
    for test_params in criterion_tests:
        test_params = deepcopy(test_params)
        name = test_params.pop('module_name')
        name = name_remap.get(name, name)
        test_params['constructor'] = getattr(nn, name)
        test = CriterionTest(**test_params)
        add_test(test)

class TestNN(NNTestCase):

    def _forward(self, module, input):
        return module.forward(input)

    def _backward(self, module, input, output, grad_output):
        return module.backward(input, grad_output)

    def _forward_criterion(self, criterion, input, target):
        return criterion.forward(input, target)

    def _backward_criterion(self, criterion, input, target):
        return criterion.backward(input, target)

    def _zero_grad_parameters(self, module):
        return module.zeroGradParameters()

    def _get_parameters(self, module):
        return module.parameters() or ([], [])

    def test_Dropout(self):
        p = 0.2
        input = torch.Tensor(1000).fill_(1-p)

        module = nn.Dropout(p)
        output = module.forward(input)
        self.assertLess(abs(output.mean() - (1-p)), 0.05)
        gradInput = module.backward(input, input)
        self.assertLess(abs(gradInput.mean() - (1-p)), 0.05)

        module = nn.Dropout(p, True)
        output = module.forward(input.clone())
        self.assertLess(abs(output.mean() - (1-p)), 0.05)
        gradInput = module.backward(input.clone(), input.clone())
        self.assertLess(abs(gradInput.mean() - (1-p)), 0.05)

    def test_SpatialDropout(self):
        p = 0.2
        b = random.randint(1, 5)
        w = random.randint(1, 5)
        h = random.randint(1, 5)
        nfeats = 1000
        input = torch.Tensor(b, nfeats, w, h).fill_(1)
        module = nn.SpatialDropout(p)
        module.training()
        output = module.forward(input)
        self.assertLess(abs(output.mean() - (1-p)), 0.05)
        gradInput = module.backward(input, input)
        self.assertLess(abs(gradInput.mean() - (1-p)), 0.05)

    def test_VolumetricDropout(self):
        p = 0.2
        bsz = random.randint(1,5)
        t = random.randint(1,5)
        w = random.randint(1,5)
        h = random.randint(1,5)
        nfeats = 1000
        input = torch.Tensor(bsz, nfeats, t, w, h).fill_(1)
        module = nn.VolumetricDropout(p)
        module.training()
        output = module.forward(input)
        self.assertLess(abs(output.mean() - (1-p)), 0.05)
        gradInput = module.backward(input, input)
        self.assertLess(abs(gradInput.mean() - (1-p)), 0.05)

    def test_ReLU_reference(self):
        input = torch.randn(10, 20)
        module = nn.ReLU()
        output = module.forward(input)
        self.assertTrue(output[input.ge(0)].eq(input[input.gt(0)]).all())
        self.assertTrue(output[input.lt(0)].eq(0).all())

    def test_ReLU6_reference(self):
        input = torch.randn(10, 20).mul(10)
        module = nn.ReLU6()
        output = module.forward(input)
        # TODO: check elements between 0 and 6
        self.assertTrue(output[input.ge(6)].eq(6).all())
        self.assertTrue(output[input.lt(0)].eq(0).all())

    def test_Copy(self):
        input = torch.randn(3,4).double()
        c = nn.Copy(torch.DoubleTensor, torch.FloatTensor)
        output = c.forward(input)
        self.assertEqual(torch.typename(output), 'torch.FloatTensor')
        self.assertEqual(output, input.float(), 1e-6)
        gradInput = c.backward(input, output.fill_(1))
        self.assertEqual(torch.typename(gradInput), 'torch.DoubleTensor')
        self.assertEqual(gradInput, output.double(), 1e-6)
        c.dontCast = True
        c.double()
        self.assertEqual(torch.typename(output), 'torch.FloatTensor')

    def test_FlattenTable(self):
        input = [
            torch.rand(1),
            [
                torch.rand(2),
                [
                    torch.rand(3)
                ],
            ],
            torch.rand(4)
        ]
        gradOutput = [
            torch.rand(1),
            torch.rand(2),
            torch.rand(3),
            torch.rand(4)
        ]

        m = nn.FlattenTable()
        output = m.forward(input)
        self.assertEqual(len(output), 4)
        self.assertEqual(output[0], input[0])
        self.assertEqual(output[1], input[1][0])
        self.assertEqual(output[2], input[1][1][0])
        self.assertEqual(output[3], input[2])

        gradInput = m.backward(input, gradOutput)
        self.assertEqual(gradOutput[0], gradInput[0])
        self.assertEqual(gradOutput[1], gradInput[1][0])
        self.assertEqual(gradOutput[2], gradInput[1][1][0])
        self.assertEqual(gradOutput[3], gradInput[2])

        # More uglyness: FlattenTable doesn't rebuild the table every updateOutput
        # call, so we need to make sure that modifications to the input are
        # detected correctly (and that the table is correctly rebuilt.
        # CASE 1: Nothing changes so the output table shouldn't be redefined
        old_input_map = m.input_map
        old_output = m.output
        m.forward(input)
        self.assertEqual(old_input_map, m.input_map)
        self.assertEqual(old_output, m.output)

        # CASE 2: An element is added to the input table
        old_input_map = m.input_map
        old_output = m.output
        input[1].append(torch.rand(5))
        m.forward(input)
        self.assertNotEqual(old_input_map, m.input_map)
        self.assertNotEqual(old_output, m.output)

        # CASE 3: An element is removed from the input table
        old_input_map = m.input_map
        old_output = m.output
        input.pop()
        m.forward(input)
        self.assertNotEqual(old_input_map, m.input_map)
        self.assertNotEqual(old_output, m.output)

    def test_Concat(self):
        input = torch.randn(4, 2)
        num_modules = random.randint(2, 5)
        linears = [nn.Linear(2, 5) for i in range(num_modules)]

        m = nn.Concat(0)
        for l in linears:
            m.add(l)
            l.zeroGradParameters()
            l.weight.fill_(1)
            l.bias.fill_(0)

        output = m.forward(input)
        output2 = input.sum(1).expand(4, 5).repeatTensor(num_modules, 1)
        self.assertEqual(output2, output)

        gradInput = m.backward(input, torch.ones(output2.size()))
        gradInput2 = torch.ones(4, 2).fill_(num_modules * 5)
        self.assertEqual(gradInput, gradInput2)

        gradWeight = input.sum(0).expand(5, 2)
        for l in linears:
            self.assertEqual(gradWeight, l.gradWeight)

    def test_Parallel(self):
        input = torch.randn(3, 4, 5)
        m = nn.Parallel(0, 2)
        m.add(nn.View(4, 5, 1))
        m.add(nn.View(4, 5, 1))
        m.add(nn.View(4, 5, 1))

        output = m.forward(input)
        output2 = input.transpose(0, 2).transpose(0, 1)
        self.assertEqual(output2, output)

        gradInput = m.backward(input, output2)
        self.assertEqual(gradInput, input)

    def test_ParallelTable(self):
        input = torch.randn(3, 4, 5)
        p = nn.ParallelTable()
        p.add(nn.View(4,5,1))
        p.add(nn.View(4,5,1))
        p.add(nn.View(4,5,1))
        m = nn.Sequential()
        m.add(nn.SplitTable(0))
        m.add(p)
        m.add(nn.JoinTable(2))

        output = m.forward(input)
        output2 = input.transpose(0,2).transpose(0,1)
        self.assertEqual(output2, output)

        gradInput = m.backward(input, output2)
        self.assertEqual(gradInput, input)

    def test_ConcatTable(self):
        input = [
                torch.randn(3, 4).float(), torch.randn(3, 4).float(), [torch.randn(3, 4).float()]
        ]
        _gradOutput = [
                torch.randn(3, 3,4).float(), torch.randn(3, 3,4).float(), torch.randn(3, 3,4).float()
        ]
        gradOutput = [
                [_gradOutput[0][0], _gradOutput[1][0], [_gradOutput[2][0]]],
                [_gradOutput[0][1], _gradOutput[1][1], [_gradOutput[2][1]]],
                [_gradOutput[0][2], _gradOutput[1][2], [_gradOutput[2][2]]]
        ]
        module = nn.ConcatTable()
        module.add(nn.Identity())
        module.add(nn.Identity())
        module.add(nn.Identity())
        module.float()

        output = module.forward(input)
        output2 = [input, input, input]
        self.assertEqual(output2, output)
        gradInput = module.backward(input, gradOutput)
        gradInput2 = [_gradOutput[0].sum(0).squeeze(0), _gradOutput[1].sum(0).squeeze(0), [_gradOutput[2].sum(0).squeeze(0)]]
        self.assertTrue(isinstance(gradInput, list))
        self.assertFalse(isinstance(gradInput[0], list))
        self.assertFalse(isinstance(gradInput[1], list))
        self.assertTrue(isinstance(gradInput[2], list))
        self.assertEqual(len(gradInput), 3)
        self.assertEqual(len(gradInput[2]), 1)
        for t1, t2 in zip(iter_tensors(gradInput), iter_tensors(gradInput2)):
            self.assertEqual(t1, t2)

        # test outputs for variable length inputs
        test = nn.ConcatTable()
        test.add(nn.Identity())
        test.add(nn.Identity())

        x = [torch.randn(5), torch.randn(5)]
        y = [torch.randn(5)]

        o1 = len(test.forward(x))
        go1 = len(test.backward(x, [x, x]))
        o2 = len(test.forward(y))
        go2 = len(test.backward(y, [y, y]))
        self.assertEqual(o1, 2)
        self.assertEqual(go1, 2)
        self.assertEqual(o2, 2)
        self.assertEqual(go2, 1)

    def test_DepthConcat(self):
        outputSize = torch.IntTensor((5, 6, 7, 8))
        input = torch.randn(2, 3, 12, 12)
        gradOutput = torch.randn(2, int(outputSize.sum()), 12, 12)
        concat = nn.DepthConcat(1)
        concat.add(nn.SpatialConvolution(3, outputSize[0], 1, 1, 1, 1)) #> 2, 5, 12, 12
        concat.add(nn.SpatialConvolution(3, outputSize[1], 3, 3, 1, 1)) #> 2, 6, 10, 10
        concat.add(nn.SpatialConvolution(3, outputSize[2], 4, 4, 1, 1)) #> 2, 7, 9, 9
        concat.add(nn.SpatialConvolution(3, outputSize[3], 5, 5, 1, 1)) #> 2, 8, 8, 8
        concat.zeroGradParameters()
        # forward/backward
        outputConcat = concat.forward(input)
        gradInputConcat = concat.backward(input, gradOutput)
        # the spatial dims are the largest, the nFilters is the sum
        output = torch.Tensor(2, int(outputSize.sum()), 12, 12).zero_() # zero for padding
        narrows = ( (slice(None), (0, 5), slice(None), slice(None)), (slice(None), (5, 11), (1, 11), (1, 11)), (slice(None), (11, 18), (1, 10), (1, 10)), (slice(None), (18, 26), (2, 10), (2, 10)) )
        gradInput = input.clone().zero_()
        for i in range(4):
           conv = concat.get(i)
           gradWeight = conv.gradWeight.clone()
           conv.zeroGradParameters()
           output[narrows[i]].copy_(conv.forward(input))
           gradInput.add_(conv.backward(input, gradOutput[narrows[i]]))
           self.assertEqual(gradWeight, conv.gradWeight)

        self.assertEqual(output, outputConcat)
        self.assertEqual(gradInput, gradInputConcat)

    def test_Contiguous(self):
        input = torch.randn(10, 10, 10)
        noncontig = input[:, 4]
        module = nn.Contiguous()
        assert not noncontig.isContiguous()
        output = module.forward(noncontig)
        self.assertEqual(output, noncontig)
        self.assertTrue(output.contiguous())

    def test_Index(self):
        net = nn.Index(0)

        # test 1D
        input = [torch.Tensor((10, 20, 30)), torch.LongTensor((0, 1, 1, 2))]
        output = net.forward(input)
        self.assertEqual(output, torch.Tensor((10, 20, 20, 30)))

        gradOutput = torch.Tensor((1, 1, 1, 3))
        gradInput = net.backward(input, gradOutput)
        self.assertEqual(gradInput[0], torch.Tensor((1, 2, 3)))

        # test 2D
        input = [torch.Tensor(((10, 20), (30, 40))), torch.LongTensor((0, 0))]
        output = net.forward(input)
        self.assertEqual(output, torch.Tensor(((10, 20), (10, 20))))

        gradOutput = torch.Tensor(((1, 2), (1, 2)))
        gradInput = net.backward(input, gradOutput)
        self.assertEqual(gradInput[0], torch.Tensor(((2, 4), (0, 0))))

    def test_L1Penalty(self):
        weight = 1
        m = nn.L1Penalty(weight, False, False)

        input = torch.rand(2,10).add_(-0.5)
        input[0][0] = 0

        m.forward(input)
        grad = m.backward(input, torch.ones(input.size()))

        self.assertEqual(input.abs().sum() * weight, m.loss)

        true_grad = (input.gt(0).typeAs(grad) +
            input.lt(0).typeAs(grad).mul_(-1)).mul_(weight)
        self.assertEqual(true_grad, grad)

    def test_MaskedSelect(self):
        input = torch.randn(4, 5)
        mask = torch.ByteTensor(4, 5).bernoulli_()
        module = nn.MaskedSelect()
        out = module.forward([input, mask])
        self.assertEqual(input.maskedSelect(mask), out)

        gradOut = torch.Tensor((20, 80))
        input = torch.Tensor(((10, 20), (30, 40)))
        inTarget = torch.Tensor(((20, 0), (0, 80)))
        mask = torch.ByteTensor(((1, 0), (0, 1)))
        module = nn.MaskedSelect()
        module.forward([input, mask])
        gradIn = module.backward([input, mask], gradOut)
        self.assertEqual(inTarget, gradIn[0])

    def test_MultiCriterion(self):
        input = torch.rand(2, 10)
        target = torch.Tensor((1, 8))
        nll = nn.ClassNLLCriterion()
        nll2 = nn.CrossEntropyCriterion()
        mc = nn.MultiCriterion().add(nll, 0.5).add(nll2)

        output = mc.forward(input, target)
        output2 = nll.forward(input, target)/2 + nll2.forward(input, target)

        self.assertEqual(output, output2)
        gradInput = mc.backward(input, target)
        gradInput2 = nll.backward(input, target).clone().div(2).add(nll2.backward(input, target))
        self.assertEqual(gradInput, gradInput2)

        # test type
        mc.float()
        gradInput = gradInput.clone()
        input3 = input.float()
        target3 = target.float()
        output3 = mc.forward(input3, target3)
        gradInput3 = mc.backward(input3, target3)
        self.assertEqual(output, output3)
        self.assertEqual(gradInput.float(), gradInput3)

        # test table input
        # TODO: enable when Criterion.clone is ready
        # mc.double()
        # input = [torch.randn(2, 10), [torch.randn(2, 10), torch.randn(2, 10)]]
        # target = [torch.IntTensor((1, 8)), [torch.IntTensor((5, 6)), torch.IntTensor((4, 3))]]
        # pnllc = nn.ParallelCriterion().add(nll).add(nn.ParallelCriterion().add(nll.clone()).add(nll.clone()))
        # pnllc2 = nn.ParallelCriterion().add(nll2).add(nn.ParallelCriterion().add(nll2.clone()).add(nll2.clone()))
        # mc = nn.MultiCriterion().add(pnllc, 0.5).add(pnllc2)
        # output = mc.forward(input, target)
        # output2 = pnllc.forward(input, target)/2 + pnllc2.forward(input, target)
        # self.assertEqual(output, output2)
        # gradInput = mc.backward(input, target)
        # gradInput2 = pnllc.clone().backward(input, target)
        # gradInput2b = pnllc2.backward(input, target)
        # gradInput2[0].div(2).add(gradInput2b[0])
        # gradInput2[1][0].div(2).add(gradInput2b[1][0])
        # gradInput2[1][1].div(2).add(gradInput2b[1][1])
        # self.assertEqual(gradInput[1], gradInput2[0])
        # self.assertEqual(gradInput[1][9], gradInput2[1][0])
        # self.assertEqual(gradInput[1][1], gradInput2[1][1])

    def test_ParallelCriterion(self):
        input = [torch.rand(2, 10), torch.randn(2, 10)]
        target = [torch.IntTensor((1, 8)), torch.randn(2, 10)]
        nll = nn.ClassNLLCriterion()
        mse = nn.MSECriterion()
        pc = nn.ParallelCriterion().add(nll, 0.5).add(mse)
        output = pc.forward(input, target)
        output2 = nll.forward(input[0], target[0])/2 + mse.forward(input[1], target[1])
        self.assertEqual(output, output2)
        gradInput2 = [nll.backward(input[0], target[0]).clone().div(2), mse.backward(input[1], target[1])]
        gradInput = pc.backward(input, target)
        self.assertEqual(gradInput[0], gradInput2[0])
        self.assertEqual(gradInput[1], gradInput2[1])

        # test type
        pc.float()
        gradInput[0], gradInput[1] = gradInput[0].clone(), gradInput[1].clone()
        input3 = [input[0].float(), input[1].float()]
        target3 = [target[0].float(), target[1].float()]
        output3 = pc.forward(input3, target3)
        gradInput3 = pc.backward(input3, target3)
        self.assertEqual(output, output3)
        self.assertEqual(gradInput[0].float(), gradInput3[0])
        self.assertEqual(gradInput[1].float(), gradInput3[1])

        # test repeatTarget
        input = [torch.rand(2, 10), torch.randn(2, 10)]
        target = torch.randn(2, 10)
        mse = nn.MSECriterion()
        pc = nn.ParallelCriterion(True).add(mse, 0.5).add(nn.MSECriterion())
        output = pc.forward(input, target)
        output2 = mse.forward(input[0], target)/2 + mse.forward(input[1], target)
        self.assertEqual(output, output2)
        gradInput = pc.backward(input, target)
        gradInput2 = [mse.backward(input[0], target).clone().div(2), mse.backward(input[1], target)]
        self.assertEqual(gradInput[0], gradInput2[0])
        self.assertEqual(gradInput[1], gradInput2[1])

        # table input
        input = [torch.randn(2, 10), [torch.rand(2, 10), torch.randn(2, 10)]]
        target = [torch.IntTensor((2, 5)), [torch.IntTensor((1, 8)), torch.randn(2, 10)]]
        nll2 = nn.ClassNLLCriterion()
        nll = nn.ClassNLLCriterion()
        mse = nn.MSECriterion()
        pc = nn.ParallelCriterion().add(nll, 0.5).add(mse)
        pc2 = nn.ParallelCriterion().add(nll2, 0.4).add(pc)
        output = pc2.forward(input, target)
        output2 = nll2.forward(input[0], target[0])*0.4 + nll.forward(input[1][0], target[1][0])/2 + mse.forward(input[1][1], target[1][1])
        self.assertEqual(output, output2)
        gradInput2 = [
                nll2.backward(input[0], target[0]).clone().mul(0.4),
                [nll.backward(input[1][1], target[1][0]).clone().div(2), mse.backward(input[1][1], target[1][1])]
        ]
        gradInput = pc2.backward(input, target)
        self.assertEqual(gradInput[0], gradInput2[0])
        self.assertEqual(gradInput[1][0], gradInput2[1][0])
        self.assertEqual(gradInput[1][1], gradInput2[1][1])

    def test_NarrowTable(self):
        input = [torch.Tensor(i) for i in range(1, 6)]

        module = nn.NarrowTable(1)
        output = module.forward(input)
        self.assertEqual(output, input[1:2])

        module = nn.NarrowTable(2, 3)
        output = module.forward(input)
        self.assertEqual(output, input[2:5])


if __name__ == '__main__':
    prepare_tests()
    unittest.main()

