import json
import os
from typing import Any, Dict

"""
簡單的多語系工具：
- 使用 key 來代表文字內容，例如 "ui.login.button"
- 透過 set_language(lang) 切換目前語言
- 透過 t(key, **params) 取得文字，params 會用 Python format 插值

目前先內建一份英文翻譯，之後可以在此檔或外部 JSON 檔擴充其他語言。
"""

_current_lang: str = "en"


def _load_external_translations(lang: str) -> Dict[str, str]:
    """
    預留：如果將來想把翻譯放到 JSON 檔，例如:
      locales/en.json, locales/zh-TW.json
    可以在這裡載入。
    目前先回傳空 dict，改用內建 TRANSLATIONS。
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    locales_dir = os.path.join(base_dir, "locales")
    file_path = os.path.join(locales_dir, f"{lang}.json")
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items()}
    except Exception:
        pass
    return {}


# 內建翻譯：目前先以原本英文文字為主，未來可以把其他語言放進來
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        # ====== Right widget / main controls ======
        "ui.chatbot.button": "Chat Bot",
        "ui.chatbot.desc": "A chat bot that answer your questions.",

        "ui.login.button": "Login",
        "ui.login.desc": "Login your Chess.com account for more functions",
        "ui.logout.button": "Logout",
        "ui.logout.desc": "Logout from your Chess.com account",

        "ui.login.username_placeholder": "Username or Email",
        "ui.login.username_desc": "The place to type in Username or Email",
        "ui.login.password_placeholder": "Password",
        "ui.login.password_desc": "The place to type in Password",
        "ui.login.submit_button": "Login",
        "ui.login.submit_desc": "Press to login",

        "ui.setting.button": "Setting",
        "ui.setting.desc": "Menu to change your preferences",

        "ui.play.computer.button": "Play with computer",
        "ui.play.computer.name": "Play with computer",
        "ui.play.computer.desc": "press space or enter to play with computer engine",

        "ui.play.other.button": "Play with other online player",
        "ui.play.other.name": "Play with other online player",
        "ui.play.other.desc": "press space or enter to play with other online player",

        "ui.puzzle.mode.button": "Puzzle Mode",
        "ui.puzzle.mode.desc": "press space or enter to play chess puzzle",
        "ui.puzzle.next.button": "Next Puzzle",
        "ui.puzzle.retry.button": "Retry Puzzle",

        "ui.game.new.button": "New Game",
        "ui.game.review.button": "Game Review",
        "ui.game.return_home.button": "Return to Home Page",
        "ui.game.return_home.desc": "Press to exit current mode",

        "ui.analysis.current_move": "Current Move: \n",
        "ui.analysis.comment": "Game Review Comment: \n",
        "ui.analysis.explanation": "Explanation: \n",
        "ui.analysis.next_move": "Next Move",
        "ui.analysis.previous_move": "Previous Move",
        "ui.analysis.first_move": "First Move",
        "ui.analysis.best_move": "Best Move",

        "ui.move_list": "Move List:\n",
        "ui.white_pieces": "White pieces: ",
        "ui.black_pieces": "Black pieces: ",
        "ui.assigned_color": "Assigned Color: ",
        "ui.opponent_last_move": "Opponent last move: \n",

        "ui.check_time.button": "Check remaining time",
        "ui.resign.button": "Resign",
        "ui.undo.button": "Undo last move",

        "ui.check_position.placeholder": "Check position",
        "ui.check_position.name": "Check position input field",
        "ui.check_position.desc": "you can query a piece or square here",

        "ui.command_panel.placeholder": "Move Input",
        "ui.command_panel.name": "Command Panel",
        "ui.command_panel.desc": "You can type your move here",

        "ui.select_panel.placeholder": "Enter Selection",

        # ====== Chatbot window ======
        "chat.voice_button.tooltip": "voice input (Ctrl+S)",
        "chat.voice_button.desc": "Press to activate voice input. Press again to finish voice input.",
        "chat.message_input.desc": "You can type your message here.",
        "chat.send_button.text": "Enter",
        "chat.send_button.desc": "Press to send message",
        "chat.welcome": "Chatbot: Hello! How can I help you today?",
        "chat.you_prefix": "You: {message}",
        "chat.bot_prefix": "Chatbot: ",
        "chat.bot_line": "Chatbot: {message}",

        # ====== System / info dialogs ======
        "dialog.information.title": "Information",
        "dialog.information.text": "This is an information message.",

        # ====== Main flow status / speak texts (部份示例，之後可擴充) ======
        "speak.login.success": "login success! Username: {username}",
        "speak.login.failed": "The username or password is incorrect. Please try again",
        "speak.login.invalid_input": "Invalid Input",
        "speak.login.trying": "trying to login",
        "speak.flow.activate_login": "Activate Login Phase",
        "speak.flow.select_bot_category": "Select bot category",
        "speak.flow.select_time_controls": "Select Time Controls",

        "speak.game.still_initializing": "Still {sentence}",
        "speak.game.resign_before_new": "Please resign before start a new game",
        "speak.game.computer_mode_selected": "computer engine mode <>{sentence}",
        "speak.game.undo.no_move": "There is no move to undo.",
        "speak.game.undo.done": "Last move has been undone.",

        # ====== Chess validation messages ======
        "chess.promotion": "Promotion",
        "chess.illegal_move": "Illegal move",
        "chess.invalid_move": "Invalid move",
        "chess.invalid_square": "Invalid square name",
        "chess.no_piece_on_source": "There is no piece on the source square.",
        "chess.opponent_piece_on_source": "You selected your opponent's piece. Please move your own piece.",
        "chess.win.black_checkmate": "Black wins by checkmate!",
        "chess.win.white_checkmate": "White wins by checkmate!",
        "chess.win.stalemate": "Stalemate!",
        "chess.win.insufficient_material": "Insufficient material!",
        "chess.win.none": "No win detected.",
    }
    ,
    "zh-TW": {
        # ====== Right widget / main controls ======
        "ui.chatbot.button": "聊天機器人",
        "ui.chatbot.desc": "一個可以回答你問題的聊天機器人。",

        "ui.login.button": "登入",
        "ui.login.desc": "登入你的 Chess.com 帳號以使用更多功能",
        "ui.logout.button": "登出",
        "ui.logout.desc": "從你的 Chess.com 帳號登出",

        "ui.login.username_placeholder": "使用者名稱或 Email",
        "ui.login.username_desc": "在此輸入使用者名稱或 Email",
        "ui.login.password_placeholder": "密碼",
        "ui.login.password_desc": "在此輸入密碼",
        "ui.login.submit_button": "登入",
        "ui.login.submit_desc": "按下以登入",

        "ui.setting.button": "設定",
        "ui.setting.desc": "開啟偏好設定選單",

        "ui.play.computer.button": "與電腦對戰",
        "ui.play.computer.name": "與電腦對戰",
        "ui.play.computer.desc": "按空白鍵或 Enter 與電腦引擎對戰",

        "ui.play.other.button": "與線上玩家對戰",
        "ui.play.other.name": "與線上玩家對戰",
        "ui.play.other.desc": "按空白鍵或 Enter 與其他線上玩家對戰",

        "ui.puzzle.mode.button": "解題模式",
        "ui.puzzle.mode.desc": "按空白鍵或 Enter 開始解題",
        "ui.puzzle.next.button": "下一題",
        "ui.puzzle.retry.button": "重試",

        "ui.game.new.button": "新對局",
        "ui.game.review.button": "棋局複盤",
        "ui.game.return_home.button": "回到首頁",
        "ui.game.return_home.desc": "按下以離開目前模式",

        "ui.analysis.current_move": "目前步：\n",
        "ui.analysis.comment": "複盤評語：\n",
        "ui.analysis.explanation": "解釋：\n",
        "ui.analysis.next_move": "下一步",
        "ui.analysis.previous_move": "上一步",
        "ui.analysis.first_move": "第一步",
        "ui.analysis.best_move": "最佳步",

        "ui.move_list": "走法列表：\n",
        "ui.white_pieces": "白棋子：",
        "ui.black_pieces": "黑棋子：",
        "ui.assigned_color": "指定顏色：",
        "ui.opponent_last_move": "對手上一步：\n",

        "ui.check_time.button": "查看剩餘時間",
        "ui.resign.button": "認輸",
        "ui.undo.button": "悔棋",

        "ui.check_position.placeholder": "查詢位置",
        "ui.check_position.name": "位置查詢輸入框",
        "ui.check_position.desc": "你可以在此查詢棋子或格子",

        "ui.command_panel.placeholder": "輸入走法",
        "ui.command_panel.name": "指令輸入框",
        "ui.command_panel.desc": "你可以在此輸入你的走法",

        "ui.select_panel.placeholder": "輸入選擇",

        # ====== Chatbot window ======
        "chat.voice_button.tooltip": "語音輸入（Ctrl+S）",
        "chat.voice_button.desc": "按下開始語音輸入，再按一次結束語音輸入。",
        "chat.message_input.desc": "你可以在此輸入訊息。",
        "chat.send_button.text": "送出",
        "chat.send_button.desc": "按下送出訊息",
        "chat.welcome": "聊天機器人：哈囉！我可以怎麼幫你？",
        "chat.you_prefix": "你：{message}",
        "chat.bot_prefix": "聊天機器人：",
        "chat.bot_line": "聊天機器人：{message}",

        # ====== System / info dialogs ======
        "dialog.information.title": "資訊",
        "dialog.information.text": "這是一則資訊訊息。",

        # ====== Speak texts ======
        "speak.login.success": "登入成功！使用者名稱：{username}",
        "speak.login.failed": "使用者名稱或密碼不正確，請再試一次",
        "speak.login.invalid_input": "輸入無效",
        "speak.login.trying": "正在嘗試登入",
        "speak.flow.activate_login": "已進入登入流程",
        "speak.flow.select_bot_category": "請選擇電腦類別",
        "speak.flow.select_time_controls": "請選擇時間控制",

        "speak.game.still_initializing": "仍在初始化：{sentence}",
        "speak.game.resign_before_new": "開始新對局前請先認輸",
        "speak.game.computer_mode_selected": "電腦引擎模式 <>{sentence}",
        "speak.game.undo.no_move": "目前沒有可以悔棋的步數。",
        "speak.game.undo.done": "已在內部棋盤悔掉上一手，如有需要請同時在 chess.com 申請悔棋。",

        # ====== Chess validation messages ======
        "chess.promotion": "升變",
        "chess.illegal_move": "非法走法",
        "chess.invalid_move": "無效走法",
        "chess.invalid_square": "無效的格子名稱",
        "chess.no_piece_on_source": "起始格沒有任何棋子，無法走這步。",
        "chess.opponent_piece_on_source": "那是對手的棋子，請選擇你自己的棋子來走。",
        "chess.win.black_checkmate": "黑方將死獲勝！",
        "chess.win.white_checkmate": "白方將死獲勝！",
        "chess.win.stalemate": "逼和！",
        "chess.win.insufficient_material": "子力不足！",
        "chess.win.none": "尚未判定勝負。",

        # ====== Settings dialog ======
        "settings.title": "設定",
        "settings.language.label": "語言：",
        "settings.language.en": "English",
        "settings.language.zh_tw": "繁體中文",
        "settings.language.zh_cn": "简体中文",
        "settings.engine.checkbox": "啟用內建語音引擎",
        "settings.engine.checkbox.desc": "勾選使用內建語音引擎；取消勾選則僅朗讀重要資訊。",
        "settings.rate.label": "語速：",
        "settings.volume.label": "音量：",
    },
    "zh-CN": {
        # ====== Right widget / main controls ======
        "ui.chatbot.button": "聊天机器人",
        "ui.chatbot.desc": "一个可以回答你问题的聊天机器人。",

        "ui.login.button": "登录",
        "ui.login.desc": "登录你的 Chess.com 账号以使用更多功能",
        "ui.logout.button": "登出",
        "ui.logout.desc": "从你的 Chess.com 账号登出",

        "ui.login.username_placeholder": "用户名或 Email",
        "ui.login.username_desc": "在此输入用户名或 Email",
        "ui.login.password_placeholder": "密码",
        "ui.login.password_desc": "在此输入密码",
        "ui.login.submit_button": "登录",
        "ui.login.submit_desc": "按下以登录",

        "ui.setting.button": "设置",
        "ui.setting.desc": "打开偏好设置菜单",

        "ui.play.computer.button": "与电脑对战",
        "ui.play.computer.name": "与电脑对战",
        "ui.play.computer.desc": "按空格键或 Enter 与电脑引擎对战",

        "ui.play.other.button": "与在线玩家对战",
        "ui.play.other.name": "与在线玩家对战",
        "ui.play.other.desc": "按空格键或 Enter 与其他在线玩家对战",

        "ui.puzzle.mode.button": "解题模式",
        "ui.puzzle.mode.desc": "按空格键或 Enter 开始解题",
        "ui.puzzle.next.button": "下一题",
        "ui.puzzle.retry.button": "重试",

        "ui.game.new.button": "新对局",
        "ui.game.review.button": "棋局复盘",
        "ui.game.return_home.button": "返回首页",
        "ui.game.return_home.desc": "按下以退出当前模式",

        "ui.analysis.current_move": "当前步：\n",
        "ui.analysis.comment": "复盘评语：\n",
        "ui.analysis.explanation": "解释：\n",
        "ui.analysis.next_move": "下一步",
        "ui.analysis.previous_move": "上一步",
        "ui.analysis.first_move": "第一步",
        "ui.analysis.best_move": "最佳步",

        "ui.move_list": "走法列表：\n",
        "ui.white_pieces": "白棋子：",
        "ui.black_pieces": "黑棋子：",
        "ui.assigned_color": "分配颜色：",
        "ui.opponent_last_move": "对手上一步：\n",

        "ui.check_time.button": "查看剩余时间",
        "ui.resign.button": "认输",
        "ui.undo.button": "悔棋",

        "ui.check_position.placeholder": "查询位置",
        "ui.check_position.name": "位置查询输入框",
        "ui.check_position.desc": "你可以在此查询棋子或格子",

        "ui.command_panel.placeholder": "输入走法",
        "ui.command_panel.name": "指令输入框",
        "ui.command_panel.desc": "你可以在此输入你的走法",

        "ui.select_panel.placeholder": "输入选择",

        # ====== Chatbot window ======
        "chat.voice_button.tooltip": "语音输入（Ctrl+S）",
        "chat.voice_button.desc": "按下开始语音输入，再按一次结束语音输入。",
        "chat.message_input.desc": "你可以在此输入消息。",
        "chat.send_button.text": "发送",
        "chat.send_button.desc": "按下发送消息",
        "chat.welcome": "聊天机器人：你好！我可以怎么帮你？",
        "chat.you_prefix": "你：{message}",
        "chat.bot_prefix": "聊天机器人：",
        "chat.bot_line": "聊天机器人：{message}",

        # ====== System / info dialogs ======
        "dialog.information.title": "信息",
        "dialog.information.text": "这是一则信息消息。",

        # ====== Speak texts ======
        "speak.login.success": "登录成功！用户名：{username}",
        "speak.login.failed": "用户名或密码不正确，请再试一次",
        "speak.login.invalid_input": "输入无效",
        "speak.login.trying": "正在尝试登录",
        "speak.flow.activate_login": "已进入登录流程",
        "speak.flow.select_bot_category": "请选择电脑类别",
        "speak.flow.select_time_controls": "请选择时间控制",

        "speak.game.still_initializing": "仍在初始化：{sentence}",
        "speak.game.resign_before_new": "开始新对局前请先认输",
        "speak.game.computer_mode_selected": "电脑引擎模式 <>{sentence}",
        "speak.game.undo.no_move": "目前没有可以悔棋的步数。",
        "speak.game.undo.done": "已在内部棋盘悔掉上一手，如有需要请同时在 chess.com 申请悔棋。",

        # ====== Chess validation messages ======
        "chess.promotion": "升变",
        "chess.illegal_move": "非法走法",
        "chess.invalid_move": "无效走法",
        "chess.invalid_square": "无效的格子名称",
        "chess.no_piece_on_source": "起始格上没有任何棋子，无法执行这步棋。",
        "chess.opponent_piece_on_source": "这是对手的棋子，请选择你自己的棋子来走。",
        "chess.win.black_checkmate": "黑方将死获胜！",
        "chess.win.white_checkmate": "白方将死获胜！",
        "chess.win.stalemate": "逼和！",
        "chess.win.insufficient_material": "子力不足！",
        "chess.win.none": "尚未判定胜负。",

        # ====== Settings dialog ======
        "settings.title": "设置",
        "settings.language.label": "语言：",
        "settings.language.en": "English",
        "settings.language.zh_tw": "繁體中文",
        "settings.language.zh_cn": "简体中文",
        "settings.engine.checkbox": "启用内建语音引擎",
        "settings.engine.checkbox.desc": "勾选使用内建语音引擎；取消勾选则仅播报重要信息。",
        "settings.rate.label": "语速：",
        "settings.volume.label": "音量：",
    }
}

_external_cache: Dict[str, Dict[str, str]] = {}


def set_language(lang: str) -> None:
    """
    設定目前語言代碼，例如 "en", "zh-TW", "zh-CN"。
    若該語言沒有翻譯，會自動 fallback 到英文。
    """
    global _current_lang
    _current_lang = lang


def get_language() -> str:
    return _current_lang


def _get_lang_table(lang: str) -> Dict[str, str]:
    """
    取得指定語言的翻譯表，會先看內建 TRANSLATIONS，再看外部 JSON。
    """
    if lang not in _external_cache:
        _external_cache[lang] = _load_external_translations(lang)

    table = dict(TRANSLATIONS.get(lang, {}))
    table.update(_external_cache.get(lang, {}))
    return table


def t(key: str, **params: Any) -> str:
    """
    取得多語系文字：
      - 先用目前語言查 key
      - 找不到時 fallback 到英文
      - 都沒有時回傳 key 本身，方便開發期發現漏翻譯
    """
    lang_table = _get_lang_table(_current_lang)
    if key in lang_table:
        text = lang_table[key]
    else:
        # fallback to English
        en_table = _get_lang_table("en")
        text = en_table.get(key, key)
    if params:
        try:
            text = text.format(**params)
        except Exception:
            # 插值失敗時，至少不要讓程式崩潰
            pass
    return text


