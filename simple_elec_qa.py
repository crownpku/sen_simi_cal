#encoding = utf8
import jieba
from scipy import spatial
from gensim.models.keyedvectors import KeyedVectors

def load_word2vec(vec_path = '/home/gwang3/workspace/chatbot/chinese_word2vec/cn.skipgram.bin'):
    return KeyedVectors.load_word2vec_format('/home/gwang3/workspace/chatbot/chinese_word2vec/cn.skipgram.bin', binary=True, unicode_errors='ignore')

def load_core_words(core_word_path = 'elec_core_word'):
    core_word_list = []
    infile = open(core_word_path)
    for line in infile:
        core_word_list.append(line.strip())
    return core_word_list


#Core function to calculat sentence vector
def cal_sen_vec(sentence, core_word_list, model):
    seg_list = jieba.cut(sentence)
    #for item in seg_list:
    #    print item
    vec = []
    for item in core_word_list:
        max_simi = 0
        for sen_seg in seg_list:
            simi_tmp = 0
            try:
                simi_tmp = model.similarity(item, sen_seg)
            except Exception as e:
                print e
                simi_tmp = 0
            if simi_tmp > max_simi:
                max_simi = simi_tmp
        vec.append(max_simi)
    return vec


#Core QA Dic Format:
#core_qa_dic[question][0] = question_vector
#core_qa_dic[question][1] = answer
def load_core_qa(core_word_list, model, core_qa_path = 'elec_core_qa'):
    core_qa_dic = {}
    infile = open(core_qa_path)
    for line in infile:
        line = line.strip().split('|')
        question = line[0].strip()
        answer = line[1].strip()
        core_qa_dic[question] = []
        core_qa_dic[question].append(cal_sen_vec(question, core_word_list, model))
        core_qa_dic[question].append(answer)
    return core_qa_dic
    

def cal_cos_simi(vec1, vec2):
    return (1 - spatial.distance.cosine(vec1, vec2))

def find_best_answer(question, core_qa_dic, core_word_list, model):
    q_vec = cal_sen_vec(question, core_word_list, model)
    print q_vec
    max_simi = 0
    best_q = ''
    for item in core_qa_dic:
        tmp_simi = cal_cos_simi(q_vec, core_qa_dic[item][0])
        if tmp_simi > max_simi:
            max_simi = tmp_simi
            best_q = item
    print "Best Matched Question is:"
    print best_q
    print "Similarity is:"
    print max_simi
    return core_qa_dic[best_q][1]
            
    
def main():
    model = load_word2vec()
    core_word_list = load_core_words()
    core_qa_dic = load_core_qa(core_word_list = core_word_list, model = model)
    while(1):
        user_question = raw_input('###Please input your question (input "exit" to exit): ')
        if user_question == 'exit':
            return
        else:
            print "Your Question is:"
            print user_question
            answer = find_best_answer(user_question, core_qa_dic, core_word_list, model)
            print "Best Answer is:"
            print answer
    

if __name__ == '__main__':
    main()