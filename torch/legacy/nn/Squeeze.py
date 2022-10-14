import torch
from .Module import Module

class Squeeze(Module):

    def __init__(self, dim=None):
        super(Squeeze, self).__init__()
        self.dim = dim

    def updateOutput(self, input):
        dim = self.dim
        self.output.set_(input.squeeze(dim) if dim is not None else input.squeeze())
        return self.output


    def updateGradInput(self, input, gradOutput):
        assert input.nElement() == gradOutput.nElement()
        self.gradInput.set_(gradOutput.viewAs(input))
        return self.gradInput

