import openai

class ChatGPT:
    def __init__(self) -> None:
        self.client = openai.OpenAI()
        self.dialog = []
    
    def question(self, prompt) -> str:
        completion = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a museum guide."},
                {"role": "user", "content": prompt}
            ]
            )
        print(completion.choices[0].message.content)
        return str(completion.choices[0].message.content)
