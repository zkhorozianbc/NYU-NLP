from nltk.stem.porter import PorterStemmer
import nltk
import scipy as sp
import numpy as np
from stop_list import closed_class_stop_words
import tensorflow as tf
import itertools
import math
import operator


class IRCran:

	def __init__(self):
		self.documents = {}
		self.queries = {}
		self.d_words = {}
		self.q_words = {}
		self.stemmer = PorterStemmer()
		self.train = {}
		self.test = {}
		self.docs_to_train = {}

	def read_cranqrel(self):
			
		f_cranqrel = open('cranqrel','r')

		for k in sorted(self.docs_to_train.keys()):
			if k <= 150:
				self.train[k] = {}
				self.train[k]["X"] = self.docs_to_train[k]
				self.train[k]["Y"] = []
			else:
				 self.test[k] = {}
				 self.test[k]["X"] = self.docs_to_train[k]
				 self.test[k]["Y"] = []


		for line in f_cranqrel:
			line = line.split()
			q_id = int(line[0])
			d_id = int(line[1])
			score = int(line[2])

			#handles missing query responses
			if q_id not in self.docs_to_train.keys():
				continue

			#create dict of ground truth labels, list of tuples with key=d_id value=relevance score
			if q_id <= 150:
				if score == -1:
					self.train[q_id]["Y"].insert(0,[d_id,1])
				else:
					self.train[q_id]["Y"].append([d_id,score])

			else:
				if score == -1:
					 self.test[q_id]["Y"].insert(0,[d_id,1])
				else:
					 self.test[q_id]["Y"].append([d_id,score])


		#initialize relevance levels of 5 to irrelevant docs as determined by cranqrel in test set
		for i in self.train.keys():
			marked = [x[0] for x in self.train[i]["Y"]]

			# for j in range(1,1401):
			for j in range(1,50):
				if j not in marked:
					train[i]["Y"].append([j,5])

			create d_id, score map
			self.train[i]["X_map"] = dict(self.train[i]["X"])
			self.train[i]["Y_map"] = dict(self.train[i]["Y"])


		for i in test.keys():
			marked = [x[0] for x in  self.test[i]["Y"]]

			# for j in range(1,1401):
			for j in range(1,50):
				if j not in marked:
					 self.test[i]["Y"].append((j,5))


			 self.test[i]["X_map"] = dict(self.test[i]["X"])
			 self.test[i]["Y_map"] = dict(self.test[i]["Y"])


		
	def read_text(self,filename,occur_dict,text_dict):
		f = open(filename,'r')

		id_to_update = 0
		read = False
		for line in f:
			line = line.split()

			if line[0] == ".I":
				
				#update occur dict, except on first iteration
				if id_to_update != 0:
					for word in list(set(text_dict[id_to_update])):

						word_count = text_dict[id_to_update].count(word)

						if word not in occur_dict.keys():
							occur_dict[word] = {}

						occur_dict[word][id_to_update] = word_count
							

				id_to_update = line[1]
				text_dict[id_to_update] = []
				read = False

			elif line[0] == ".W":
				read = True

			elif line[0] == ".T":
				read = True

			elif line[0] == ".A":
				read = False

			else:
				if read == True:

					#stem words exclude stop words, periods and commas
					line = [str(self.stemmer.stem(word)) for word in line if word not in closed_class_stop_words and len(word) > 1]

					for word in line:
						for letter in word:
							if letter.isalpha() == False:
								word = word.replace(letter,"")

					text_dict[id_to_update].extend(line)

		#handle last query
		for word in list(set(text_dict[id_to_update])):

			word_count = text_dict[id_to_update].count(word)

			if word not in occur_dict.keys():
				occur_dict[word] = {}

			occur_dict[word][id_to_update] = word_count

		f.close()



	def vectorize(self):
		f_output = open('f_output','w')

		num_queries = float(len(queries))
		num_documents = float(len(documents))
		q_index = 1
		for q_id in sorted(queries.keys()):

			query = self.queries[q_id]

			query_vector = {}
			query_length = float(len(query))

			#term frequency
			for word in list(set(query)):
				query_vector[word] = query.count(word) 

			#tf-idf
			for word in query_vector.keys():
				query_vector[word] *= np.log(num_queries / len(self.q_words[word]))


			document_vector_dict = {}

			#vectorize self.documents
			for d_id in self.documents.keys():

				document = self.documents[d_id]
				document_vector = {}
				doc_length = float(len(document))

				#handles empty self.documents
				if doc_length == 0:
					document_vector_dict[d_id] = 0
					continue

				#term frequency 
				for word in query_vector.keys():

					document_vector[word] = document.count(word)

				#tf-idf
				for word in document_vector.keys():
					if document_vector[word] > 0:

						document_vector[word] *= np.log(num_documents / len(self.d_words[word]))



				#features: cosine similarity, distance between non-stop words in doc
				d = []
				q = []
				for word in sorted(query_vector.keys()):
					d.append(document_vector[word])
					q.append(query_vector[word])

				if sum(d) > 0:
					document_vector_dict[d_id] = 1 - sp.spatial.distance.cosine(d,q)
					
				else:
					document_vector_dict[d_id] = 0

		

			ranking = sorted((k for k,v in document_vector_dict.iteritems()), reverse=True)



			# sort self.documents by cosine similarity score
			ranking = sorted(document_vector_dict,key=document_vector_dict.get,reverse=True)

			# remove unrelated self.documents where score = 0
			ranking = [rank for rank in ranking if document_vector_dict[rank] != 0]


			#write to output file
			for d_id in ranking:
				f_output.write(str(q_index) + " " + str(d_id) + " " + str(document_vector_dict[d_id]) + "\n")

			q_index += 1

		f_output.close()