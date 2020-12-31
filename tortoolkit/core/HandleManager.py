# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]

from telethon import TelegramClient,events 
from telethon import __version__ as telever
from telethon.tl.types import KeyboardButtonCallback
from ..consts.ExecVarsSample import ExecVars
from ..core.getCommand import get_command
from ..core.getVars import get_val
from ..functions.Leech_Module import check_link,cancel_torrent,pause_all,resume_all,purge_all,get_status,print_files, get_transfer
from ..functions.tele_upload import upload_a_file,upload_handel
from ..functions import Human_Format
from .database_handle import TtkUpload,TtkTorrents, TorToolkitDB
from .settings import handle_settings,handle_setting_callback
from functools import partial
from ..functions.rclone_upload import get_config,rclone_driver
from ..functions.admin_check import is_admin
import asyncio as aio
import re,logging,time,os,psutil
from tortoolkit import __version__
from .ttk_ytdl import handle_ytdl_command,handle_ytdl_callbacks,handle_ytdl_file_download,handle_ytdl_playlist,handle_ytdl_playlist_down

torlog = logging.getLogger(__name__)

def add_handlers(bot: TelegramClient):
    #bot.add_event_handler(handle_leech_command,events.NewMessage(func=lambda e : command_process(e,get_command("LEECH")),chats=ExecVars.ALD_USR))
    
    bot.add_event_handler(
        handle_leech_command,
        events.NewMessage(pattern=command_process(get_command("LEECH")),
        chats=get_val("ALD_USR"))
    )
    
    bot.add_event_handler(
        handle_purge_command,
        events.NewMessage(pattern=command_process(get_command("PURGE")),
        chats=get_val("ALD_USR"))
    )
    
    bot.add_event_handler(
        handle_pauseall_command,
        events.NewMessage(pattern=command_process(get_command("PAUSEALL")),
        chats=get_val("ALD_USR"))
    )
    
    bot.add_event_handler(
        handle_resumeall_command,
        events.NewMessage(pattern=command_process(get_command("RESUMEALL")),
        chats=get_val("ALD_USR"))
    )

    bot.add_event_handler(
        handle_status_command,
        events.NewMessage(pattern=command_process(get_command("STATUS")),
        chats=get_val("ALD_USR"))
    )

    bot.add_event_handler(
        handle_settings_command,
        events.NewMessage(pattern=command_process(get_command("SETTINGS")),
        chats=get_val("ALD_USR"))
    )

    bot.add_event_handler(
        handle_exec_message_f,
        events.NewMessage(pattern=command_process(get_command("EXEC")),
        chats=get_val("ALD_USR"))
    )
    
    bot.add_event_handler(
        upload_document_f,
        events.NewMessage(pattern=command_process(get_command("UPLOAD")),
        chats=get_val("ALD_USR"))
    )

    bot.add_event_handler(
        handle_ytdl_command,
        events.NewMessage(pattern=command_process(get_command("YTDL")),
        chats=get_val("ALD_USR"))
    )

    bot.add_event_handler(
        handle_ytdl_playlist,
        events.NewMessage(pattern=command_process(get_command("PYTDL")),
        chats=get_val("ALD_USR"))
    )
    
    bot.add_event_handler(
        about_me,
        events.NewMessage(pattern=command_process(get_command("ABOUT")),
        chats=get_val("ALD_USR"))
    )

    bot.add_event_handler(
        get_logs_f,
        events.NewMessage(pattern=command_process(get_command("GETLOGS")),
        chats=get_val("ALD_USR"))
    )
    
    bot.add_event_handler(
        handle_test_command,
        events.NewMessage(pattern="/test",
        chats=get_val("ALD_USR"))
    )

    bot.add_event_handler(
        handle_server_command,
        events.NewMessage(pattern=command_process(get_command("SERVER")),
        chats=get_val("ALD_USR"))
    )



    

    #*********** Callback Handlers *********** 
    
    bot.add_event_handler(
        callback_handler_canc,
        events.CallbackQuery(pattern="torcancel")
    )

    bot.add_event_handler(
        handle_settings_cb,
        events.CallbackQuery(pattern="setting")
    )

    bot.add_event_handler(
        handle_upcancel_cb,
        events.CallbackQuery(pattern="upcancel")
    )

    bot.add_event_handler(
        handle_pincode_cb,
        events.CallbackQuery(pattern="getpin")
    )

    bot.add_event_handler(
        handle_ytdl_callbacks,
        events.CallbackQuery(pattern="ytdlsmenu")
    )

    bot.add_event_handler(
        handle_ytdl_callbacks,
        events.CallbackQuery(pattern="ytdlmmenu")
    )
    
    bot.add_event_handler(
        handle_ytdl_file_download,
        events.CallbackQuery(pattern="ytdldfile")
    )
    
    bot.add_event_handler(
        handle_ytdl_playlist_down,
        events.CallbackQuery(pattern="ytdlplaylist")
    )

