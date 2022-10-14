import torch
from .Module import Module

class View(Module):

    def resetSize(self, *args):
        if len(args) == 1 and isinstance(args[0], torch.LongStorage):
            self.size = args[0]
        else:
            self.size = torch.LongStorage(args)

        self.numElements = 1
        inferdim = False
        for i in range(len(self.size)):
            szi = self.size[i]
            if szi >= 0:
                self.numElements = self.numElements * self.size[i]
            else:
                assert szi == -1
                assert not inferdim
                inferdim = True

        return self

    def __init__(self, *args):
        super(View, self).__init__()
        self.resetSize(*args)

    def updateOutput(self, input):
        self.output = self.output or input.new()
        self.output = input.view(self.size)
        return self.output


    def updateGradInput(self, input, gradOutput):
        self.gradInput = self.gradInput or gradOutput.new()
        self.gradInput = gradOutput.view(input.size())
        return self.gradInput

    def __repr__(self):
        return super(View, self).__repr__() + '({})'.format(', '.join(map(str, self.size)))

