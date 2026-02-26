from langchain_community.llms import LlamaCpp
from langchain_core.callbacks import CallbackManager, StreamingStdOutCallbackHandler
from langchain_core.prompts import PromptTemplate

# Optional: Set up streaming output
callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])

# Instantiate the LlamaCpp model
llm = LlamaCpp(
    model_path="/Users/gaan/Documents/kamal/python/rag_framework/models/Hermes-2-Pro-Llama-3-8B.Q4_K_M.gguf",  # Replace with your model path
    temperature=0.75,
    max_tokens=2000,
    n_ctx=4000,  # Context window size
    top_p=1,
    callback_manager=callback_manager,
    verbose=True,
    n_gpu_layers=-1,  # Uncomment to offload all layers to the GPU if compiled with GPU support
)

# Define a prompt template
prompt = PromptTemplate(
    template="Question: {question}\nAnswer:",
    input_variables=["question"],
)

# Create a simple chain
chain = prompt | llm

# Invoke the chain
question = "What are the benefits of running LLMs locally?"
print(chain.invoke({"question": question}))
