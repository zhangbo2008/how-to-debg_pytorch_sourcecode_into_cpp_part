import torch
from .Criterion import Criterion

class SpatialClassNLLCriterion(Criterion):

    def __init__(self, weights=None, sizeAverage=True):
        assert weights is None or weights.dim() == 1
        super(SpatialClassNLLCriterion, self).__init__()
        self.sizeAverage = sizeAverage
        self.weights = weights

        self.output_tensor = torch.zeros(1)
        self.total_weight_tensor = torch.ones(1)
        self.target = torch.zeros(1).long()

    def updateOutput(self, input, target):
        if target.type() == 'torch.cuda.FloatTensor':
           self.target = target
        else:
           self.target = target.long()

        self._backend.SpatialClassNLLCriterion_updateOutput(
            self._backend.library_state,
            input,
            self.target,
            self.output_tensor,
            self.sizeAverage,
            self.weights,
            self.total_weight_tensor
        )
        self.output = self.output_tensor[0]
        return self.output

    def updateGradInput(self, input, target):
        if target.type() == 'torch.cuda.FloatTensor':
           self.target = target
        else:
           self.target = target.long()

        self.gradInput.resizeAs_(input).zero_()
        self._backend.SpatialClassNLLCriterion_updateGradInput(
            self._backend.library_state,
            input,
            self.target,
            self.gradInput,
            self.sizeAverage,
            self.weights,
            self.total_weight_tensor
        )
        return self.gradInput

