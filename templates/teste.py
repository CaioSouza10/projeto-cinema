from google import genai

client = genai.Client(api_key="AIzaSyAYKAQhwUEIsGgptv9Gi-HYTcgMPBmIQrM")

for model in client.models.list():
    print(model.name)