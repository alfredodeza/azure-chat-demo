import os
from os.path import dirname
from dotenv import load_dotenv
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion


current_dir = dirname(os.path.abspath(__file__))
root_dir = dirname(dirname(current_dir))
env_file = os.path.join(root_dir, '.env')


async def main():
    # Initialize the kernel
    kernel = sk.Kernel()

    load_dotenv(env_file)
    deployment_name = os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"]
    endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
    api_key = os.environ["AZURE_OPENAI_API_KEY"]
    
    kernel.add_chat_service(
        "chat_completion",
        AzureChatCompletion(
            deployment_name=deployment_name,
            endpoint=endpoint,
            api_key=api_key)
    )

    # Import the WinePlugin from the plugins directory.
    plugins_directory = "./plugins"
    wine_plugin = kernel.import_semantic_skill_from_directory(
        plugins_directory, "WinePlugin"
    )

    # Run the wine pairing function
    result = await kernel.run_async(
        wine_plugin["Somellier"], input_str="White wine"
    )
    print(result)


# Run the main function
if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
