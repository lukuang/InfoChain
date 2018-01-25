"""
evaluate on test data while outputing the output vector
"""

import os
import json
import sys
import re
import argparse
import codecs
import cPickle
import math
import torch
import torch.nn as nn
from torch.autograd import Variable
from collections import namedtuple
import data


DICTIONARY = {}

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
    data = Variable(source[i:i+seq_len], requires_grad=False)
    target = Variable(source[i+1:i+1+seq_len].view(-1))

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
    # print asdf

def evaluate_all(data_source,model,corpus,bptt,eval_batch_size):
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
        # print('output_flat size:', output_flat.data.size())
        # print output.data[0]
        total_loss += len(data) * criterion(output_flat, targets).data
        hidden = repackage_hidden(hidden)
    return total_loss[0] / len(data_source)

def evaluate_small_sample(data_source,model,corpus,bptt,eval_batch_size):
    # Turn on evaluation mode which disables dropout.
    model.eval()
    criterion = nn.CrossEntropyLoss()
    total_loss = 0
    ntokens = len(corpus.dictionary)
    idx2word = corpus.dictionary.idx2word
    hidden = model.init_hidden(eval_batch_size)
    data, targets = get_batch(data_source, 0, bptt,evaluation=True)
    output, hidden = model(data, hidden)
    output_flat = output.view(-1, ntokens)

    # print('output size:', output.data.size())
    # print('targets size:', targets.size())
    # print('output size:', output.data.size())
    # print('output_flat size:', output_flat.data.size())
    # print output.data[0]
    output_words = []
    target_words = []
    # print targets
    for i in range(bptt):
        word_output_vector = output_flat.data[5+i*eval_batch_size]
        word_index = word_output_vector.max(0)[1]
        word_output = idx2word[int(word_index)]
        
        target_index = targets[5+i*eval_batch_size]
        # print "target index %d" %(target_index)
        target_word = idx2word[int(target_index)]
        # print word_index

        output_words.append(word_output)
        target_words.append(target_word)
        # print "output word: %s" %() 
        # print "target word: %s" %() 

    print "output words: %s" %(" ".join(output_words))
    print '-'*10
    print "targetwords: %s" %(" ".join(target_words))
    print output_flat.data[9]
    

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_dir_path")
    parser.add_argument("-a","--all", action='store_true',
                    help='if specified, evaluate all test data')
    args=parser.parse_args()
    

    # Load the best saved model and the training configuration.
    model_path = os.path.join(args.model_dir_path,"model.ft")

    with open(model_path, 'rb') as f:
        model = torch.load(f)
    training_config = json.load(open( os.path.join(args.model_dir_path,"training.config") ))

    training_config = namedtuple( "TrainingConfig", training_config.keys())(**training_config)


    corpus_file = os.path.join(training_config.corpus_path,"corpus")
    if os.path.exists(corpus_file):
        with open(corpus_file, "rb") as cf:
            corpus = cPickle.load(cf)
    else:
        corpus = data.Corpus(training_config.corpus_path)
        with open(corpus_file, "wb") as cf:
            cPickle.dump(corpus, cf)

    eval_batch_size = 10
    train_data = batchify(corpus.train, training_config.batch_size)
    val_data = batchify(corpus.valid, eval_batch_size)
    test_data = batchify(corpus.test, eval_batch_size)
    # print test_data.size()
    # print test_data
    # sys.exit()
    # model.decoder.register_forward_hook(printnorm)

    # Run on test data.
    if args.all:
        test_loss = evaluate_all(test_data,model,corpus,training_config.bptt,eval_batch_size)
        print('=' * 89)
        print('| End of training | test loss {:5.2f} | test ppl {:8.2f}'.format(
            test_loss, math.exp(test_loss)))
        print('=' * 89)
    else:
        evaluate_small_sample(test_data,model,corpus,training_config.bptt,eval_batch_size)


if __name__=="__main__":
    main()

