# coding=UTF-8
from __future__ import division
import re
import sys
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
import boilerpipe
from boilerpipe.extract import Extractor
import nltk.data
from nltk.corpus import stopwords
import urllib2
import pymongo
from pymongo import MongoClient

class SummaryTool(object):

    def __init__(self):
        self.ideal = 20.0
        self.stop = stopwords.words('english')

    # Naive method for splitting a text into sentences
    def split_content_to_sentences(self, content):
        #xyz = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s',content)
        tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
        xyz = tokenizer.tokenize(content)
        return xyz, len(xyz)
 
    # Format a sentence - remove all non-alphbetic chars from the sentence
    # We'll use the formatted sentence as a key in our sentences dictionary
    def format_sentence(self, sentence):
        sentence = re.sub(r'\W+', '', sentence)
        return sentence
 
    def getSentencePositionScore(self, i, sentenceCount):
        normalized = i / (sentenceCount * 1.0)

        if normalized > 0 and normalized <= 0.1:
          return 0.17
        elif normalized > 0.1 and normalized <= 0.2:
          return 0.23
        elif normalized > 0.2 and normalized <= 0.3:
          return 0.14
        elif normalized > 0.3 and normalized <= 0.4:
          return 0.08
        elif normalized > 0.4 and normalized <= 0.5:
          return 0.05
        elif normalized > 0.5 and normalized <= 0.6:
          return 0.04
        elif normalized > 0.6 and normalized <= 0.7:
          return 0.06
        elif normalized > 0.7 and normalized <= 0.8:
          return 0.04
        elif normalized > 0.8 and normalized <= 0.9:
          return 0.04
        elif normalized > 0.9 and normalized <= 1.0:
          return 0.15
        else:
          return 0

    def getTitleMatchingScore(self,sentence,title):

        wds = sentence.split()
        score = 0
        title_ref = [word.lower() for word in title.split() if word.lower() not in self.stop]
        for w in wds:
            if w.lower() in title_ref and w.lower() not in self.stop:
                score += 1
        return score/len(wds)

    def getLengthScore(self, sentence):
        return (self.ideal - abs(self.ideal - len(sentence))) / self.ideal

    def scoring(self, sentences,title, sentenceCount):
        err = 0
        tfidf_vectorizer = TfidfVectorizer(max_df=0.80, max_features=1000,min_df=0.05,use_idf=True,stop_words="english", ngram_range=(1,2))
        try:
            tfidf_matrix = tfidf_vectorizer.fit_transform(sentences)
            #terms = tfidf_vectorizer.get_feature_names()
            row_sum = tfidf_matrix.sum(axis=1)
            max = -1
            for m in range(len(row_sum)):
                if float(row_sum[m]) > max:
                    max = float(row_sum[m])
        except:
            err = 1
            pass

        sentences_dic = []
        if err == 0:
            for i in xrange(len(sentences)):
                if len(sentences[i]) != 0:
                    #Sentence Positioning Score calculated by calling the getSentencePositionScore method
                    sps = self.getSentencePositionScore(i, sentenceCount)
                    #Higher number of matching words with title give relevance to sentence...getTitleMatchingScore method
                    tms = self.getTitleMatchingScore(sentences[i], title)
                    #Length of score calculated by calling getLengthScore method. self.ideal set at 20(can be changed accordingly).
                    lenScore = self.getLengthScore(sentences[i])
                    #Final score calculated. Weightage also given, could be changed as per requirements.
                    sentences_dic.append((self.format_sentence(sentences[i]), ((2.0*(float(row_sum[i])/max) + 1*sps + 1.5*tms + 0.5*lenScore)/5)))

        return sentences_dic

    # Return the best sentence in a paragraph
    def get_sentence_ranks(self, content, sentences_dic):
 
        sentences = self.split_content_to_sentences(content)[0]
        newArr = []


        for s in sentences:
            strip_s = self.format_sentence(s)
            for i in xrange(len(sentences_dic)):
                if strip_s == sentences_dic[i][0]:
                    newArr.append((s,sentences_dic[i][1]))

        return newArr
 
    # Build the summary
    def get_summary(self, content, sentences_dic):
        summary = self.get_sentence_ranks(content, sentences_dic)
        return summary
 

def main():

    def doit(text):
        matches=re.findall(r'[.!?:]*?\s*.*?".*?[.!?]"',text)
        matches1 = re.findall(r'[.!?:]*?\s*.*?".*?".*?[.!?]',text)
        #m2 =  re.findall(r'[:!?]*?\s*.*?".*?[.!?]"',text)

        for m in matches1:
            matches.append(m)

        return matches

    err = 0

    dbclient = MongoClient().local
    db = dbclient['Urls']
    res_db = dbclient['Lines']
    

    if int(sys.argv[1]) == 1:
        number_of_sent = int(sys.argv[3])
        your_url = sys.argv[2]
        try:
            extractor = Extractor(extractor='ArticleExtractor', url=your_url)
            page = urllib2.urlopen(sys.argv[2])
            soup = BeautifulSoup(page.read())
            title = soup.title.string
            print title
        except:
            err = 1
            pass

        if err == 0:
            extracted_text = extractor.getText()




    else:
        number_of_sent = int(sys.argv[2])
        try:
            title = ""
            extracted_text = 'Bayern Munich signed Brazil midfielder Douglas Costa from Ukrainian side Shakhtar Donetsk on Wednesday."A dream has come true for me today," said Costa, who will join his new teammates on July 11. "I\'m proud to become a player for Bayern, following in the footsteps of so many magnificent Brazilian players."After joining Donetsk from Gremio in January 2010, Costa scored 38 goals in 203 competitive games and helped the side to five consecutive titles from 2010-14, as well as three Ukrainian Cup wins.'
        except:
            err = 1
            pass

    if err == 0:
        st = SummaryTool()
        final_summ = []

        initialQuotes = doit(extracted_text)
        scs = st.split_content_to_sentences(extracted_text)
        sen_test = scs[0]
        senCount = scs[1]
        score_sentences = st.scoring(sen_test, title, senCount)


        sen_quotes = []

        for q in initialQuotes:
            returned_sent_quotes = st.split_content_to_sentences(q)[0]
            for rsq in returned_sent_quotes:
                if rsq not in sen_quotes:
                    rsq = rsq.strip()
                    sen_quotes.append(rsq)



        summary = st.get_summary(extracted_text, score_sentences)

        final_summ_q = []
        if len(summary) > 0:
            for i in xrange(len(summary)):
                j = summary[i][0].strip()
                soupI = BeautifulSoup(j)
                text = soupI.getText()
                if text in sen_quotes:
                    for q in initialQuotes:
                        if text in q:
                            if q not in final_summ_q:
                                final_summ_q.append(q)
                                q = q.lstrip('.\n')
                                final_summ.append((q, summary[i][1]))

                            break
                else:
                    if text not in final_summ_q:
                        final_summ.append((text,summary[i][1]))
                        final_summ_q.append(text)

        final_summ_sorted = sorted(final_summ, key=lambda tup: tup[1],reverse=True)

        threshold_score = final_summ_sorted[min(number_of_sent-1,len(final_summ)-1)][1]

        counter = 0
        final = []
        for yo in xrange(len(final_summ)):
            if counter == number_of_sent:
                break
            if (final_summ[yo][1] >= threshold_score):
                final.append(final_summ[yo][0])
                counter += 1

        #for f in final:
        #   print '>> ' + f

        return final
if __name__ == '__main__':
    main()