#*********** Handlers Below ***********

async def handle_leech_command(e):

    if not e.is_reply:
        await e.reply("Reply to a link or magnet")
    else:
        rclone = False
        # convo init
        # todo errors when multiple leech command fired 
        if await get_config() is not None:
            tsp = time.time()
            #async with e.client.conversation(e.chat_id) as conv:
            buts = [[KeyboardButtonCallback("To Drive",data=f"leechselect drive {tsp}")],[KeyboardButtonCallback("To Telegram",data=f"leechselect tg {tsp}")]]
            conf_mes = await e.respond("<b>Choose where to upload your files:- </b>\nThe files will be uploaded to default destination after 60 sec of no action by user.",parse_mode="html",buttons=buts,reply_to=e.id)
                
            choice = await get_leech_choice(e,tsp)
            if choice == "drive":
                rclone = True
            else:
                rclone = False
            
            await conf_mes.delete()
        if rclone:
            if get_val("RCLONE_ENABLED"):
                await check_link(e,rclone)
            else:
                await e.reply("<b>DRIVE IS DISABLED BY THE ADMIN</b>",parse_mode="html")
        else:
            if get_val("LEECH_ENABLED"):
                await check_link(e,rclone)
            else:
                await e.reply("<b>TG LEECH IS DISABLED BY THE ADMIN</b>",parse_mode="html")

            #path = await check_link(e)
            #if path is not None:
            #    pass


async def get_leech_choice(e,timestamp):
    # abstract for getting the confirm in a context

    lis = [False,None]
    cbak = partial(get_leech_choice_callback,o_sender=e.sender_id,lis=lis,ts=timestamp)
    
    e.client.add_event_handler(
        #lambda e: test_callback(e,lis),
        cbak,
        events.CallbackQuery(pattern="leechselect")
    )

    start = time.time()
    defleech = get_val("DEFAULT_TIMEOUT")

    while not lis[0]:
        if (time.time() - start) >= 60: #TIMEOUT_SEC:
            
            if defleech == "leech":
                return "tg"
            elif defleech == "rclone":
                return "drive"
            else:
                # just in case something goes wrong
                return "tg"
            break
        await aio.sleep(1)

    val = lis[1]
    
    e.client.remove_event_handler(cbak)

    return val

async def get_leech_choice_callback(e,o_sender,lis,ts):
    # handle the confirm callback

    if o_sender != e.sender_id:
        return
    data = e.data.decode().split(" ")
    if data [2] != str(ts):
        return
    
    lis[0] = True
    lis[1] = data[1]

#add admin checks here - done
async def handle_purge_command(e):
    if await is_admin(e.client,e.sender_id,e.chat_id):
        await purge_all(e)
    else:
        await e.delete()

async def handle_pauseall_command(e):
    if await is_admin(e.client,e.sender_id,e.chat_id):
        await pause_all(e)
    else:
        await e.delete()

async def handle_resumeall_command(e):
    if await is_admin(e.client,e.sender_id,e.chat_id):
        await resume_all(e)
    else:
        await e.delete()

async def handle_settings_command(e):
    if await is_admin(e.client,e.sender_id,e.chat_id):
        await handle_settings(e)
    else:
        await e.delete()

async def handle_status_command(e):
    cmds = e.text.split(" ")
    if len(cmds) > 1:
        if cmds[1] == "all":
            await get_status(e,True)
        else:
            await get_status(e)
    else:
        await get_status(e)
        

