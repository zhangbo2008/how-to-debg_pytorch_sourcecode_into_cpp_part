How to Debug PyTorch Source Code with vscode 
i used version 0.1.1 . cause it is teh simplest for learning.

cause this is so important, so i write the istruction by English, and put it on github. 
1.first you must make sure you can run python with vscode.
    如果运行python没效果,那是因为vscode里面python插件太新了.一般是python3.6
    找个两年前的python插件即可.https://zhuanlan.zhihu.com/p/543432988
    launch.json里面设置    "justMyCode": false .

    if you python can not run, just because you use python early version.
    so the python plug must be match, but defalutly vscode install the latest version. you can change zhe plug vesrion mannually.
2. because with WSL or other linux system . we may have python2 and python3.
    so check the later torch install directory for which python you use.
    if my repos, i use python2.

    DEBUG=1 USE_DISTRIBUTED=0 USE_MKLDNN=0 USE_CUDA=0 BUILD_TEST=0 USE_FBGEMM=0 USE_NNPACK=0 USE_QNNPACK=0 USE_XNNPACK=0

    python setup.py develop

3. set .vscode/lauch.json as i set
4. run abc/aaa.py by Run/start_debugging
5. click the upper triangluer button , select (gdb) attach, then click the triangular button left. then input aaa.py, select the bigger pid for attached, just like :
root     13103  1.0  0.1 483984 22792 pts/4    Sl   09:16   0:01 /usr/bin/python /root/.vscode-server/extensions/ms-python.python-2021.1.502429796/pythonFiles/lib/python/debugpy --connect 127.0.0.1:63215 --configure-qt none --adapter-access-token 0205a60036aad9da3fad64b96855cf1675acfeceae73ebacfb7f4f763545de36 /home/root2/pytorch-0.1.1/abc/aaa.py

6. continue debug python code ,then you will inter the cpp part. so begin your journey for the pytorch sourcecode .


编译这个torch0.1源码. 编译成功之后,我们会发现项目跟目录里面有一个torch目录,所以我们如果直接在这个目录运行import torch必然会调用这个目录而不是真正安装的位置.
运行:
    所以我们要cd abc, 然后再运行python3  import torch即可.
    如果运行python没效果,那是因为vscode里面python插件太新了.一般是python3.6
    找个两年前的python插件即可.https://zhuanlan.zhihu.com/p/543432988
    launch.json里面设置    "justMyCode": false .

源码会在/usr/local/lib/python3.6/dist-packages/torch/



How to Debug PyTorch Source Code


靠谱教程:
https://www.zhihu.com/question/58253344/answer/2689147902?utm_id=0



vscode 运行之后 gdb attach比较长的那个.
















# pytorch [alpha-1] ![Build Status](https://travis-ci.com/apaszke/pytorch.svg?token=x5muYzmNgtGJxk6DvWMN&branch=master)

The project is still under active development and is likely to drastically change in short periods of time.
We will be announcing API changes and important developments via a newsletter, github issues and post a link to the issues on slack.
Please remember that at this stage, this is an invite-only closed alpha, and please don't distribute code further.
This is done so that we can control development tightly and rapidly during the initial phases with feedback from you.


## Installation
```bash
pip install -r requirements.txt
pip install .
```

To install with CUDA support change `WITH_CUDA = False` to `WITH_CUDA = True` in `setup.py`.

## Communication
* github issues: bug reports, feature requests, install issues, RFCs, thoughts, etc.
* slack: general chat, online discussions, collaboration etc. https://pytorch.slack.com/ . If you need a slack invite, ping me at soumith@pytorch.org
* newsletter: no-noise, one-way email newsletter with important announcements about pytorch. You can sign-up here: http://eepurl.com/cbG0rv

## Timeline

We will run the alpha releases weekly for 6 weeks.
After that, we will reevaluate progress, and if we are ready, we will hit beta-0. If not, we will do another two weeks of alpha.

