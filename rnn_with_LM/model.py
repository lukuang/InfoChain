import torch
import torch.nn as nn
from torch.autograd import Variable

class RNNModel(nn.Module):
    """Container module with an encoder, a recurrent module, and a decoder."""

    def __init__(self, rnn_type, ntoken, ninp, nhid, nlayers, dropout=0.5, tie_weights=False,n_topics=2):
        super(RNNModel, self).__init__()
        self.drop = nn.Dropout(dropout)
        self.n_topics = n_topics
        print "There are %d topics" %(n_topics)
        self.encoder = nn.ModuleList([nn.Embedding(ntoken, ninp) for i in range(n_topics)])
        self.decoder = nn.ModuleList([nn.Linear(nhid, ntoken) for i in range(n_topics)])
        self.smx = nn.Softmax(dim=1)
        self.topic_generator = nn.Linear(nhid, self.n_topics)
        

        if rnn_type in ['LSTM', 'GRU']:
            rnn_type += 'Cell'
            self.first_rnn_cell = getattr(nn, rnn_type)(ninp, nhid)
            if nlayers > 1:
                self.subsequent_rnn_cell = nn.ModuleList([ getattr(nn, rnn_type)(nhid, nhid) for i in range(nlayers-1)])
            
            # self.rnn = getattr(nn, rnn_type)(ninp, nhid, nlayers, dropout=dropout)
        else:
            raise NotImplemented("Raw RNN is not implemented!")
            try:
                nonlinearity = {'RNN_TANH': 'tanh', 'RNN_RELU': 'relu'}[rnn_type]
            except KeyError:
                raise ValueError( """An invalid option for `--model` was supplied,
                                 options are ['LSTM', 'GRU', 'RNN_TANH' or 'RNN_RELU']""")
            self.rnn = nn.RNN(ninp, nhid, nlayers, nonlinearity=nonlinearity, dropout=dropout)


        # Optionally tie weights as in:
        # "Using the Output Embedding to Improve Language Models" (Press & Wolf 2016)
        # https://arxiv.org/abs/1608.05859
        # and
        # "Tying Word Vectors and Word Classifiers: A Loss Framework for Language Modeling" (Inan et al. 2016)
        # https://arxiv.org/abs/1611.01462
        if tie_weights:
            if nhid != ninp:
                raise ValueError('When using the tied flag, nhid must be equal to emsize')
            for i in range(n_topics):
                self.decoder[i].weight = self.encoder[i].weight

        self.init_weights()

        self.rnn_type = rnn_type
        self.ntoken = ntoken
        self.nhid = nhid
        self.ninp = ninp
        self.nlayers = nlayers

    def init_weights(self):
        initrange = 0.1
        for i in range(self.n_topics):

            self.encoder[i].weight.data.uniform_(-initrange, initrange)
            self.decoder[i].bias.data.fill_(0)
            self.decoder[i].weight.data.uniform_(-initrange, initrange)

        self.topic_generator.weight.data.uniform_(-initrange, initrange)

    def forward(self, input, hidden):
        if self.rnn_type == 'LSTMCell':
            hx = hidden[0]
            cx = hidden[1]
            # print input.size()
            # print "hx size: " + str(hx.size())
            for m in range(input.size(0)):
                input_topic_decoded = self.topic_generator(self.drop(hx[0]))
                input_topic_dist =  self.smx(input_topic_decoded)
                # print "topic dist size: "+str(input_topic_dist.size())
                # print input_topic_dist
                dropout_input = self.drop(input[m])
                for i in range(self.n_topics):
                    topic_emb = self.encoder[i](dropout_input)
                    for j in range(input_topic_dist.size(0)):
                        topic_emb[j] = topic_emb[j].clone().mul(input_topic_dist[j][i])
                    if i == 0:
                        emb = topic_emb.clone()
                    else:
                        emb = emb.clone().add( topic_emb)

                new_hx, new_cx = self.first_rnn_cell(emb.clone(), (hx[0].clone(), cx[0].clone()) )
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

                output_topic_decoded = self.topic_generator(new_hx[-1])
                output_topic_dist =  self.smx(output_topic_decoded)

                

                # decoded = Variable( torch.FloatTensor(output_topic_dist.size(0),self.ntoken).zero_() )
                output_hx = self.drop(new_hx[-1])
                for i in range(self.n_topics):
                    topic_decoded = self.decoder[i](output_hx)
                    for j in range(output_topic_dist.size(0)):
                        topic_decoded[j] = topic_decoded[j].clone().mul(output_topic_dist[j][i])
                    # print topic_decoded.size()
                    if i ==0:
                        decoded = topic_decoded.clone()
                    else:
                        decoded = decoded.clone().add( topic_decoded)
                
                decoded = decoded.unsqueeze(0)
                if m == 0:
                    output = decoded.clone()
                else:
                    output = torch.cat((output.clone(),decoded.clone()))
                hx = new_hx
                cx = new_cx
            # decoded = self.decoder(output.view(output.size(0)*output.size(1), output.size(2)))
            # topic_decoded = self.topic_generator(output.view(output.size(0)*output.size(1), output.size(2)))
            # topic_distribution = self.smx(topic_decoded).view(output.size(0), output.size(1),topic_decoded.size(1))
            return output , (new_hx, new_cx)

    def init_hidden(self, bsz):
        weight = next(self.parameters()).data
        if self.rnn_type == 'LSTMCell':
            return (Variable(weight.new(self.nlayers, bsz, self.nhid).zero_()),
                    Variable(weight.new(self.nlayers, bsz, self.nhid).zero_()))
        else:
            return Variable(weight.new(self.nlayers, bsz, self.nhid).zero_())