async def handle_test_command(e):
    queue = e.client.queue
    db = TtkUpload()
    msg = await e.reply("test")
    #msg = await e.client.get_messages(e.chat_id,ids=msg.id)
    await rclone_driver("/mnt/d/gitmajors/ofile.mkv",msg)
    del db


async def handle_settings_cb(e):
    if await is_admin(e.client,e.sender_id,e.chat_id):
        await handle_setting_callback(e)
    else:
        await e.answer("⚠️ WARN ⚠️ Dont Touch Admin Settings.",alert=True)

async def handle_upcancel_cb(e):
    db = TtkUpload()

    data = e.data.decode("UTF-8")
    torlog.info("Data is {}".format(data))
    data = data.split(" ")

    if str(e.sender_id) == data[3]:
        db.cancel_download(data[1],data[2])
        await e.answer("CANCLED UPLOAD")
    else:
        await e.answer("Cant Cancel others upload 😡",alert=True)


async def callback_handler_canc(e):
    # TODO the msg can be deleted
    #mes = await e.get_message()
    #mes = await mes.get_reply_message()
    

    torlog.debug(f"Here the sender _id is {e.sender_id}")
    torlog.debug("here is the allower users list {} {}".format(get_val("ALD_USR"),type(get_val("ALD_USR"))))

    data = e.data.decode("utf-8").split(" ")
    torlog.debug("data is {}".format(data))
    is_aria = False
    if data[1] == "aria2":
        is_aria = True
        data.remove("aria2")

    if data[2] == str(e.sender_id):
        hashid = data[1]
        hashid = hashid.strip("'")
        torlog.info(f"Hashid :- {hashid}")

        await cancel_torrent(hashid, is_aria)
        await e.answer("The torrent has been cancled ;)",alert=True)
    elif e.sender_id in get_val("ALD_USR"):
        hashid = data[1]
        hashid = hashid.strip("'")
        
        torlog.info(f"Hashid :- {hashid}")
        
        await cancel_torrent(hashid, is_aria)
        await e.answer("The torrent has been cancled in ADMIN MODE XD ;)",alert=True)
    else:
        await e.answer("You can cancel only your torrents ;)", alert=True)


