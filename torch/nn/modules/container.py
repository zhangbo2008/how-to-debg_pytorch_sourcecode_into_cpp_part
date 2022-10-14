from torch.autograd import Variable
from .module import Module
from collections import OrderedDict


class Container(Module):

    def __init__(self, **kwargs):
        super(Container, self).__init__()
        self.module_set = set()
        for key, value in kwargs.items():
            self._assign_module(key, value)

    def _assign_module(self, name, module):
        # TODO: error message
        assert not hasattr(self, name)
        setattr(self, name, module)
        self.module_set.add(module)

    def parameters(self):
        for module in self.module_set:
            for p in module.parameters():
                yield p

    def zero_grad_parameters(self):
        for p in self.parameters():
            p.grad.zero_()


class Sequential(Container):

    def __init__(self, *args):
        super(Sequential, self).__init__()
        self.modules = []
        module_name = None
        if len(args) == 1 and isinstance(args[0], OrderedDict):
            for key, module in args[0].items():
                self.modules.append(module)
                self._assign_module(key, module)
        else:
            for arg in args:
                if isinstance(arg, str):
                    assert module_name is None
                    module_name = arg
                else:
                    self.modules.append(arg)
                    if module_name is not None:
                        self._assign_module(module_name, arg)
                    module_name = None
            assert module_name is None

    def __getitem__(self, idx):
        throw = False
        try:
            int_idx = int(idx)
        except ValueError:
            throw = True
        if throw:
            raise IndexError("Trying to index sequential with an invalid object: " + str(idx))
        try:
            return self.modules[int_idx]
        except IndexError:
            throw = True
        if throw:
            raise IndexError("Sequential doesn't have any module with index " + str(idx))

    def _forward(self, input):
        for module in self.modules:
            input = module(input)
        return (input,)
