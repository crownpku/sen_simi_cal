#coding:utf-8
import jieba
from scipy import spatial
from gensim.models.keyedvectors import KeyedVectors
import pickle
import os
import SimpleHTTPServer, SocketServer
import urlparse
import urllib

PORT = 9112




def load_word2vec(vec_path = '/home/gwang3/workspace/chatbot/chinese_word2vec/cn.skipgram.bin'):
    return KeyedVectors.load_word2vec_format('/home/gwang3/workspace/chatbot/chinese_word2vec/cn.skipgram.bin', binary=True, unicode_errors='ignore')

def load_core_words(model, core_word_path = 'elec_core_word'):
    core_word_list = []
    infile = open(core_word_path)
    for line in infile:
        line = line.strip().decode('utf-8')
        if line in model:
            core_word_list.append(line)
    return core_word_list


#Core function to calculat sentence vector
def cal_sen_vec(sentence, core_word_list, model, debug=False):
    seg_org_list = jieba.cut(sentence)
    seg_list = []
    for sen_seg in seg_org_list:
        sen_seg = sen_seg.strip()
        if sen_seg == '':
            continue
        seg_list.append(sen_seg)
    if debug:
        print seg_list
        
    vec = []
    for n, item in enumerate(core_word_list):
        #print n
        max_simi = 0
        for sen_seg in seg_list:
            simi_tmp = 0
            try:
                simi_tmp = model.similarity(item, sen_seg)
            except Exception as e:
                #print e
                simi_tmp = 0
            if simi_tmp > max_simi:
                max_simi = simi_tmp
        vec.append(max_simi)
    if debug:
        print vec
    return vec


#Core QA Dic Format:
#core_qa_dic[question][0] = question_vector
#core_qa_dic[question][1] = answer
def load_core_qa(core_word_list, model, core_qa_path = 'elec_core_qa'):
    core_qa_dic = {}
    infile = open(core_qa_path)
    for n, line in enumerate(infile):
        if n % 100 == 0:
            print "Processing Question No." + str(n)
        line = line.strip().split('|')
        question = line[0].strip().decode('utf-8')
        answer = line[1].strip().decode('utf-8')
        if question == '' or answer == '':
            continue
        core_qa_dic[question] = []
        core_qa_dic[question].append(cal_sen_vec(question, core_word_list, model))
        core_qa_dic[question].append(answer)
    return core_qa_dic
    
#Very interesting question: How to transform vector quetion and vector target for our problem?

def cal_cos_simi(vec_q, vec_core):
    threshold = 0.5
    lenth = len(vec_q)
    count = 0
    newvec1 = []
    newvec2 = []
    for i in range(lenth):
        #if vec1[i] < threshold:
        #    vec1[i] = 0
        #if vec2[i] < threshold:
        #    vec2[i] = 0
        if vec_q[i] > threshold or vec_core[i] > threshold:
            newvec1.append(vec_q[i])
            newvec2.append(vec_core[i])
    return (1 - spatial.distance.cosine(newvec1, newvec2))


#def cal_cos_simi(vec_q, vec_core):
#    return (1 - spatial.distance.cosine(vec_q, vec_core))

def find_best_answer(question, core_qa_dic, core_word_list, model):
    q_vec = cal_sen_vec(sentence = question, core_word_list = core_word_list, model = model, debug = False)
    #print q_vec
    max_simi = 0
    best_q = ''
    for item in core_qa_dic:
        tmp_simi = cal_cos_simi(q_vec, core_qa_dic[item][0])
        if tmp_simi > max_simi:
            max_simi = tmp_simi
            best_q = item
    
    print "Similarity is:"
    print max_simi
    if max_simi == 0:
        return u"抱歉，我没办法回答您的这个问题。。。" #No question found
    print "Best Matched Question is:"
    print best_q
    return core_qa_dic[best_q][1]
            
def save_obj(obj, name ):
    with open(name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def load_obj(name ):
    with open(name + '.pkl', 'rb') as f:
        return pickle.load(f)
    
#Initializting
print 'Loading Word2vec Model...'
model = load_word2vec()
print 'Loading core words...'
core_word_list = load_core_words(model = model)
print 'Generating core questions and answers...'
if os.path.isfile('core_qa.pkl'):
    core_qa_dic = load_obj('core_qa')
else:
    core_qa_dic = load_core_qa(core_word_list = core_word_list, model = model)
    save_obj(core_qa_dic, 'core_qa')
    
    
    
#Class for handling http query and send answer
class MyHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        SimpleHTTPServer.SimpleHTTPRequestHandler.end_headers(self)
        
    def log_message(self, format, *args):
        pass

    def do_GET(self):

        # Parse query data & params to find out what was passed
        parsedParams = urlparse.urlparse(self.path)
        #queryParsed = urlparse.parse_qs(parsedParams.query)
        
        # request is either for a file to be served up or our test
        query_string = parsedParams.path
       
        self.processMyRequest(query_string)
       

    def processMyRequest(self, query_string):
        self.send_response(200)
        query_string = urllib.unquote(query_string).decode('utf-8').split(':')
        if len(query_string)<=1:
            return
        query_string = query_string[1]
        print "Your Question is:"
        print query_string
        answer = find_best_answer(query_string, core_qa_dic, core_word_list, model)
        print "Best Answer is:"
        print answer
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        #self.wfile.write("Hello world! " + query_string.encode());
        self.wfile.write(answer.encode('utf-8'));
        self.wfile.close();
        
        
    
    
Handler = MyHandler
httpd = SocketServer.TCPServer(("", PORT), Handler)
print "Serving at port " +  str(PORT)
httpd.serve_forever()

