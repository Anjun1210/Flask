from google import genai

client = genai.Client(api_key='AIzaSyCbN6GjUiBSAbL4w-Hyzwa3ndEq1ubnNsM')

# 直接體驗最新一代的 3.5 Flash 
response = client.models.generate_content(
    model='gemini-3.5-flash',
    contents='台中市今天天氣如何',
)

print(response.text)
