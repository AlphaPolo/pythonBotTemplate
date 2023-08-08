import ast
import csv
import os
import openai
from scipy import spatial
import tiktoken

from custom_api import CustomApi

openai.api_key = os.getenv("OPENAI_API_KEY", "")
GPT_MODEL = os.getenv("OPENAI_GPT_MODEL", "gpt-3.5-turbo")
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002")
SAVE_PATH = os.getenv("EMBEDDING_DATA_PATH", "embedding_data/ccwork_data.csv")
# TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", default = 0))
# FREQUENCY_PENALTY = float(os.getenv("OPENAI_FREQUENCY_PENALTY", default = 0))
# PRESENCE_PENALTY = float(os.getenv("OPENAI_PRESENCE_PENALTY", default = 0.6))
# MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", default = 240))

def read_csv_with_eval(file_path):
    result = []
    try:
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # 將 embedding 欄位轉換為實際的陣列
                row['embedding'] = ast.literal_eval(row['embedding'])
                result.append({'text': row['text'], 'embedding': row['embedding']})
    except FileNotFoundError as not_found:
        print(not_found.filename)
    return result

class ChatGPT:

    def __init__(self):
        self.data = read_csv_with_eval(SAVE_PATH)
        self.custom_api = CustomApi()

    def num_tokens(self, text: str, model: str=GPT_MODEL) -> int:
        """計算字串花費的Token數量"""
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))

    def strings_ranked_by_relatedness(
        self,
        query: str,
        df,
        relatedness_fn=lambda x, y: 1 - spatial.distance.cosine(x, y),
        top_n: int = 100
    ) -> tuple[list[str], list[float]]:
        """取的與query關聯的文章, 照關聯性排序"""
        query_embedding_response = openai.Embedding.create(
            model=EMBEDDING_MODEL,
            input=query,
        )
        query_embedding = query_embedding_response["data"][0]["embedding"]
        strings_and_relatednesses = [
            (row["text"], relatedness_fn(query_embedding, row["embedding"]))
            for row in df
        ]
        strings_and_relatednesses.sort(key=lambda x: x[1], reverse=True)
        strings, relatednesses = zip(*strings_and_relatednesses)
        return strings[:top_n], relatednesses[:top_n]

    def query_message(
        self,
        query: str,
        df,
        model: str,
        token_budget: int
    ) -> str:
        """製作與提問相關聯的文章Prompt"""
        strings, relatednesses = self.strings_ranked_by_relatedness(query, df)
        introduction = '使用下面的文章資料來回答關於創創集團的問題"'
        question = f"\n\nQuestion: {query}"
        message = introduction
        for string in strings:
            next_article = f'\n\n article section:\n"""\n{string}\n"""'
            if (
                self.num_tokens(message + next_article + question, model=model)
                > token_budget
            ):
                break
            else:
                message += next_article
        return message + question

    def get_completion(self, messages, model=GPT_MODEL):
        functions = self.custom_api.functions
        completion = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            functions=functions,
            function_call="auto",
            temperature=0,
        )
        return completion
    
    def answer_or_function_call(self, messages) -> str:
        while True:
            response = self.get_completion(messages)
            # print(response);

            if response.choices[0]["finish_reason"] == "stop":
                # print(response.choices[0]["message"]["content"])
                return response.choices[0]["message"]["content"]

            elif response.choices[0]["finish_reason"] == "function_call":
                fn_name = response.choices[0].message["function_call"].name
                arguments = response.choices[0].message["function_call"].arguments

                function_response = self.custom_api.execute_function(fn_name, arguments)

                messages.append(
                    {
                        "role": "assistant",
                        "content": None,
                        "function_call": {
                            "name": fn_name,
                            "arguments": arguments,
                        },
                    }
                )

                messages.append(
                    {
                        "role": "function", 
                        "name": fn_name, 
                        "content": f'{{"result": {str(function_response)} }}'
                    }
                )

                response = self.get_completion(messages)

            else:
                return '異常中止，請稍後再嘗試'


    def ask(
        self,
        query: str,
        model: str=GPT_MODEL,
        token_budget: int = 4096 - 500,
        print_message: bool = False,
    ) -> str:
        """Answers a query using GPT and a dataframe of relevant texts and embeddings."""
        data = self.data
        embedding_article = self.query_message(query, data, model=model, token_budget=token_budget)

        if print_message:
            print(embedding_article)

        messages = [
            {"role": "system", "content": 
            f"如果有關聯的文章則請根據文章回答問題\n\n{embedding_article}"},
            {"role": "user", "content": query},
        ]

        return self.answer_or_function_call(messages)

        






