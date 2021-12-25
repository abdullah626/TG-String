import asyncio

from bot import bot, HU_APP
from pyromod import listen
from asyncio.exceptions import TimeoutError

from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import (
    SessionPasswordNeeded, FloodWait,
    PhoneNumberInvalid, ApiIdInvalid,
    PhoneCodeInvalid, PhoneCodeExpired
)

API_TEXT = """Hi, {}.
BU PROGRAM SESSİON ASİSTAN İLE BOTU BİRBİRİ ARASINAKİ BAĞLANIYI SAĞLAMAK İÇİN KRULDUM

By @MUBTEZELL

ŞİMDİ OTURUM OLUŞTURMAYA BAŞLAMAK İÇİN 'API_İD' GİRİNİZ."""
HASH_TEXT = "ŞİMDİ `API_HASH` GÖNDERİN.\n\nBASIN /cancel GÖREVİ  İPTAL ETMEK İÇİN."
PHONE_NUMBER_TEXT = (
    "ŞİMDİ TELEGRAM HESABINIZIN YANİKULLANICAĞINIZ ASİSTAN HESAP NMARANAZI BAŞINA + OLUCAK ŞEKİLDE GİRİNİZ. \n"
    "ÜLKE KODU DAHİL ÖRNEK: **+14154566376**\n\n"
    "BASIN /cancel İPTAL ETMEK İÇİN."
)

@bot.on_message(filters.private & filters.command("start"))
async def genStr(_, msg: Message):
    chat = msg.chat
    api = await bot.ask(
        chat.id, API_TEXT.format(msg.from_user.mention)
    )
    if await is_cancel(msg, api.text):
        return
    try:
        check_api = int(api.text)
    except Exception:
        await msg.reply("`API_ID` GEÇERSİZ.\nBASIN /start YENİDEN BAŞLAMAK İÇİN.")
        return
    api_id = api.text
    hash = await bot.ask(chat.id, HASH_TEXT)
    if await is_cancel(msg, hash.text):
        return
    if not len(hash.text) >= 30:
        await msg.reply("`API_HASH` GEÇERSİZ.\nBASIN /start YENİDEN BAŞLAMAK İÇİN.")
        return
    api_hash = hash.text
    while True:
        number = await bot.ask(chat.id, PHONE_NUMBER_TEXT)
        if not number.text:
            continue
        if await is_cancel(msg, number.text):
            return
        phone = number.text
        confirm = await bot.ask(chat.id, f'`Is "{phone}" DOĞRUMU? (y/n):` \n\nGÖNDER: `y` (EVET İSE)\nGÖNDER: `n` (HAYIR İSE)')
        if await is_cancel(msg, confirm.text):
            return
        if "y" in confirm.text:
            break
    try:
        client = Client("my_account", api_id=api_id, api_hash=api_hash)
    except Exception as e:
        await bot.send_message(chat.id ,f"**ERROR:** `{str(e)}`\nBASIN /start YENİDEN BAŞLAMAK İÇİN.")
        return
    try:
        await client.connect()
    except ConnectionError:
        await client.disconnect()
        await client.connect()
    try:
        code = await client.send_code(phone)
        await asyncio.sleep(1)
    except FloodWait as e:
        await msg.reply(f"You have Floodwait of {e.x} Seconds")
        return
    except ApiIdInvalid:
        await msg.reply("API ID and API Hash GEÇERSİZ.\n\nBASIN  /start YENİDEN BAŞLAMAK İÇİN.")
        return
    except PhoneNumberInvalid:
        await msg.reply("TELEFON NUMARASI GEÇERSİZ .\n\nBASIN  /start YEENNİDEN BAŞLAMAK İÇİN .")
        return
    try:
        otp = await bot.ask(
            chat.id, ("TELEFON NUMARANIZA BİR KOD GÖNDERİLDİ, "
                      "LÜTFEN KODU  `1 2 3 4 5` FORMATINDA GİRİNİZ . __(HER SAYI ARASINA BİR BOŞLUK!)__ \n\n"
                      "BOT KODU GÖNDERMİYORSA /restart KOMUTU İLE YENİDEN BAŞLATMAYI DENEYİN  VE /start KOMUTU İLE TEKRAR BAŞLATIN.\n"
                      "BASIN /cancel İPAL ETMEK İÇİN."), timeout=300)

    except TimeoutError:
        await msg.reply("5 DAKİKALIK SÜRE SINNIRINA ULAŞILDI.\nBASIN  /start YENİDEN BAŞLATMAK İÇİN .")
        return
    if await is_cancel(msg, otp.text):
        return
    otp_code = otp.text
    try:
        await client.sign_in(phone, code.phone_code_hash, phone_code=' '.join(str(otp_code)))
    except PhoneCodeInvalid:
        await msg.reply("GÇERSİZ KOD .\n\nBASIN  /start YENİDEN BAŞLATMAK İÇİN.")
        return
    except PhoneCodeExpired:
        await msg.reply("KODUN SÜRESİ DOLDU.\n\nBASIN  /start YENİDEN BAŞLATMAK İÇİN .")
        return
    except SessionPasswordNeeded:
        try:
            two_step_code = await bot.ask(
                chat.id, 
                "HESABINIZDA İKİ ADIMLI DOĞRLAMA VARR.\nLÜTFEN PAROLANIZI GİRİNİZ .\n\nBASIN  /cancel İPTAL ETMEK İÇİN.",
                timeout=300
            )
        except TimeoutError:
            await msg.reply("`5 DAKİKALIK SÜRE SIINIRINA ULAŞILDI.\n\nBASIN  /start YENİDEN BAŞLATMAK İÇİN .`")
            return
        if await is_cancel(msg, two_step_code.text):
            return
        new_code = two_step_code.text
        try:
            await client.check_password(new_code)
        except Exception as e:
            await msg.reply(f"**ERROR:** `{str(e)}`")
            return
    except Exception as e:
        await bot.send_message(chat.id ,f"**ERROR:** `{str(e)}`")
        return
    try:
        session_string = await client.export_session_string()
        await client.send_message("me", f"#PYROGRAM #STRING_SESSION\n\n```{session_string}``` \n\nBy [@Session1Bot](tg://openmessage?user_id=5008082645) \nA Bot By @Mubtezell")
        await client.disconnect()
        text = "DİZE OTURRUMU BAŞARILI BİR ŞEKİLDE OLUŞTURULDU.\nAŞŞAĞIAKİ BUTONA TIKKLAYINIZ."
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton(text="DİZE OTURUMUNU GÖSTER", url=f"tg://openmessage?user_id={chat.id}")]]
        )
        await bot.send_message(chat.id, text, reply_markup=reply_markup)
    except Exception as e:
        await bot.send_message(chat.id ,f"**ERROR:** `{str(e)}`")
        return