async def handle_exec_message_f(e):
    message = e
    client = e.client
    if await is_admin(client, message.sender_id, message.chat_id):
        PROCESS_RUN_TIME = 100
        cmd = message.text.split(" ", maxsplit=1)[1]

        reply_to_id = message.id
        if message.is_reply:
            reply_to_id = message.reply_to_msg_id

        start_time = time.time() + PROCESS_RUN_TIME
        process = await aio.create_subprocess_shell(
            cmd,
            stdout=aio.subprocess.PIPE,
            stderr=aio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        e = stderr.decode()
        if not e:
            e = "No Error"
        o = stdout.decode()
        if not o:
            o = "No Output"
        else:
            _o = o.split("\n")
            o = "`\n".join(_o)
        OUTPUT = f"**QUERY:**\n__Command:__\n`{cmd}` \n__PID:__\n`{process.pid}`\n\n**stderr:** \n`{e}`\n**Output:**\n{o}"

        if len(OUTPUT) > 3900:
            with open("exec.text", "w+", encoding="utf8") as out_file:
                out_file.write(str(OUTPUT))
            await client.send_file(
                entity=message.chat_id,
                file="exec.text",
                caption=cmd,
                reply_to=reply_to_id
            )
            os.remove("exec.text")
            await message.delete()
        else:
            await message.reply(OUTPUT)

async def handle_pincode_cb(e):
    data = e.data.decode("UTF-8")
    data = data.split(" ")
    
    if str(e.sender_id) == data[2]:
        db = TtkTorrents()
        passw = db.get_password(data[1])
        if isinstance(passw,bool):
            await e.answer("torrent expired download has been started now.")
        else:
            await e.answer(f"Your Pincode if \"{passw}\"",alert=True)

        del db
    else:
        await e.answer("Its not you torrent.",alert=True)

async def upload_document_f(message):
    imsegd = await message.reply(
        "processing ..."
    )
    imsegd = await message.client.get_messages(message.chat_id,ids=imsegd.id)
    if await is_admin(message.client, message.sender_id, message.chat_id):
        if " " in message.text:
            recvd_command, local_file_name = message.text.split(" ", 1)
            recvd_response = await upload_a_file(
                local_file_name,
                imsegd,
                False,
                TtkUpload()
            )
            #torlog.info(recvd_response)
    await imsegd.delete()

async def get_logs_f(message):
    message.text += " torlog.txt"
    await upload_document_f(message)

async def handle_server_command(message):
    try:
        # Memory
        mem = psutil.virtual_memory()
        memavailable = mem.available
        memtotal = mem.total
        mempercent = mem.percent
        memfree = mem.free
    except:
        memavailable = "N/A"
        memtotal = "N/A"
        mempercent = "N/A"
        memfree = "N/A"

    try:
        # Frequencies
        cpufreq = psutil.cpu_freq()
        freqcurrent = cpufreq.current
        freqmax = cpufreq.max
    except:
        freqcurrent = "N/A"
        freqmax = "N/A"

    try:
        # Cores
        cores = psutil.cpu_count(logical=False)
        lcores = psutil.cpu_count()
    except:
        cores = "N/A"
        lcores = "N/A"

    try:
        cpupercent = psutil.cpu_percent()
    except:
        cpupercent = "N/A"
    
    try:
        transfer = await get_transfer()
        dlb = Human_Format.human_readable_bytes(transfer["dl_info_data"])
        upb = Human_Format.human_readable_bytes(transfer["up_info_data"])
    except:
        dlb = "N/A"
        upb = "N/A"

    msg = (
        "<b>CPU STATS:-</b>\n"
        f"Cores: {cores} Logical: {lcores}\n"
        f"CPU Frequency: {freqcurrent}  Mhz Max: {freqmax}\n"
        f"CPU Utilization: {cpupercent}%\n"
        "\n"
        "<b>MEMORY STATS:-</b>\n"
        f"Available: {memavailable}\n"
        f"Total: {memtotal}\n"
        f"Usage: {mempercent}%\n"
        f"Free: {memfree}\n"
        "\n"
        "<b>TRANSFER INFO:</b>\n"
        f"Download: {dlb}\n"
        f"Upload: {upb}\n"
    )
    await message.reply(msg, parse_mode="html")

async def about_me(message):
    db = TorToolkitDB()
    _, val1 = db.get_variable("RCLONE_CONFIG")
    if val1 is None:
        rclone_cfg = "No Rclone Config is loaded."
    else:
        rclone_cfg = "Rclone Config is loaded"

    val1  = get_val("RCLONE_ENABLED")
    if val1 is not None:
        if val1:
            rclone = "Rclone enabled by admin."
        else:
            rclone = "Rclone disabled by admin."
    else:
        rclone = "N/A"

    val1  = get_val("LEECH_ENABLED")
    if val1 is not None:
        if val1:
            leen = "Leech command enabled by admin."
        else:
            leen = "Leech command disabled by admin."
    else:
        leen = "N/A"

    val1  = get_val("RUNTIME_RCLONE")
    if val1 is not None:
        if val1:
            rclone_m = "Rclone mod is applied."
        else:
            rclone_m = "Rclone mod is not applied."
    else:
        rclone_m = "N/A"

    msg = (
        "<b>Name</b>: <code>TorToolkit</code>\n"
        f"<b>Version</b>: <code>{__version__}</code>\n"
        f"<b>Telethon Version</b>: {telever}\n"
        "<b>Created By</b>: @yaknight\n\n"
        "<u>Currents Configs:-</u>\n"
        "<b>Torrent Download Engine:-</b> <code>qBittorrent [4.3.0 fix active]</code> \n"
        "<b>Direct Link Download Engine:-</b> <code>aria2</code> \n"
        "<b>Upload Engine:-</b> <code>RCLONE</code> \n"
        "<b>Youtube Download Engine:-</b> <code>youtube-dl</code>\n"
        f"<b>Rclone config:- </b> <code>{rclone_cfg}</code>\n"
        f"<b>Leech:- </b> <code>{leen}</code>\n"
        f"<b>Rclone:- </b> <code>{rclone}</code>\n"
        f"<b>Rclone Mod :- </b> <code>{rclone_m}</code> \n"
        f"<b>User Caps(Limits) :- </b> <code>In-progress</code> \n"
    )

    await message.reply(msg,parse_mode="html")


def command_process(command):
    return re.compile(command,re.IGNORECASE)