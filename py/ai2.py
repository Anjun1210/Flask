from google import genai

client = genai.Client(api_key='AIzaSyCbN6GjUiBSAbL4w-Hyzwa3ndEq1ubnNsM')
question = input("請輸入您要問AI的問題")
# 直接體驗最新一代的 3.5 Flash 
response = client.models.generate_content(
    model='gemini-3.5-flash',
    contents=question,
)

print(response.text)
