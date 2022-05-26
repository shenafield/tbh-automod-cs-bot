import math
from dataclasses import dataclass

from .complete import Completer


@dataclass
class Message:
    author: str
    content: str


class Chat:
    def __init__(self):
        self.messages = []

    def send(self, author, content):
        self.messages.append(Message(author=author, content=content))

    def __str__(self):
        return "\n".join(
            f"{message.author}: {message.content}" for message in self.messages
        )


class Intervener:
    def __init__(self, completer: Completer, chat=None, questions=None, prompt_head=""):
        self.completer = completer
        if chat is None:
            self.chat = Chat()
        else:
            self.chat = chat
        if questions is None:
            questions = "\n\nQ: Is this chat going south?\nA: "
        if isinstance(questions, str):
            questions = [questions + "Yes", questions + "No"]
        self.questions = questions
        self.prompt_head = prompt_head

    @property
    def needed(self):
        chat_repr = str(self.chat)
        prompts = [self.prompt_head[max(0, len(chat_repr)-2048*5+len(self.prompt_head)):] + chat_repr + question for question in self.questions]
        log_probabilities = [self.completer.last_logprob(prompt) for prompt in prompts]
        probabilities = [math.e ** prob for prob in log_probabilities]
        normalized_probabilities = [prob / sum(probabilities) for prob in probabilities]
        return normalized_probabilities[0]
