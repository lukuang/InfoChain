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

import copy
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from random import randint


DICTIONARY = {}

def get_gpu_memory_map():
    """Get the current gpu usage.

    Returns
    -------
    usage: dict
        Keys are device ids as integers.
        Values are memory usage as integers in MB.
    """
    result = subprocess.check_output(
        [
            'nvidia-smi', '--query-gpu=memory.used',
            '--format=csv,nounits,noheader'
        ])
    # Convert lines into a dictionary
    gpu_memory = [int(x) for x in result.strip().split('\n')]
    gpu_memory_map = dict(zip(range(len(gpu_memory)), gpu_memory))
    return gpu_memory_map
    
def batchify(data, bsz,cuda):
    # Work out how cleanly we can divide the dataset into bsz parts.
    nbatch = data.size(0) // bsz
    # Trim off any extra elements that wouldn't cleanly fit (remainders).
    data = data.narrow(0, 0, nbatch * bsz)
    # Evenly divide the data across the bsz batches.
    data = data.view(bsz, -1).t().contiguous()

    if cuda:
        data = data.cuda()
    
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

def check_tagret(targets,required_word_index,position,eval_batch_size,bptt):
    for batch_position in range(eval_batch_size):
        for required_word_position in range(bptt):
            if targets[batch_position+required_word_position*eval_batch_size].data.cpu().numpy() == required_word_index:
                return required_word_position,batch_position
    return None, None

def evaluate_all(data_source,model,corpus,bptt,eval_batch_size):
    # Turn on evaluation mode which disables dropout.
    model.eval()
    criterion = nn.CrossEntropyLoss()
    total_loss = 0
    ntokens = len(corpus.dictionary)

    topic_generator = copy.deepcopy(model.topic_generator)
    smx = copy.deepcopy(model.smx)
    n_topics = model.n_topics
    topic_dist_stats = [[] for i in range(n_topics)]

    hidden = model.init_hidden(eval_batch_size)
    for i in range(0, data_source.size(0) - 1, bptt):
        data, targets = get_batch(data_source, i, bptt,evaluation=True)
        output, hidden = model(data, hidden)
        output_flat = output.view(-1, ntokens)
        total_loss += len(data) * criterion(output_flat, targets).data
        output_topic_decoded = topic_generator(hidden[0][-1])
        output_topic_dist =  smx(output_topic_decoded)
        for m in range(output_topic_dist.size(0)):
            for n in range(n_topics):
                value = float(output_topic_dist[m][n])
                topic_dist_stats[n].append(value)
        hidden = repackage_hidden(hidden)

    for j in range(n_topics):
        plt.hist(topic_dist_stats[j],10,rwidth=0.8)
        plt.savefig("%s.png" %(str(j)))
        plt.clf()

    return total_loss[0] / len(data_source)

def evaluate_small_sample(data_source,model,corpus,bptt,eval_batch_size,required_word_index, position,index):
    # Turn on evaluation mode which disables dropout.
    model.eval()
    criterion = nn.CrossEntropyLoss()
    total_loss = 0
    ntokens = len(corpus.dictionary)
    idx2word = corpus.dictionary.idx2word
    hidden = model.init_hidden(eval_batch_size)
    data, targets = get_batch(data_source, index, bptt,evaluation=True)
    output, hidden = model(data, hidden)
    output_flat = output.view(-1, ntokens)

    required_word_position, batch_position = check_tagret(targets,required_word_index,position,eval_batch_size,bptt)
    if required_word_position is not None:
        output_words = []
        target_words = []
        # print targets
        for i in range(bptt):
            word_output_vector = output_flat.data[batch_position+i*eval_batch_size]
            word_index = word_output_vector.max(0)[1]
            word_output = idx2word[int(word_index)]
            
            target_index = targets[batch_position+i*eval_batch_size]
            # print "target index %d" %(target_index)
            target_word = idx2word[int(target_index)]
            # print word_index

            output_words.append(word_output)
            target_words.append(target_word)
            # print "output word: %s" %() 
            # print "target word: %s" %() 
            if i == required_word_position:
                print "for target word %s" %(target_word)
                m = nn.Softmax(dim=0)
                input = torch.autograd.Variable(word_output_vector,requires_grad=False)
                softmax_output = m(input).data
                topk_values, topk_indecies = torch.topk(softmax_output,10,0)
                # topk_values = topk_values.view(-1,1)
                # topk_indecies = topk_indecies.view(-1,1)
                for k in range(topk_values.size(0)):
                    word = idx2word[topk_indecies[k]]
                    possiblility = topk_values[k]
                    print "\tword:{0} possiblility:{1:.3f}%".format(word,possiblility)


        print "output words: %s" %(" ".join(output_words))
        print "targetwords: %s" %(" ".join(target_words))
        # print output_flat.data[9]
        print '-'*10
        return True
    else:
        return False


    
    

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_dir_path")
    parser.add_argument("--word","-w",default="Nepal")
    parser.add_argument("--position","-p",type=int,default=5,
                    help="""
                        the position that the required word must be higher than
                    """)
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
    # train_data = batchify(corpus.train, training_config.batch_size)
    # val_data = batchify(corpus.valid, eval_batch_size)
    test_data = batchify(corpus.test, eval_batch_size,training_config.cuda)
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
        past_batch_index = set()
        number_of_sentence = 0
        word_index = corpus.dictionary.word2idx[args.word]
        print "The word index is:%d" %(word_index)
        print corpus.dictionary.idx2word[word_index]
        possible_indecies = range(0, test_data.size(0) - 1, training_config.bptt)
        while number_of_sentence < 5:
            i = randint(0, len(possible_indecies)-1)
            batch_index = possible_indecies[i]
            # print "batch index: %d" %(batch_index)
            succeed  = evaluate_small_sample(test_data,model,corpus,
                                             training_config.bptt,
                                             eval_batch_size, word_index,
                                             args.position, batch_index)
            if succeed:
                number_of_sentence += 1

if __name__=="__main__":
    main()

