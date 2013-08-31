#!/usr/bin/python 
# -*- coding: utf-8 -*-

'''
 @desc   基于用户的协同过滤算法,方法为User-IIF
 @author cheng.cheng
 @email  cc@iamcc.me
 @date   2012-06-18
'''
import sys
import random
import math
from operator import itemgetter


def ReadData(file,data):
    ''' 读取评分数据
        @param file  评分数据文件
        @param data 储存评分数据的List
    '''
    for line in file:
        line = line.strip('\n')
        linelist = line.split("::")
        data.append([linelist[0],linelist[1]])

def SplitData(data, M, key, seed):
    ''' 将数据分为训练集和测试集
        @param data   储存训练和测试数据的List
        @param M      将数据分为M份
        @param key    选取第key份数据做为测试数据
        @param seed   随机种子
        @return train 训练数据集Dict
        @return test  测试数据集Dict
    '''
    test = dict ()
    train = dict ()
    random.seed(seed)
    for user,item in data:
        if random.randint(0,M) == key:
            if user in test:
                test[user].append(item)
            else:
                test[user] = []
        else:
            if  user in train:
                train[user].append(item)
            else:
                train[user] = []
    return train, test

def UserSimilarity(train):
    ''' 计算用户相似度
        @param train 训练数据集Dict
        @return W    记录用户相似度的二维矩阵
    '''
    #建立物品到用户之间的倒查表，降低计算用户相似度的时间复杂性
    item_users = dict()
    for u, items in train.items():
        for i in items:
            if(i not in item_users):
                item_users[i] = set()
            item_users[i].add(u)
        C = dict()
        N = dict()
        #计算用户之间共有的item的数目
        for i, users in item_users.items():
            for u in users:
                if(u not in N):
                    N[u] = 1
                N[u] += 1
                for v in users:
                    if u == v:
                        continue
                    if(u not in C):
                        C[u] = dict()
                    if(v not in C[u]):
                        C[u][v] = 0
                    #对热门物品进行了惩罚，采用这种方法被称做UserCF-IIF
                    C[u][v] += (1 / math.log(1+len(users)))
    W = dict()
    for u, related_users in C.items():
        for v, cuv in related_users.items():
            if(u not in W):
                W[u] = dict()
            #利用余弦相似度计算用户之间的相似度
            W[u][v] =  cuv / math.sqrt(N[u] * N[v])

    return W


def Coverage(train, test, W, N, K):
    ''' 获取推荐结果
        @param user  输入的用户
        @param train 训练数据集Dict
        @param W     记录用户相似度的二维矩阵
        @param N     推荐结果的数目
        @param K     选取近邻的数目
    '''
    recommned_items = set()
    all_items = set()

    for user in train.keys():
        for item in train[user]:
            all_items.add(item)

        rank = GetRecommendation(user, train, W, N, K)
        for item, pui in rank:
            recommned_items.add(item)

    #print 'len: ',len(recommned_items),'\n'
    return len(recommned_items) / (len(all_items) * 1.0)

def GetRecommendation(user, train ,W, N, K):
    ''' 获取推荐结果
        @param user  输入的用户
        @param train 训练数据集Dict
        @param W     记录用户相似度的二维矩阵
        @param N     推荐结果的数目
        @param K     选取近邻的数目
    '''
    rank = dict()
    interacted_items = train[user]
    #选取K个近邻计算得分
    for v,wuv in sorted(W[user].items(), key=itemgetter(1),\
        reverse = True)[0:K]:
        for i in train[v]:
            if i in interacted_items:
                continue
            if i in rank:
                rank[i] += wuv
            else:
                rank[i] = 0

    #取得分最高的N个item作为推荐结果 
    rank = sorted(rank.items(), key=itemgetter(1), reverse = True)[0:N]

    return rank

def Recall(train, test, W, N, K):
    ''' 计算推荐结果的召回率
        @param train 训练数据集Dict
        @param test  测试数据集Dict
        @param W     记录用户相似度的二维矩阵
        @param N     推荐结果的数目
        @param K     选取近邻的数目
    '''
    hit = 0
    all = 0
    for user in train.keys():
        if user in test:
            tu = test[user]
            rank = GetRecommendation(user, train, W, N, K)
            for item, pui in rank:
                if item in tu:
                    hit+= 1
            all += len(tu)
    #print(hit)
    #print(all)
    return hit/(all * 1.0)
        
def Precision(train, test, W, N, K):
    ''' 计算推荐结果的准确率
        @param train 训练数据集Dict
        @param test  测试数据集Dict
        @param W     记录用户相似度的二维矩阵
        @param N     推荐结果的数目
        @param K     选取近邻的数目
    '''
    hit = 0
    all = 0
    for user in train.keys():
        if user in test:
            tu = test[user]
            rank = GetRecommendation(user, train, W, N, K)
            for item, pui in rank:
                if item in tu:
                    hit+= 1
            all += N
    #print(hit)
    #print(all)
    return hit/(all * 1.0)

def Popularity(train, test, W, N, K):
    ''' 计算推荐结果的流行度
        @param train 训练数据集Dict
        @param test  测试数据集Dict
        @param W     记录用户相似度的二维矩阵
        @param N     推荐结果的数目
        @param K     选取近邻的数目
    '''
    item_popularity = dict()
    for user, items in train.items():
        for item in items:
            if item not in item_popularity:
                item_popularity[item] = 0
            item_popularity[item] += 1

    ret = 0
    n = 0
    for user in train.keys():
        rank = GetRecommendation(user, train, W, N, K)
        for item, pui in rank:
            ret += math.log(1+ item_popularity[item])
            n += 1
    ret /= n * 1.0
    return ret



if __name__ == '__main__':
     data = []
     M = 8
     key = 1
     seed = 1
     N = 10
     K = 80
     W = dict()
     rank = dict()

     print("this is the main function")
     file = open('./ml-1m/rat.dat')
     ReadData(file,data)
     train,test = SplitData(data, M, key, seed)
     W = UserSimilarity(train)
     recall = Recall(train, test, W, N, K)
     precision = Precision(train, test, W, N, K)
     popularity = Popularity(train, test, W, N, K)
     coverage = Coverage(train, test, W, N, K)
     print 'recall: ',recall,'\n'
     print 'precision: ',precision,'\n'
     print 'Popularity: ',popularity,'\n'
     print 'coverage: ', coverage,'\n'
else :
     print("this is not the main function")
