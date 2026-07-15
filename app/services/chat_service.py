from importlib import import_module

generator_module = import_module(
    "app.generator.rag_pipeline"
)

ask_rag = generator_module.ask_rag

def get_chat_response(question):

    answer = ask_rag(question)

    return answer