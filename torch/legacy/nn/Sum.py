import torch
from .Module import Module
from .utils import clear

class Sum(Module):

    def __init__(self, dimension=0, sizeAverage=False):
        super(Sum, self).__init__()
        self.dimension   = dimension
        self.sizeAverage = sizeAverage
        self._gradOutput = None

    def _getPositiveDimension(self, input):
        dimension = self.dimension
        if dimension < 0:
            dimension = input.dim() + dimension
        return dimension

    def updateOutput(self, input):
        dimension = self._getPositiveDimension(input)

        torch.sum(self.output, input, dimension)
        if self.sizeAverage:
            self.output.div_(input.size(dimension))

        return self.output

    def updateGradInput(self, input, gradOutput):
        dimension = self._getPositiveDimension(input)
        # zero-strides dont work with MKL/BLAS, so
        # dont set self.gradInput to zero-stride tensor.
        # Instead, do a deepcopy.
        size = input.size()
        size[dimension] = 1
        if not gradOutput.isContiguous():
            self._gradOutput = self._gradOutput or gradOutput.new()
            self._gradOutput.resizeAs_(gradOutput).copy_(gradOutput)
            gradOutput = self._gradOutput

        gradOutput = gradOutput.view(size)
        self.gradInput.resizeAs_(input)
        self.gradInput.copy_(gradOutput.expandAs(input))
        if self.sizeAverage:
            self.gradInput.div_(input.size(dimension))

        return self.gradInput


    def clearState(self):
         clear(self, '_gradOutput')
         return super(Sum, self).clearState()

