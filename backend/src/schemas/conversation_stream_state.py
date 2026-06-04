class ConversationStreamState:
    def __init__(self):
        self.message_stream_started = False
        self.recipe_generation_started = False
        self.full_response = ""

    def start_message_stream(self):
        self.message_stream_started = True

    def end_message_stream(self):
        self.message_stream_started = False
        self.full_response = ""

    def start_recipe_generation(self):
        self.recipe_generation_started = True

    def end_recipe_generation(self):
        self.recipe_generation_started = False

    def add_message_chunk(self, chunk: str):
        self.full_response += chunk

    def reset(self):
        self.message_stream_started = False
        self.recipe_generation_started = False
        self.full_response = ""

    def has_message_stream_started(self) -> bool:
        return self.message_stream_started

    def has_recipe_generation_started(self) -> bool:
        return self.recipe_generation_started

    def get_full_response(self) -> str:
        return self.full_response
