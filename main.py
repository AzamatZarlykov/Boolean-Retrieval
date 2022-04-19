import os

from bs4 import BeautifulSoup

class InvertedIndex:
    def __init__(self, directory="A2/documents_cs") -> None:
        self.inverted_index = {}

        for filename in os.listdir(directory):
            if filename == "czech.dtd":
                continue
            file_path = os.path.join(directory, filename)

            with open(file_path, 'r', encoding="utf8") as f:
                file = f.read()

            soup = BeautifulSoup(file, 'xml')
            documents = soup.find_all("DOC")

            self.generate_inverted_index(documents)
        
    
    def generate_inverted_index(self, documents):
        """
            Takes documents from each file and stores terms 
            to their corresponding documents ids
        """
        for document in documents:
            doc_id = document.DOCID.text
            self.populate_inverted_index(document, doc_id)

    def populate_inverted_index(self, document, doc_id):
        """
            Takes the document and gets the text from TITLE,
            HEADING and TEXT tags. By tokenizing them,
            stores the terms to the dictionary with the doc_id
        """
        content = ""
        content += self.collect_content(document.find_all("TITLE"))
        content += self.collect_content(document.find_all("HEADING"))
        content += self.collect_content(document.find_all("TEXT"))

        term = ""
        for char in content:
            if char.isnumeric() or char.isalpha():
                term += char
            else:
                if term.strip() == "":
                    continue

                if term in self.inverted_index:
                    self.inverted_index[term].add(doc_id)
                else:
                    # if term does not exist in the dict add a new set and add the doc_id
                    self.inverted_index[term] = set()
                    self.inverted_index[term].add(doc_id)
                
                term = ""
        
    def collect_content(self, container):
        """
            this method is used to scrap the text from the provided tag/container
        """
        res = ""
        for elem in container:
            if elem is not None:
                res += elem.text
        return res

class Query:
    def __init__(self, directory="A2") -> None:
        self.queries = []
        self.nums = []
        self.directory = ""

        file_path = os.path.join(directory, "queries_cs.xml")

        with open(file_path, 'r', encoding="utf8") as f:
            file = f.read()

        soup = BeautifulSoup(file, 'xml')
        query_topics = soup.find_all("top")

        self.store_queries(query_topics)

        # create output directory if doesn't exist
        if not os.path.exists(self.directory):
            os.mkdir(self.directory)

    def store_queries(self, topics):
        """
            Traverses over the topics, accesses the query element 
            and stores as a string to a query field
        """
        for topic in topics:
            if topic.query is None:
                continue

            path = topic.num.text.split('/')

            self.nums.append(path[1])
            self.directory = path[0]

            self.queries.append(topic.query.text)
            

class QueryEvaluator:
    def __init__(self) -> None:
        self.values = []
        self.ops =[]

    def evaluate(self, query, inverted_index):
        """
            iterates over the elements in the splitted query and performs the infix
            expression evaluator using 2 stacks: values and operations
        """
        for elem in query:
            if self.is_operator(elem):
                while (len(self.ops) != 0 and self.precedence(self.ops[-1]) >= self.precedence(elem)):
                    val1 = self.values.pop()
                    val2 = self.values.pop()
                    op = self.ops.pop()

                    self.values.append(self.perform_operation(val1, val2, op))
                
                self.ops.append(elem)
            else:
                # if a token
                if elem in inverted_index:
                    postings = inverted_index[elem]
                else:
                    postings = set()
                self.values.append(postings)
                
        # perform remaining operations on the self.ops stack
        while (len(self.ops) != 0):
            first_op = self.ops.pop()
            val1 = self.values.pop()
            val2 = self.values.pop()
            
            if first_op == "NOT":
                _ = self.ops.pop()
                self.values.append(self.perform_operation(val1, val2, "difference"))
            else:
                self.values.append(self.perform_operation(val1, val2, first_op))

        return self.values[-1]
    

    def precedence(self, op):
        """
            returns the precedence of the operator. 
            NOT has higher precedence than AND and OR
        """
        if op == "AND" or op == "OR":
            return 1
        return 2

    def is_operator(self, elem):
        """
            returns true if the elem is an operator
        """
        return elem == "AND" or elem == "OR" or elem == "NOT"

    
    def perform_operation(self, posting1, posting2, op):
        """
            this method performs the operation over passed sets
            based on the boolean operator
        """
        if op == "AND":
            return posting1.intersection(posting2)
            # return intersection(posting1, posting2)
        elif op == "OR":
            return posting1.union(posting2)
            # return union(posting1, posting2)
        else:
            # difference (AND NOT)
            return posting2 - posting1
            # return difference(posting2, posting1)

    # def intersection(self, a, b):
    #     if len(a) > len(b):
    #         a,b = b,a
    #     res = set()
    #     for elem in a:
    #         if elem in b:
    #             res.add(elem)
    #     return res

    # def union(self, a, b):
    #     if len(a) > len(b):
    #         a,b = b,a
    #     for elem in a:
    #         if elem not in b:
    #             b.add(elem)
    #     return b   

    # def different(self, a, b):
    #     res = set()
    #     for elem in a:
    #         if elem not in b:
    #             res.add(elem)
    #     return res

def store(directory_name, file_name, result):
    """
        this method stores the docment ids to the given
        file path that is build using directory and file name
    """ 
    file_path = os.path.join(directory_name, file_name)

    with open(file_path, "w") as file:
        for doc_id in result:
            file.write(doc_id + '\n')

def main():
    inverted_index_holder = InvertedIndex()
    query_holder = Query()

    for query, num in zip(query_holder.queries, query_holder.nums):
        evaluator = QueryEvaluator()

        res = evaluator.evaluate(query.split(), inverted_index_holder.inverted_index)
        
        store(query_holder.directory, num, res)

    
if __name__ == "__main__":
    main()
