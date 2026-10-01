import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Render se token lega
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

router = Router()

# States for FSM
class PostMaker(StatesGroup):
    waiting_for_content = State()
    waiting_for_button = State()
    waiting_for_channel = State()

@router.message(CommandStart())
async def start_cmd(message: Message, state: FSMContext):
    text = (
        "👋 *Welcome to the Post Maker Bot!*\n\n"
        "Main aapki madad karunga aisi posts banane mein jisme niche URL Buttons lage hon.\n\n"
        "Koi bhi is bot ko use kar sakta hai!\n"
        "👉 Post banana shuru karne ke liye /create dabayein."
    )
    await message.answer(text, parse_mode="Markdown")
    await state.clear()

@router.message(Command("create"))
async def create_post(message: Message, state: FSMContext):
    await state.set_state(PostMaker.waiting_for_content)
    await message.answer("📝 Sabse pehle mujhe wo **Text, Photo, ya Video** bhejiye jo aap post karna chahte hain.", parse_mode="Markdown")

@router.message(PostMaker.waiting_for_content)
async def get_content(message: Message, state: FSMContext):
    # Save the message data
    await state.update_data(
        text=message.html_text if message.text else message.caption,
        photo_id=message.photo[-1].file_id if message.photo else None,
        video_id=message.video.file_id if message.video else None
    )
    
    await state.set_state(PostMaker.waiting_for_button)
    instruction = (
        "✅ Content save ho gaya!\n\n"
        "🔗 Ab mujhe Button ka naam aur Link is format mein bhejiye:\n\n"
        "`Button Name - https://yourlink.com`\n\n"
        "*(Agar button nahi chahiye toh 'skip' likh kar bhej dein)*"
    )
    await message.answer(instruction, parse_mode="Markdown")

@router.message(PostMaker.waiting_for_button)
async def get_button(message: Message, state: FSMContext):
    kb = None
    if message.text.lower() != 'skip':
        try:
            btn_text, btn_url = message.text.split("-", 1)
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=btn_text.strip(), url=btn_url.strip())]
            ])
            # Keyboard ko state mein save kar lo
            await state.update_data(keyboard=kb)
        except ValueError:
            return await message.answer("❌ Format galat hai. Kripya aise bhejein:\n`Click Here - https://google.com`", parse_mode="Markdown")

    data = await state.get_data()
    
    # Preview dikhana
    await message.answer("👀 *Ye raha aapki Post ka Preview:*", parse_mode="Markdown")
    
    if data.get("photo_id"):
        await message.answer_photo(photo=data["photo_id"], caption=data.get("text", ""), reply_markup=kb, parse_mode="HTML")
    elif data.get("video_id"):
        await message.answer_video(video=data["video_id"], caption=data.get("text", ""), reply_markup=kb, parse_mode="HTML")
    else:
        await message.answer(text=data.get("text", ""), reply_markup=kb, parse_mode="HTML")

    await state.set_state(PostMaker.waiting_for_channel)
    await message.answer("📢 Agar aap chahte hain ki main isko aapke channel par post karu, toh mujhe apne **Channel ka Username** bhejiye (e.g., `@mychannel`).\n\n⚠️ *Dhyan rahe: Mujhe us channel mein Admin banana zaroori hai!*\n\n*(Agar khud forward karna chahte hain toh /cancel daba dein)*", parse_mode="Markdown")

@router.message(PostMaker.waiting_for_channel)
async def send_to_channel(message: Message, state: FSMContext, bot: Bot):
    channel_username = message.text.strip()
    data = await state.get_data()
    kb = data.get("keyboard")
    
    try:
        if data.get("photo_id"):
            await bot.send_photo(chat_id=channel_username, photo=data["photo_id"], caption=data.get("text", ""), reply_markup=kb, parse_mode="HTML")
        elif data.get("video_id"):
            await bot.send_video(chat_id=channel_username, video=data["video_id"], caption=data.get("text", ""), reply_markup=kb, parse_mode="HTML")
        else:
            await bot.send_message(chat_id=channel_username, text=data.get("text", ""), reply_markup=kb, parse_mode="HTML")
            
        await message.answer(f"✅ Post successfully sent to {channel_username}!")
    except Exception as e:
        await message.answer(f"❌ Error: Main us channel mein post nahi kar paya. Kya main wahan Admin hu?\nError detail: {e}")
        
    await state.clear()

@router.message(Command("cancel"))
async def cancel_cmd(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Process cancelled. Nayi post banane ke liye /create dabayein.")

async def main():
    logging.basicConfig(level=logging.INFO)
    if not BOT_TOKEN:
        logging.error("BOT_TOKEN is missing!")
        return
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    
    logging.info("Post Maker Bot Started...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
