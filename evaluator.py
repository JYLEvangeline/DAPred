import time
import torch
import torch.nn as nn
import torch.optim as optim
from utils import format_list_to_string
from torch.autograd import Variable
import numpy as np
use_cuda = torch.cuda.is_available()
# use_cuda = False

class Evaluator:
    def __init__(self, model, opt):
        self.model = model
        self.opt = opt

    def eval(self, test_data):
        hits = np.zeros(3)
        cnt = 0
        print(len(test_data))
        for idx,data_batch in enumerate(test_data):
            print("batch",str(idx))
            uids, vids_long, len_long, vids_short_al, len_short_al, tids_next, short_cnt, mask_long, vids_next, mask_optim, mask_evaluate = self.convert_to_variable(
                data_batch)
            hiddens_comb_masked, vid_candidates_masked = self.model(uids, vids_long, len_long, vids_short_al,
                                                                    len_short_al, tids_next, short_cnt, mask_long,
                                                                    mask_optim, mask_evaluate)
            hits_batch = self.get_hits(hiddens_comb_masked, vid_candidates_masked, vids_next)
            hits += hits_batch
            cnt += hiddens_comb_masked.size(0)
            print(hits/cnt)
        hits /= cnt
        print hits
        return hits

    def get_hits(self,hiddens_comb_masked, vid_candidates_masked, vids_next):
        hits = np.zeros(3)
        for idx in range(len(vid_candidates_masked)):
            probs_sorted, vid_sorted = torch.sort(hiddens_comb_masked[idx].view(-1), 0, descending=True)
            vid_ranked = [vid_candidates_masked[idx][id] for id in vid_sorted.data]
            for j in range(min(len(vid_ranked), 10)):
                if vids_next[idx] == vid_ranked[j]:
                    if j == 0:
                        hits[0] += 1
                    if j < 5:
                        hits[1] += 1
                    if j < 10:
                        hits[2] += 1
        return hits

    def convert_to_variable(self, data_batch):
        vids_long = Variable(data_batch[0])
        vids_short_al = Variable(data_batch[1])
        tids = Variable(data_batch[2])
        len_long = Variable(data_batch[3])
        len_short_al = Variable(data_batch[4])
        mask_long = Variable(data_batch[5])
        mask_optim = Variable(data_batch[6])
        tids_next = Variable(data_batch[8])
        uids = Variable(data_batch[9])
        # print uids
        test_idx = Variable(data_batch[10])
        short_cnt = Variable(data_batch[11])
        mask_evaluate = Variable(torch.zeros(0))
        # if there are records for evaluation
        if torch.sum(len_long - test_idx, 0).data[0] >   0:
        #if torch.sum(len_long - test_idx, 0).data[0, 0] > 0:
            mask_evaluate = mask_optim.clone()
            for uid in xrange(len_long.size(0)):
                for idx in xrange(len_long.data[uid, 0]):
                    if idx < test_idx.data[uid, 0]:
                        mask_evaluate.data[uid, idx] = 0
        vids_next = Variable(data_batch[7]).masked_select(mask_optim if len(mask_evaluate) == 0 else mask_evaluate)
        # print 'len_short_al: ', len_short_al
        # print 'len_long: ', len_long
        # print 'test_idx: ', test_idx
        # print 'vids_next: ', vids_next
        return uids, vids_long, len_long, vids_short_al, len_short_al, tids_next, short_cnt, mask_long, vids_next, mask_optim, mask_evaluate
        #if use_cuda:
        #    return uids.cuda(), vids_long.cuda(), len_long.cuda(), vids_short_al.cuda(), len_short_al.cuda(), tids_next, short_cnt.cuda(), mask_long.cuda(), vids_next.cuda(), mask_optim.cuda(), mask_evaluate.cuda()
        #else:
        #    return uids, vids_long, len_long, vids_short_al, len_short_al, tids_next, short_cnt, mask_long, vids_next, mask_optim, mask_evaluate