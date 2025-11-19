from app.config import settings
from openai import AzureOpenAI

print("Testing Azure OpenAI...")
print(f"Endpoint: {settings.azure_openai_endpoint}")
print(f"Deployment: {settings.azure_openai_deployment}")

client = AzureOpenAI(
    api_key=settings.azure_openai_api_key,
    api_version=settings.azure_openai_api_version,
    azure_endpoint=settings.azure_openai_endpoint,
)

response = client.chat.completions.create(
    model=settings.azure_openai_deployment,
    messages=[{"role": "user", "content": "Say 'Working!' if you can read this"}],
    max_completion_tokens=10,  # CHANGED: Use max_completion_tokens for GPT-4o/GPT-5
)

print(f"✅ Response: {response.choices[0].message.content}")
print("✅ Azure OpenAI is working!")