* alpha-0: Working versions of torch, cutorch, nn, cunn, optim fully unit tested with seamless numpy conversions
* alpha-1: Serialization to/from disk with sharing intact. initial release of the new neuralnets package based on a Chainer-like design
* alpha-2: sharing tensors across processes for hogwild training or data-loading processes. a rewritten optim package for this new nn.
* alpha-3: binary installs (prob will take @alexbw 's help here), contbuilds, etc.
* alpha-4: a ton of examples across vision, nlp, speech, RL -- this phase might make us rethink parts of the APIs, and hence want to do this in alpha than beta
* alpha-5: Putting a simple and efficient story around multi-machine training. Probably simplistic like torch-distlearn. Building the website, release scripts, more documentation, etc.
* alpha-6: [no plan yet]

The beta phases will be leaning more towards working with all of you, convering your use-cases, active development on non-core aspects.

## pytorch vs torch: important changes

We've decided that it's time to rewrite/update parts of the old torch API, even if it means losing some of backward compatibility (we can hack up a model converter that converts correctly).
This section lists the biggest changes, and suggests how to shift from torch to pytorch.

For now there's no pytorch documentation.
Since all currently implemented modules are very similar to the old ones, it's best to use torch7 docs for now (having in mind several differences described below).

### Library structure

All core modules are merged into a single repository.
Most of them will be rewritten and will be completely new (more on this below), but we're providing a Python version of old packages under torch.legacy namespace.
* torch           (torch)
* cutorch         (torch.cuda)
* nn              (torch.legacy.nn)
* cunn            (torch.legacy.cunn)
* optim           (torch.legacy.optim)
* nngraph         (torch.legacy.nngraph - not implemented yet)

### 0-based indexing

pytorch uses 0-based indexing everywhere.
This includes arguments to `index*` functions and nn criterion weights.

Under the hood, on the C side, we've changed logic on TH / THC / THNN / THCUNN to introduce a TH_INDEX_BASE compile-time definition to switch between 0 and 1 indexing logic.

### New Tensor API

**All methods operating on tensors are now out-of-place by default.**

This means that although `a.add(b)` used to have a side-effect of mutating the elements in a, it will now return a new Tensor, holding the result.
All methods that mutate the Tensor/Storage are now marked with a trailing underscore (including `copy` -> `copy_`, `fill` -> `fill_`, `set` -> `set_`, etc.).
Most of math methods have their in-place counterparts, so  an equivalent to `a.add(b)` in Lua is now `a.add_(b)` (or `torch.add(a, a, b)`, which is not recommended in this case)

### CUDA module

All tensors have their CUDA counterparts in torch.cuda module.

There is no `torch.cuda.setDevice` anymore. By default always the 0th device is selected, but code can be placed in a `with` statement to change it:

```python
with torch.cuda.device(1):
    a = torch.cuda.FloatTensor(10) # a is allocated on GPU1
```

Calling `.cuda()` on tensors no longer converts it to a GPU float tensor, but to a CUDA tensor of the same type located on a currently selected device.
So, for example: `a = torch.LongTensor(10).cuda() # a is a CudaLongTensor`

Calling `.cuda(3)` will send it to the third device.
`.cuda()` can be also used to transfer CUDA tensors between devices (calling it on a GPU tensor, with a different device selected will copy it into the current device).

```python
a = torch.LongTensor(10)
b = a.cuda()  # b is a torch.cuda.LongTensor placed on GPU0
c = a.cuda(2) # c is a torch.cuda.LongTensor placed on GPU2
with torch.cuda.device(1):
    d = b.cuda() # d is a copy of b, but on GPU1
    e = d.cuda() # a no-op, d is already on current GPU, e is d == True
```

Also, setting device is now only important to specify where to allocate new Tensors. You can perform operations on CUDA Tensors irrespective of currently selected device (but all arguments have to be on the same device) - result will be also allocated there. See below for an example:

```python
a = torch.randn(2, 2).cuda()
b = torch.randn(2, 2).cuda()
with torch.cuda.device(1):
    c = a + b                    # c is on GPU0
    d = torch.randn(2, 2).cuda() # d is on GPU1
```

In the near future, we also plan to use a CUDA allocator, which allows to alleviate problems with cudaMalloc/cudaFree being a sync point.
This will help us to not worry about using buffers for every intermediate computation in a module if one wants to do multi-GPU training, for example.
See: https://github.com/torch/cutorch/pull/443


### Numpy integration

Because numpy is a core numerical package in Python, and is used by many other libraries like matplotlib, we've implemented a two-way bridge between pytorch and numpy.

```python
a = torch.randn(2, 2)
b = a.numpy() # b is a numpy array of type corresponding to a
              # no memory copy is performed, they share the same storage
c = numpy.zeros(5, 5)
d = torch.DoubleTensor(c) # it's possible to construct Tensors from numpy arrays
              # d shares memory with b - there's no copy
```

### New neural network module

After looking at several framework designs, looking at the current design of `nn` and thinking through a few original design ideas, this is what we've converged to:

* Adopt a Chainer-like design
    * Makes it extremely natural to express Recurrent Nets and weight sharing
    * Each module can operate in-place, but marks used variables as dirty - errors will be raised if they're used again
* RNN example:

```python
class Network(nn.Container):
    def __init__(self):
        super(Network, self).__init__(
            conv1=nn.SpatialConvolution(3, 16, 3, 3, 1, 1),
            relu1=nn.ReLU(True),
            lstm=nn.LSTM(),
        )

    def __call__(self, input):
        y = self.conv(input)
        y = self.relu1(y)
        y = self.lstm(y)
        return y

model = Network()
input = nn.Variable(torch.zeros(256, 3, 224, 224))

output = model(input)

loss = 0
for i in range(ITERS):
    input, target = ...
    # That's all you need for an RNN
    for t in range(TIMESTEPS):
        loss += loss_fn(model(input), target)
    loss.backward()

```

* Here, nn.Variable will have a complete tape-based automatic differentiation implemented
* To access states, have hooks for forward / backward (this also makes multi-GPU easier to implement)
    * This has the advantage of not having to worry about in-place / out-of-place operators for accessing .output or .gradInput
* When writing the module, make sure debuggability is straight forward. Dropping into pdb and inspecting things should be natural, especially when going over the backward graph.
* Pulling handles to a module after constructing a chain should be very natural (apart from having a handle at construction)
    * It's easy, since modules are assigned as Container properties
* Drop overly verbose names. Example:
    * SpatialConvolution → conv2d
    * VolumetricConvolution → conv3d

#### Some notes on new nn implementation

As shown above, structure of the networks is fully defined by control-flow embedded in the code. There are no rigid containers known from Lua. You can put an `if` in the middle of your model and freely branch depending on any condition you can come up with. All operations are registered in the computational graph history.

There are two main objects that make this possible - variables and functions. They will be denoted as squares and circles respectively.

![Variable and function symbols](http://students.mimuw.edu.pl/~ap360585/__torch_img/variable_function.png)

Variables are the objects that hold a reference to a tensor (and optionally to gradient w.r.t. that tensor), and to the function in the computational graph that created it. Variables created explicitly by the user (`Variable(tensor)`) have a Leaf function node associated with them.

![Variable and leaf function](http://students.mimuw.edu.pl/~ap360585/__torch_img/variable_leaf.png)

Functions are simple classes that define a function from a tuple of inputs to a tuple of outputs, and a formula for computing gradient w.r.t. it's inputs. Function objects are instantiated to hold references to other functions, and these references allow to reconstruct the history of a computation. An example graph for a linear layer (`Wx + b`) is shown below.

![Linear layer](http://students.mimuw.edu.pl/~ap360585/__torch_img/linear.png)

Please note that function objects never hold references to Variable objects, except for when they're necessary in the backward pass. This allows to free all the unnecessary intermediate values. A good example for this is addition when computing e.g. (`y = Wx + My`):

![Freeing intermediate values](http://students.mimuw.edu.pl/~ap360585/__torch_img/intermediate_free.png)

Matrix multiplication operation keeps references to it's inputs because it will need them, but addition doesn't need `Wx` and `My` after it computes the result, so as soon as they go out of scope they are freed. To access intermediate values in the forward pass you can either copy them when you still have a reference, or you can use a system of hooks that can be attached to any function. Hooks also allow to access and inspect gradients inside the graph.

Another nice thing about this is that a single layer doesn't hold any state other than it's parameters (all intermediate values are alive as long as the graph references them), so it can be used multiple times before calling backward. This is especially convenient when training RNNs. You can use the same network for all timesteps and the gradients will sum up automatically.

To compute backward pass you can call `.backward()` on a variable if it's a scalar (a 1-element Variable), or you can provide a gradient tensor of matching shape if it's not. This creates an execution engine object that manages the whole backward pass. It's been introduced, so that the code for analyzing the graph and scheduling node processing order is decoupled from other parts, and can be easily replaced. Right now it's simply processing the nodes in topological order, without any prioritization, but in the future we can implement algorithms and heuristics for scheduling independent nodes on different GPU streams, deciding which branches to compute first, etc.

### Serialization

Pickling tensors is supported, but requires making a temporary copy of all data and breaks sharing.
For this reason we're providing `torch.load` and `torch.save`, that are free of these problems.
They have the same interfaces as `pickle.load` (file object) and `pickle.dump` (serialized object, file object) respectively.
For now the only requirement is that the file should have a `fileno` method, which returns a file descriptor number (this is already implemented by objects returned by `open`).

Objects are serialized in a tar archive consisting of four files:
`sys_info` - protocol version, byte order, long size, etc.
`pickle` - pickled object
`tensors` - tensor metadata
`storages` - serialized data

### Multi-GPU

Proposed solutions need to address:

* Kernel launch latency
    * without affecting the user's code
* Implementation should be as transparent as possible
    * Should we expose DPT as:
        * Split
        * ParallelApply (scheduling kernels in breadth first order, to address launch latency)
        * Join
* In backward phase, send parameters as soon as the module finishes computation

**Rough solution:**

```python
# This is an example of a network that has a data parallel part inside
#
#             B is data parallel
#     +->A+-->B+-+
#  +--+          +->D
#     +->C+------+
class Network(nn.Container):
    __init__(self):
        super(Network, self).__init__(
            A = ...,
            B = GPUReplicate(B, [0, 1, 2, 3]), # Copies the module onto a list of GPUs
            C = ...,
            D = ...
        )

    __call__(self, x):
        a = self.A(x)
        c = self.C(x)
        a_split = Split(a) # a_split is a list of Tensors placed on different devices
        b = ParallelApply(self.B, a_split) # self.B is a list-like object containing copies of B
        d_input = Join(b + [c]) # gathers Tensors on a single GPU
        return self.D(d_input)

```

Each module is assigned to a single GPU.

For Kernel Launch Latency:
* Python threading
* Generators

For parameter reductions ASAP:

* In the forward pass, register a hooks on a  every parameter which are evaluated as soon as the last backward is executed for that parameter. The hook will then “all-reduce” those parameters across GPUs
    * Problem with multiple forward calls - how do you know that the parameters won't be used anymore?
        * Well, last usage in backward graph = first usage in forward graph, so this should be straightforward


#### Multiprocessing

We plan to make it as straightforward as possible, to use pytorch in a multiprocessing environment.
For this, we plan to implement a .share() method for tensors that will enable them to be shared across processes seamlessly.
One can use [python multiprocessing](https://docs.python.org/2/library/multiprocessing.html) seamlessly.
"# how-to-debg_pytorch_sourcecode_into_cpp_part" 