@bot.on_message(filters.private & filters.command("restart"))
async def restart(_, msg: Message):
    await msg.reply("YENNİDEN BAŞLATILAN Bot!")
    HU_APP.restart()


@bot.on_message(filters.private & filters.command("help"))
async def restart(_, msg: Message):
    out = f"""
MERHABA, {msg.from_user.mention}. BU SESSİON STRİNG BOTU DUR . \
USER BOTUNUZ İÇİN  `STRING_SESSION` VERECEĞİM.

 `API_ID`, `API_HASH`, LEFON NUUMARASI VE TEK SFERLİK DOĞRULAMA KODUNA İHTİYAÇ VARDIR. \
WHANGİ ELEFON NUMARANIZA GÖNDERİLECEKTİR.

**NOTE:** BOT TELEFON NUMARAANIZA KOD GÖNDERMİYORSA BOTU YENİDEN BAŞLATINNIZ. 

BOT GÜNCELLEMELERİ ÖĞRENMEK İÇİN KANALA KATILINIZ !!
"""
    reply_markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton('Support Group', url='https://t.me/VirtualMafia'),
                InlineKeyboardButton('Developer', url='https://t.me/Mubtezll')
            ],
            [
                InlineKeyboardButton('Bots Updates Channel', url='https://t.me/UtagOnline'),
            ]
        ]
    )
    await msg.reply(out, reply_markup=reply_markup)


async def is_cancel(msg: Message, text: str):
    if text.startswith("/cancel"):
        await msg.reply("İŞLEM İPTAL EDİDİ.")
        return True
    return False

if __name__ == "__main__":
    bot.run()
