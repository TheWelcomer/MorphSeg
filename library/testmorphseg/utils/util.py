import torch


def make_mask_2d(lengths: torch.Tensor):
    """Create binary mask from lengths indicating which indices are padding"""
    # Make sure `lengths` is a 1d array
    assert len(lengths.shape) == 1

    max_length = torch.amax(lengths, dim=0).item()
    mask = torch.arange(max_length).expand(lengths.shape[0], max_length)  # Shape batch x timesteps
    mask = torch.ge(mask, lengths.unsqueeze(1))
    return mask


def make_mask_3d(source_lengths: torch.Tensor, target_lengths: torch.Tensor):
    """
    Make binary mask indicating which combinations of indices involve at least 1 padding element.
    Can be used to mask, for example, a batch attention matrix between 2 sequences
    """
    # Calculate binary masks for source and target
    # Then invert boolean values and convert to float (necessary for bmm later)
    source_mask = (~ make_mask_2d(source_lengths)).float()
    target_mask = (~ make_mask_2d(target_lengths)).float()

    # Add dummy dimensions for bmm
    source_mask = source_mask.unsqueeze(2)
    target_mask = target_mask.unsqueeze(1)

    # Calculate combinations by batch matrix multiplication
    mask = torch.bmm(source_mask, target_mask).bool()
    # Invert boolean values
    mask = torch.logical_not(mask)
    return mask


def softmax_2d(x: torch.Tensor, n_dims: int = 2, log: bool = True):
    """Softmax over last `n_dims` dimensions"""
    shape = x.shape
    # Fallen last `n_dims` dimensions of x
    flattened_shape = (*shape[:-n_dims], -1)
    x = torch.reshape(x, shape=flattened_shape).contiguous()

    if log:
        x = torch.log_softmax(x, dim=-1)
    else:
        x = torch.softmax(x, dim=-1)

    # Restore original shape
    x = torch.reshape(x, shape=shape)
    return x


def joint_softmax(distribution, log=True):
    shape = distribution.shape
    distribution = distribution.flatten()

    if log:
        normalised = torch.log_softmax(distribution, dim=0)
    else:
        normalised = torch.softmax(distribution, dim=0)

    distribution = normalised.reshape(*shape).contiguous()
    return distribution


def torch_index(seq, indexer):
    indexed_seq = [indexer[el] for el in seq]
    return torch.LongTensor(indexed_seq)


def move_to_cuda(var):
    if isinstance(var, torch.Tensor):
        return var.cuda()
    elif isinstance(var, list) or isinstance(var, tuple):
        return [tensor.cuda() for tensor in var]


def move_to_cpu(var):
    if isinstance(var, torch.Tensor):
        return var.cpu()
    elif isinstance(var, list) or isinstance(var, tuple):
        return [tensor.cpu() for tensor in var]
