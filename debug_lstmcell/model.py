import torch
import torch.nn as nn
from torch.autograd import Variable

class RNNModel(nn.Module):
    """Container module with an encoder, a recurrent module, and a decoder."""

    def __init__(self, rnn_type, ntoken, ninp, nhid, nlayers, dropout=0.5, tie_weights=False):
        super(RNNModel, self).__init__()
        self.drop = nn.Dropout(dropout)
        self.encoder = nn.Embedding(ntoken, ninp)
        if rnn_type != 'LSTM':
            raise NotImplemented("Only Implemented LSTM for debugging")
        else:
            rnn_type += "Cell" 
            self.first_rnn_cell = getattr(nn, rnn_type)(ninp, nhid)
            if nlayers > 1:
                self.subsequent_rnn_cell = nn.ModuleList([ getattr(nn, rnn_type)(nhid, nhid) for i in range(nlayers-1)])
            
        self.decoder = nn.Linear(nhid, ntoken)

        # Optionally tie weights as in:
        # "Using the Output Embedding to Improve Language Models" (Press & Wolf 2016)
        # https://arxiv.org/abs/1608.05859
        # and
        # "Tying Word Vectors and Word Classifiers: A Loss Framework for Language Modeling" (Inan et al. 2016)
        # https://arxiv.org/abs/1611.01462
        if tie_weights:
            if nhid != ninp:
                raise ValueError('When using the tied flag, nhid must be equal to emsize')
            self.decoder.weight = self.encoder.weight

        self.init_weights()

        self.rnn_type = rnn_type
        self.nhid = nhid
        self.nlayers = nlayers

    def init_weights(self):
        initrange = 0.1
        self.encoder.weight.data.uniform_(-initrange, initrange)
        self.decoder.bias.data.fill_(0)
        self.decoder.weight.data.uniform_(-initrange, initrange)

    def forward(self, input, hidden):
        emb = self.drop(self.encoder(input))
        hx = hidden[0]
        cx = hidden[1]
        for m in range(input.size(0)):
            new_hx, new_cx = self.first_rnn_cell(emb[0], (hx[0],cx[0]))
            new_hx = self.drop(new_hx)
            new_cx = self.drop(new_cx)
            new_hx = new_hx.unsqueeze(0)
            new_cx = new_cx.unsqueeze(0)

            if self.nlayers > 1:
                for n in range(1,self.nlayers):
                    layer_hx, layer_cx= self.subsequent_rnn_cell[n-1](hx[n-1], (hx[n], cx[n]) )
                    layer_hx = self.drop(layer_hx)
                    layer_cx = self.drop(layer_cx)
                    layer_hx = layer_hx.unsqueeze(0)
                    layer_cx = layer_cx.unsqueeze(0)

                    new_hx = torch.cat((new_hx.clone(),layer_hx.clone()))
                    new_cx = torch.cat((new_cx.clone(),layer_cx.clone()))
            

            # output, hidden = self.rnn(emb, hidden)
            output = new_hx[-1]

        output = self.drop(output)
        hidden = (new_hx, new_cx)
        print output.size()
        print self.decoder
	decoded = self.decoder(output.view(output.size(0)*output.size(1), output.size(2)))
        #print output.size()
        #print self.decoder.size()
        return decoded.view(output.size(0), output.size(1), decoded.size(1)), hidden

    def init_hidden(self, bsz):
        weight = next(self.parameters()).data
        if self.rnn_type == 'LSTMCell':
            return (Variable(weight.new(self.nlayers, bsz, self.nhid).zero_()),
                    Variable(weight.new(self.nlayers, bsz, self.nhid).zero_()))
        else:
            return Variable(weight.new(self.nlayers, bsz, self.nhid).zero_())
