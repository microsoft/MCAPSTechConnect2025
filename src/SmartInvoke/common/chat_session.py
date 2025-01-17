import datetime
import json
from textwrap import shorten

from common.cache_utils import CacheFactory, CacheType


class ChatSession:
    """
    A class that provides functionality for saving and loading chat history to and from a cache.
    """
    def __init__(self,redis_host, redis_password,user_history_retrieval_limit=None):
        """
        Initializes a new instance of ChatHistory.

        :param settings: The application settings.
        """
       
        self.cache = CacheFactory.get_cache(CacheType.REDIS,redis_host, redis_password)
        self._user_history_retrieval_limit = user_history_retrieval_limit

    def append_to_user_history(self, user_id, question, answer, timestamp=None):
        """
        Appends a user's question and answer to the chat history.

        :param user_id: The user's identifier.
        :param question: The user's question.
        :param answer: The system's answer.
        :param timestamp: The timestamp of the entry.
        """
        if timestamp is None:
            timestamp = str(datetime.datetime.now())

        trimmed_answer = self._trim_text(answer)

        # Construct the data dictionary
        #data = {"timestamp": timestamp, "question": question, "answer": trimmed_answer}
        data ={"timestamp": timestamp,"actor":"user",  "user question": question, "bot answer": trimmed_answer}
        # Convert the data to JSON
        json_data = json.dumps(data)

        context = self.get_current_domain_context(user_id)

        # Create a unique key for each user
        user_key = f"user:{user_id}{context}"

        # Append the user question and answer to the cache
        with self.cache as redis_cache:
            redis_cache.rpush(user_key, json_data)

    
    def append_to_user_history_system_message(self, user_id, message_type, message, timestamp=None):
        """
        Appends a user's question and answer to the chat history.

        :param user_id: The user's identifier.
        :param question: The user's question.
        :param answer: The system's answer.
        :param timestamp: The timestamp of the entry.
        """
        if timestamp is None:
            timestamp = str(datetime.datetime.now())

        trimmed_answer = self._trim_text(message)

        # Construct the data dictionary
        data = {"timestamp": timestamp,"actor":"system", "message_type": message_type, "message": trimmed_answer}

        # Convert the data to JSON
        json_data = json.dumps(data)

        context = self.get_current_domain_context(user_id)

        # Create a unique key for each user
        user_key = f"user:{user_id}{context}"

        # Append the user question and answer to the cache
        with self.cache as redis_cache:
            redis_cache.rpush(user_key, json_data)
    
    def get_user_history(self, user_id, context):
        """
        Retrieves a user's chat history.

        :param user_id: The user's identifier.
        :param context: The context/domain of the conversation.

        :return: A list containing the user's chat history.
        """
        # Create a unique key for each user
        user_key = f"user:{user_id}{context}"

        # Get all elements from the cache list
        with self.cache as redis_cache:
            if self._user_history_retrieval_limit is not None:
                user_history = redis_cache.lrange(user_key, 0 - self._user_history_retrieval_limit, -1)
            else:
                user_history = redis_cache.lrange(user_key, 0, -1)

        user_history = [json.loads(entry) for entry in user_history]

        return user_history

    def _trim_text(self, text, max_words=1500):
        """
        Trim the text to a certain number of words.

        :param text: The text to be trimmed.
        :param max_words: The maximum number of words to retain.

        :return: The trimmed text.
        """
        return shorten(text, width=max_words, placeholder="...")

    def clear_chat_history(self, user_id):
        """
        Clears a user's chat history.

        :param user_id: The user's identifier.
        """
        context = self.get_current_domain_context(user_id)
        user_key = f"user:{user_id}{context}"

        with self.cache as redis_cache:
            redis_cache.delete(user_key)

    def set_current_domain_context(self, user_id, context):
        """
        Sets the current domain context for a user.

        :param user_id: The user's identifier.
        :param context: The domain context.
        """
        self.clear_chat_history(user_id)
        user_key = f"user_context:{user_id}"

        with self.cache as redis_cache:
            redis_cache.write_to_cache(user_key, context)

    def get_current_domain_context(self, user_id):
        """
        Retrieves the current domain context for a user.

        :param user_id: The user's identifier.

        :return: The current domain context.
        """
        user_key = f"user_context:{user_id}"
        with self.cache as redis_cache:
            context = redis_cache.read_from_cache(user_key)

        return context if context is not None else "Procurement"
