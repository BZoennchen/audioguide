import openai

class ChatGPT:
    def __init__(self, age=16, interests='history', frequency='often') -> None:
        self.client = openai.OpenAI()
        self.dialog = []
        self.agents = ["museum guide", "football commentator", "story teller"]
        self.age = age
        self.interests = interests
        self.frequency = frequency

    def construct_prompt(self, user_prompt) -> str:
        system_message = f"you are an audio guide at an art exhibition, describe the works and more about the exhibition in the most interesting way possible. Use fluent language. Your visitor is {self.age} years old, they go to the museum {self.frequency}, they prefer X language, they want X answers, and they are interested in {self.interests}."

        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Beschreibe fliesend folgende Frage: {user_prompt}"}
            ],
        )
        
        return response.choices[0].message.content
        

    def construct_prompt_streamed(self, user_prompt) -> str:
        system_message = f"you are an audio guide at an art exhibition, describe the works and more about the exhibition in the most interesting way possible. Use fluent language. Your visitor is {self.age} years old, they go to the museum {self.frequency}, they prefer X language, they want X answers, and they are interested in {self.interests}."

        stream_response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Beschreibe fliesend folgende Frage: {user_prompt}"}
            ],
            stream=True
        )
        
        for chunk in stream_response:
            delta = chunk.choices[0].delta.content
            yield delta

    def question(self, user_prompt) -> str:
        return self.construct_prompt(user_prompt)

    def question_streamed(self, user_prompt) -> str:
        for response in self.construct_prompt_streamed(user_prompt):
            yield response
    

# Beispiel für die Verwendung
if __name__ == "__main__":
    # Hier müsstest du die ausgewählten Optionen aus dem HTML-Formular übergeben
    age = "erwachsen"
    interests = "Kunstgeschichte"
    frequency = "regelmäßig"

    chat_gpt = ChatGPT(age, interests, frequency)

    # Teste die Funktion mit einer Benutzeranfrage
    user_prompt = "Was ist die Bedeutung dieses Gemäldes?"
    response = chat_gpt.question(user_prompt)

    print(response)