"""
evaluate on test data while outputing the output vector
"""

import os
import json
import sys
import re
import argparse
import codecs
import torch
import torch.nn as nn
from torch.autograd import Variable
from collections import namedtuple
import data

def batchify(data, bsz):
    # Work out how cleanly we can divide the dataset into bsz parts.
    nbatch = data.size(0) // bsz
    # Trim off any extra elements that wouldn't cleanly fit (remainders).
    data = data.narrow(0, 0, nbatch * bsz)
    # Evenly divide the data across the bsz batches.
    data = data.view(bsz, -1).t().contiguous()
    
    return data

def get_batch(source, i,bptt, evaluation=False):
    seq_len = min(bptt, len(source) - 1 - i)
    data = Variable(source[i:i+seq_len], volatile=evaluation)
    print  ("batch size ", data.size())
    target = Variable(source[i+1:i+1+seq_len].view(-1))
    print  ("batch target size " , target.size() )
    return data, target

def repackage_hidden(h):
    """Wraps hidden states in new Variables, to detach them from their history."""
    if type(h) == Variable:
        return Variable(h.data)
    else:
        return tuple(repackage_hidden(v) for v in h)


def printnorm(self, input, output):
    # input is a tuple of packed inputs
    # output is a Variable. output.data is the Tensor we are interested
    print('Inside ' + self.__class__.__name__ + ' forward')
    print('')
    print('input: ', type(input))
    print('input[0]: ', type(input[0]))
    print('output: ', type(output))
    print('')
    print('input size:', input[0].size())
    print('output size:', output.data.size())
    print('output norm:', output.data.norm())

def evaluate(data_source,model,corpus,bptt,eval_batch_size):
    # Turn on evaluation mode which disables dropout.
    model.eval()
    criterion = nn.CrossEntropyLoss()
    total_loss = 0
    ntokens = len(corpus.dictionary)
    hidden = model.init_hidden(eval_batch_size)
    for i in range(0, data_source.size(0) - 1, bptt):
        data, targets = get_batch(data_source, i, bptt,evaluation=True)
        output, hidden = model(data, hidden)
        output_flat = output.view(-1, ntokens)
        total_loss += len(data) * criterion(output_flat, targets).data
        hidden = repackage_hidden(hidden)
    return total_loss[0] / len(data_source)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_dir_path")
    parser.add_argument("--corpus_path", type=str,
                    help='location of the data corpus')
    parser.add_argument('--batch_size', type=int, default=20, metavar='N',
                    help='batch size')
    parser.add_argument('--bptt', type=int, default=35,
                    help='sequence length')
    args=parser.parse_args()
    

    # Load the best saved model and the training configuration.
    model_path = os.path.join(args.model_dir_path,"model.pt")

    with open(model_path, 'rb') as f:
        model = torch.load(f)
    training_config = json.load(open( os.path.join(args.model_dir_path,"training.config") ))

    training_config = namedtuple( "TrainingConfig", training_config.keys())(**training_config)

    corpus = data.Corpus(training_config.corpus_path)
    eval_batch_size = 10
    train_data = batchify(corpus.train, training_config.batch_size)
    val_data = batchify(corpus.valid, eval_batch_size)
    test_data = batchify(corpus.test, eval_batch_size)

    model.decoder.register_forward_hook(printnorm)

    # Run on test data.
    test_loss = evaluate(test_data,model,corpus,training_config.bptt,eval_batch_size)
    print('=' * 89)
    print('| End of training | test loss {:5.2f} | test ppl {:8.2f}'.format(
        test_loss, math.exp(test_loss)))
    print('=' * 89)


if __name__=="__main__":
    main()

