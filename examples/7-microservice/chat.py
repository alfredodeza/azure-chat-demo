from dotenv import load_dotenv
import os
import json
from os.path import dirname
import requests
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.skill_definition import sk_function, sk_function_context_parameter
from semantic_kernel.orchestration.sk_context import SKContext


current_dir = dirname(os.path.abspath(__file__))
env_file = os.path.join(current_dir, '.env')


# Native Python function that can work with the Kernel
def travel_weather(city=None, month=None) -> str:
    microservice_url = "http://127.0.0.1:8000"

    result = requests.get(f"{microservice_url}/countries/Portugal/{city}/{month}").json()

    print(f"The average high temperature in {city} in {month} is {result['high']} degrees.")

native_functions = {"travel_weather": travel_weather}

async def main():
    # Load the .env file. Replace the path with the path to your .env file.
    load_dotenv(env_file)
    deployment_name = os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"]
    endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
    api_key = os.environ["AZURE_OPENAI_API_KEY"]

    kernel = sk.Kernel(log=sk.NullLogger())
    kernel.add_chat_service(
        "chat-gpt",
        AzureChatCompletion(
            deployment_name=deployment_name,
            endpoint=endpoint,
            api_key=api_key,
            api_version="2023-07-01-preview"
        )
    )

    prompt_config = sk.PromptTemplateConfig.from_completion_parameters(
        max_tokens=2000,
        temperature=0.7,
        top_p=0.8,
        function_call="auto",
        chat_system_prompt="You are a travel weather chat bot. Your name is Frederick. You are trying to help people find the average temperature in a city in a month.",
    )
    prompt_template = sk.ChatPromptTemplate(
        "{{$user_input}}", kernel.prompt_template_engine, prompt_config
    )


    function_config = sk.SemanticFunctionConfig(prompt_config, prompt_template)
    chat_function = kernel.register_semantic_function("ChatBot", "Chat", function_config)
    functions = [
        {
            "name": "travel_weather",
            "description": "Finds the average temperature for a city in a month.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The city for example Madrid",
                    },
                    "month": {
                        "type": "string",
                        "description": "The month of the year, for example June",
                    },
                },
                "required": ["city", "month"],
            },
        }
    ]
    context = kernel.create_new_context()

    context.variables["user_input"] = "I'm travelling to Madrid, and it seems that it would happen in January. What would be the average temperature?"
    context = await chat_function.invoke_async(context=context, functions=functions)

    if context.error_occurred:
        print(f"Error occurred: {context.last_error_description}")
        return

    if function_call := context.objects.pop('function_call', None):
        print(f"Function to be called: {function_call.name}")
        print(f"Function parameters: \n{function_call.arguments}")
        arguments = json.loads(function_call.arguments)
        function_to_call = native_functions[function_call.name]
        function_to_call(**arguments)


# Run the main function
if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
