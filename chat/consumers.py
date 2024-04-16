# chat/consumers.py
import os
import json
import anthropic
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        # Tritt der Gruppe bei
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()


    async def disconnect(self, close_code):
        # Verlässt die Gruppe
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )


    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        user_message = text_data_json['message']

        # Senden der Nutzereingabe an GPT und Empfangen der Antwort
        response = await self.get_claude_response(user_message)

        # Senden der GPT-Antwort an die Gruppe
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "chat_message", "message": response}
        )


    async def chat_message(self, event):
        # Sendet die Nachricht an WebSocket
        await self.send(text_data=json.dumps({
            'message': event['message']
        }))

        

    async def get_claude_response(self, user_message):

        with client.messages.stream(
            max_tokens=200,
            messages=[{"role": "user", "content": "Friedrich Schiller"}],
            model="claude-3-haiku-20240307",
        ) as stream:
            output=""
            for text in stream.text_stream:
                print(text, end="", flush=True)  # Gebe Texte nur aus, nachdem das Schluesselwort gefunden und das Stoppschluesselwort noch nicht gefunden wurde
                output += text
            
        print("\n\n")    
        return(output)