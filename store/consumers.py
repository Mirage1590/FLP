import json
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import ChatMessage, ChatRoom
from django.contrib.auth.models import User


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["chat_box_name"]
        self.room_group_name = f"chat_{self.room_name}"

        # ✅ สร้างหรือดึงห้องแชทจากฐานข้อมูล
        self.room, _ = await sync_to_async(ChatRoom.objects.get_or_create)(name=self.room_name)

        # ✅ เข้าร่วมห้องแชท
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # ✅ ดึงข้อความเก่าและแปลง `datetime` เป็น `isoformat`
        previous_messages = await self.get_previous_messages()
        messages_serialized = [
            {
                "username": msg["sender__username"],
                "message": msg["message"],
                "timestamp": msg["timestamp"].isoformat()  # ✅ แปลง datetime เป็น string
            }
            for msg in previous_messages
        ]

        # ✅ ส่งข้อความเก่าไปยัง frontend
        await self.send(text_data=json.dumps({"previous_messages": messages_serialized}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data["message"]
        username = data.get("username", "Anonymous")

        # ✅ หาผู้ใช้
        try:
            user = await sync_to_async(User.objects.get)(username=username)
        except User.DoesNotExist:
            user = None  # ป้องกัน error ถ้าผู้ใช้ไม่มีอยู่จริง

        # ✅ บันทึกข้อความลงฐานข้อมูล
        chat_message = await self.save_message(user, message)

        # ✅ ส่งข้อความกลับไปยังทุกคนในห้อง
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "username": username,
                "message": message,
                "timestamp": chat_message.timestamp.isoformat()  # ✅ แปลง datetime เป็น string
            }
        )

    async def chat_message(self, event):
        message = event["message"]
        username = event["username"]
        timestamp = event["timestamp"]  # ✅ เพิ่ม timestamp

        await self.send(text_data=json.dumps({
            "message": message,
            "username": username,
            "timestamp": timestamp  # ✅ ส่ง timestamp ไปยัง frontend
        }))

    @sync_to_async
    def get_previous_messages(self):
        return list(ChatMessage.objects.filter(room=self.room)
                    .order_by("timestamp")
                    .values("sender__username", "message", "timestamp"))

    @sync_to_async
    def save_message(self, user, message):
        return ChatMessage.objects.create(room=self.room, sender=user, message=message)