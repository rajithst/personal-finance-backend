
from django.conf import settings

from openai import OpenAI

from config.assistant_config import FINANCE_ASSISTANT_SYSTEM_MESSAGE
from oauth.middleware import get_current_user


class FinancialAgent:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.client = OpenAI(api_key=self.api_key)

    def get_query_from_prompt(self, prompt: str, categories: list[str], accounts: list[str]) -> str:
        """
        Convert a natural language prompt into a structured query.
        """
        system_message = FINANCE_ASSISTANT_SYSTEM_MESSAGE % (', '.join(categories), ', '.join(accounts))
        response = self.client.chat.completions.create(
            model="o4-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ]
        )
        query = response.choices[0].message.content if response.choices else None
        if not query:
            raise ValueError("No query generated from the prompt.")
        return self.prepare_query(query)

    def prepare_query(self, query: str, user) -> str:
        user = get_current_user()
        if not user or not user.id:
            raise ValueError("User ID is required in the request data.")
        if 't.user_id' not in query:
            raise ValueError("User ID placeholder ':user_id' not found in the query.")
        return query % user.id