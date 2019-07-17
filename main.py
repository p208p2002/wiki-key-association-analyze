# -!- coding: utf-8 -!-
import jieba
import jieba.posseg
# import jieba.analyse
import json
import os
from collections import Counter
import pickle

class KeyMatch():
    def __init__(self):        
        self.jsonData = '' # 原始json資料
        self.jsonDataWithSplit = [] # 句子分割        
        self.blackFlags = [] # 詞性過濾黑名單
        self.keyMatchRes = []
            
    def split(self, jsonDataPath, blackFlags=[]):        
        # 加載字典        
        jieba.initialize('dict/dict.txt.big')     
        jieba.load_userdict('dict/my_dict')
        jieba.load_userdict('dict/no_use_words')
        #
        self.blackFlags = blackFlags
        # 加載wiki json
        print('** 加載 wiki json **')
        self.__loadJson(jsonDataPath)        
        # 將文章分隔成句子
        print('** 開始分割文章 **')
        self.__splitArticleAsSentence(self.jsonData)        
        # 將句子分割成單詞，並且過濾指定詞性
        print('** 開始分割句子成單詞 **')
        self.__splitSentenceAsWords(self.jsonDataWithSplit, self.blackFlags)

    def match(self, key='', blackWords=[], subDir= ''):
        # 開始匹配
        print('** 開始關鍵字匹配 **')
        self.__matchKey(key, blackWords, subDir)
        print('** 完成 **')
    
    def getTop(self,n):
        return Counter(self.keyMatchRes).most_common(n)
  
    def __loadJson(self, jsonDataPath):
        with open(jsonDataPath, 'r',encoding="utf-8") as f:
            data = json.load(f)
        self.jsonData = data
    
    def __splitArticleAsSentence(self, jsonData):
        # 拆分句子
        data = jsonData        
        tmp = ''
        txtSplitAry = []
        
        index = 0
        while(True):
            try:
                for s in data[str(index)]:
                    if(s == '，' or s == '。'):
                        tmp = tmp.replace('\n','')
                        tmp = tmp.replace(' ','')
                        txtSplitAry.append(tmp)
                        tmp = ''
                    else:
                        tmp = tmp + s

                if(tmp != ''):
                    tmp = tmp.replace('\n','')
                    txtSplitAry.append(tmp)
                index += 1

            except:
                break
        
        self.jsonDataWithSplit = txtSplitAry
    
    def __splitSentenceAsWords(self, jsonDataWithSplit, blackFlags=[]):
        # 分詞&過濾詞性                
        segLists = []
        lenOfJsonDataWithSplit = len(jsonDataWithSplit)
        fileSerialNumber = 0
        for i in range(len(jsonDataWithSplit)):
            seg_list = jieba.posseg.lcut(jsonDataWithSplit[i])

            # 找到刪除目標
            delTarget = []
            for j in seg_list:
                word, flag = j
                if flag in blackFlags:
                    delTarget.append(j)
            
            # 刪除
            for j in delTarget:
                seg_list.remove(j)

            # 存回陣列                              
            segLists.append(seg_list)

            # 階段存檔
            if((i!=0 and i %10000 ==0) or (i!=0 and i == lenOfJsonDataWithSplit-1)):                
                # 抽離詞性
                dataOnlyAsWordsWithoutFlags = [] # 不含詞性的資料
                for k in segLists:            
                    onlyWords = []
                    for l in k:                
                        w,f = l
                        onlyWords.append(w)
                    dataOnlyAsWordsWithoutFlags.append(onlyWords)
                
                # 
                segLists = dataOnlyAsWordsWithoutFlags
                del dataOnlyAsWordsWithoutFlags
                
                # 儲存存檔                
                with open('./splitdata/seg_lists_'+str(fileSerialNumber)+'.pkl', 'wb') as f:
                    pickle.dump(segLists, f, protocol=pickle.HIGHEST_PROTOCOL)

                print('save:','seg_lists_'+str(fileSerialNumber)+'.pkl',i)
                
                # release mem
                del segLists                
                segLists = []
                fileSerialNumber += 1
        
        #
        try:
            del segLists
        except:
            pass

    def __matchKey(self, key, blackWords=[], subDir= ''):
        fileSN = 0
        totalFiles = 0
        fileBaseName = 'seg_lists_'
        fileRootPath = 'splitdata/' + subDir 
        jsonDataAsWords = [] # 讀入的資料存檔        
        keyMatchRes = [] # 與關鍵字匹配

        # 檢測檔案數量
        while(True):
            if os.path.isfile(fileRootPath + '/' + fileBaseName+str(totalFiles) + '.pkl'):
                totalFiles += 1
            else:                
                totalFiles -= 1                
                break        

        # 讀入存檔資料
        while(True):            
            try:
                with open(fileRootPath + '/' + fileBaseName + str(fileSN) + '.pkl', 'rb') as f:
                    jsonDataAsWords = pickle.load(f)
                print('matching:',str(fileSN) + '/' + str(totalFiles))
                fileSN += 1
                
                # 匹配關鍵字                
                for words in jsonDataAsWords:
                    if key in words:
                        for i in words:
                            if (i != key) and (not i in blackWords) and i != ' ':
                                keyMatchRes.append(i)
                    else:
                        continue
                del jsonDataAsWords                

            except:                
                break
        
        self.keyMatchRes = keyMatchRes
        

if __name__ == "__main__":
    # 自訂詞性黑名單
    with open('blacklists/flags.txt','r',encoding='utf-8') as f:
        data = f.read()
    blackFlags = data.split()

    # 自訂單詞黑名單
    with open('blacklists/words.txt','r',encoding='utf-8') as f:
        data = f.read()
    blackWords = data.split()

    # 單詞黑名單字典
    with open('blacklists/words.pkl', 'rb') as f:
        data = list(pickle.load(f))
    blackWords = blackWords + data

    # 配對關鍵字
    key = '蔡依林'

    # 維基資料
    # jsonFile = 'wikidata/wiki20180805_fullText.json'
    jsonFile = 'wikidata/wikidata_little.json'

    # 
    km = KeyMatch()
    # km.split(jsonDataPath = jsonFile ,blackFlags = blackFlags)
    km.match(key = key, blackWords = blackWords)
    # km.match(key = key, blackWords = blackWords, subDir = 'full')
    print(km.getTop(40))