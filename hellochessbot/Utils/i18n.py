import json
import os
from typing import Any, Dict


_current_lang: str = "en"


def _normalize_lang_code(lang: str) -> str:
    value = str(lang or "en").strip().lower()

    if value in {"en", "en-us", "en_us", "english", "英文"}:
        return "en"

    if value in {"zh-tw", "zh_tw", "zh-hk", "zh_hk", "tw", "hk", "繁體", "繁體中文", "traditional chinese"}:
        return "zh-TW"

    if value in {"zh-cn", "zh_cn", "zh", "cn", "简体", "簡體", "简体中文", "simplified chinese"}:
        return "zh-CN"

    return "en"


def _load_external_translations(lang: str) -> Dict[str, str]:

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



TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        # ====== Right widget / main controls ======
        "ui.chatbot.button": "Chat Bot",
        "ui.chatbot.desc": "A AI chat bot that answer your questions.",

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
        "ui.play.computer.category_hint": "Press Tab to select options, press Enter or Space Bar to confirm option.",

        "ui.play.other.button": "Play with other online player",
        "ui.play.other.name": "Play with other online player",
        "ui.play.other.desc": "press space bar or enter key to play with other online player",

        "ui.puzzle.mode.button": "Puzzle Mode",
        "ui.puzzle.mode.desc": "press space bar or enter key to play chess puzzle",
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
        "ui.current_game_analysis.button": "Current Game Analysis",
        "ui.current_game_analysis.desc": "Analyze current game situation",
        "ui.macro_view.button": "Macro View",
        "ui.common.play": "Play",
        "ui.common.back_to_category": "Back to Category",
        "ui.common.back_to_previous_page": "Back to Previous Page",
        "ui.common.ok": "OK",

        # ====== Chatbot window ======
        "chat.voice_button.tooltip": "Voice input (Ctrl+S)",
        "chat.voice_button.desc": "Press to activate voice input. Press again to finish voice input.",
        "settings.voice_button.desc.toggle": "Press to start voice input, press again to finish.",
        "settings.voice_button.desc.hold": "Press and hold to record, release to finish.",
        "settings.voice_button.tooltip.toggle": "Voice input (Ctrl+S: press to start/press again to finish)",
        "settings.voice_button.tooltip.hold": "Voice input (Ctrl+S: hold to record/release to finish)",
        "chat.message_input.desc": "You can type your message here.",
        "chat.send_button.text": "Enter",
        "chat.send_button.desc": "Press to send message",
        "chat.welcome": "Hello! How can I help you today?",
        "chat.user_label": "You",
        "chat.bot_label": "Chatbot",
        "chat.macro.none_under_attack": "Macro view: No pieces are under attack.",
        "chat.macro.under_attack_count": "Macro view: {count} pieces are under attack.",
        "chat.you_prefix": "You: {message}",
        "chat.bot_prefix": "Chatbot: ",
        "chat.bot_line": "Chatbot: {message}",

        # ====== System / info dialogs ======
        "dialog.information.title": "Information",
        "dialog.information.text": "This is an information message.",
        "dialog.confirm.title": "Confirm Dialog",
        "dialog.confirm.prefix": "Confirm {message}",
        "dialog.confirm.resign_message": "to resign from current game by pressing enter or cancel by pressing delete",
        "startup.audio_reminder.title": "Audio Reminder",
        "startup.audio_reminder.message": "This software is designed for visually impaired users. Please ensure your system audio is enabled for voice guidance and assistance.",
        "startup.audio_reminder.confirm": "{message} Press Enter to confirm.",

        # ====== Settings dialog ======
        "settings.title": "Settings",
        "settings.language.label": "Language:",
        "settings.language.desc": "Use up and down arrow keys to change the language.",
        "settings.language.en": "English",
        "settings.language.zh_tw": "Traditional Chinese",
        "settings.language.zh_cn": "Simplified Chinese",
        "settings.engine.checkbox": "Use built-in speech engine",
        "settings.engine.checkbox.desc": "Enable the built-in speech engine for spoken text.",
        "settings.font_size.label": "Font size:",
        "settings.font_size.desc": "Use left and right arrow keys to adjust the font size.",
        "settings.rate.label": "Speech rate:",
        "settings.rate.desc": "Use left and right arrow keys to adjust the speech rate.",
        "settings.volume.label": "Speech volume:",
        "settings.volume.desc": "Use left and right arrow keys to adjust the speech volume.",
        "settings.voice_trigger.label": "Voice trigger mode:",
        "settings.voice_trigger.desc": "Choose how Ctrl+S starts voice recording.",
        "settings.voice_trigger.toggle": "Press to start/press again to finish",
        "settings.voice_trigger.hold": "Hold to record/release to finish",
        "settings.ok": "OK",
        "settings.ok.desc": "Press to save settings",
        "settings.voice_button.desc.toggle": "Press to start voice input, press again to finish.",
        "settings.voice_button.desc.hold": "Press and hold to record, release to finish.",
        "settings.voice_button.tooltip.toggle": "Voice input (Ctrl+S: press to start/press again to finish)",
        "settings.voice_button.tooltip.hold": "Voice input (Ctrl+S: hold to record/release to finish)",

        # ====== Main flow status / speak texts  ======
        "speak.login.success": "login success! Username: {username}",
        "speak.login.failed": "The username or password is incorrect. Please try again",
        "speak.login.invalid_input": "Invalid Input",
        "speak.login.trying": "trying to login",
        "speak.logout.logging_out": "Logging out",
        "speak.logout.success": "Logout successful",
        "speak.flow.activate_login": "Activate Login Phase",
        "speak.flow.activate_login_input": "Activate Login Phase, please input your username and password",
        "speak.common.confirm_or_cancel": "Press Enter to confirm, or press Delete to cancel.",
        "speak.common.cancel": "Cancel",
        "speak.common.press_tab_next_option": "Press Tab to select the next option.",
        "speak.settings.engine_on": "Turn on speech engine",
        "speak.settings.engine_off": "Turn off speech engine",
        "speak.settings.saved": "User preferences saved",
        "speak.settings.opened_hint": "Settings opened. Please use Tab to select an option and Enter to confirm.",
        "speak.game.bot_started": "Bot game started",
        "speak.game.select_bot_then_start": "Please select the bot you want to play, then press Enter or Space to start",
        "speak.game.bot_selected": "{name} is selected",
        "speak.game.existing_game_found": "Existing game found. ",
        "speak.game.opponent_last_move": "Opponent last move: {src} to {dest}",
        "speak.game.select_category_time_control": "Select {category} time control",
        "speak.game.time_control_selected": "{name} selected. Press OK to start game.",
        "speak.game.macro_under_attack_count": "Macro view: {count} pieces are under attack.",
        "speak.game.and_more_count": "And {count} more.",
        "speak.game.no_timer_computer_mode": "No timer for computer mode",
        "speak.game.wait_opponent_move": "Please wait for your opponent's move",
        "speak.game.not_started_wait_matchmaking": "Game has not started yet. Please wait for matchmaking to finish.",
        "speak.game.select_time_control_category": "Select time control category",
        "speak.game.restart_computer_game": "Restart computer game",
        "speak.game.starting_new_game": "Starting a new game",
        "speak.game.returned_home": "You have returned to home page",
        "speak.game.no_active_macro_unavailable": "No active game. Macro view is unavailable right now.",
        "speak.game.color_not_assigned": "Color is not assigned yet. Please start a game first.",
        "speak.game.no_pieces_under_attack": "No pieces are under attack",
        "speak.game.no_active_start_or_resume": "No active game. Please start or resume a game first.",
        "speak.game.macro_view_failed": "Macro view failed.",
        "speak.mode.command_mode_hint": "Command mode. You can type your move here.",
        "speak.mode.arrow_mode": "Arrow mode",
        "speak.analysis.analyzing_current_game": "Analyzing current game situation",
        "speak.analysis.unable_to_analyze": "Unable to analyze game situation",
        "speak.analysis.free_review_used": "You have used your free Game Review for the day.",
        "speak.analysis.login_required": "Please login for Game Review function",
        "speak.analysis.this_is_beginning": "This is the beginning",
        "speak.analysis.this_is_last_move": "This is the last move",
        "speak.analysis.current_is_best": "The current move is the best move",
        "speak.audio.processing_wait": "Audio is being processed, please wait.",
        "speak.audio.sr_server_unreachable": "Speech recognition server is unreachable.",
        "speak.puzzle.limit_reached": "You have reached the puzzle limit for your account. Returning to home page.",
        "speak.puzzle.correct_next_action": "Correct. Please select next action.",
        "speak.puzzle.incorrect_ended": "Incorrect, puzzle run ended. Please select next action.",
        "speak.chat.user_input": "User input: {message}",
        "speak.chat.delegate_to_ai_wait": "I will pass this question to AI first. Please wait.",
        "speak.flow.select_bot_category": "Select bot category, by pressing tab key",
        "speak.flow.select_bot_category": "Select bot category, by pressing tab key",
        "speak.flow.select_time_controls": "Select Time Controls",

        "speak.game.still_initializing": "Still {sentence}",
        "speak.game.resign_before_new": "Please resign before start a new game",
        "speak.game.computer_mode_selected": "computer engine mode <>{sentence}",
        "speak.game.online_mode_selected": "online player mode <>{sentence}",
        "speak.game.match_not_started": "Match not started yet. Please wait a moment.",
        "speak.game.online_page_not_ready": "Page is not fully loaded yet. Please wait a moment.",
        "speak.game.undo.no_move": "There is no move to undo.",
        "speak.game.undo.done": "Last move has been undone.",

        # ====== Speak template texts (moved from enum_helper.Speak_template) ======
        "speak.template.welcome_sentence": "Welcome to chess bot!! ",
        "speak.template.game_intro_sentence": "press TAB key to navigate options. <> press spacebar or enter key to confirm your selection. <> press control R to repeat last sentence. <> press control O to find availble options. <> press control Q to summon Chatbot to answer your questions.",
        "speak.template.setting_state_help_message": "Press Control + 1 to play with computer. Press Control + 2 to play with other online player. Press Control + 3 to play with puzzle mode. Or press tab key to select from buttons. You can also press Control + S to start record voice input, and press Control + S again to stop. ",
        "speak.template.setting_state_vinput_help_message": "Say Computer or bot for Computer Mode. Say Online or Player for Online Player Mode.",
        "speak.template.initialize_game_sentence": "Initializing game for you",
        "speak.template.init_state_help_message": "please wait the initializing process",
        "speak.template.select_computer_help_message": "Press Tab key to select the bot category and press enter key to select the bot you want to play with.",
        "speak.template.select_online_help_message": "Press Tab key to select the Time Control for Online Game and press enter key to select the Time Control.",
        "speak.template.select_computer_vinput_help_message": "Say the Bot Category to select the Category. Then Say the bot name to select the bot.",
        "speak.template.select_online_vinput_help_message": "Say the time control with format <minute plus increment> to select. For example, say ten plus zero to select 10 minute with 0 second time increment, say fifteen plus ten to select 15 minute with 10 seconds time increment.",
        "speak.template.game_state_help_message": "You can press control F for command mode or press control J for arrow mode",
        "speak.template.command_panel_help_message": "Press tab key to find other functions <> or press control J for arrow mode",
        "speak.template.command_panel_vinput_help_message": "For moving pieces, say the chess move with format <source to destination>. For example, E2 to E4.",
        "speak.template.arrow_mode_help_message": "use arrow key to travel the chess board <> use space bar to select the piece to move <> and the square to place <>",
        "speak.template.opponent_move_sentence": "{color} {piece} moved to {square} ",
        "speak.template.ask_for_promote_type": "please indicate promote type by first letter",
        "speak.template.confirm_move": "Confirm move {source} to {destination} ",
        "speak.template.user_resign": "Resigned",
        "speak.template.check_time_sentence": "you remain {user}, opponent remain {opponent}",
        "speak.template.user_black_side_sentence": "You are playing as black.",
        "speak.template.user_white_side_sentence": "You are playing as white.",
        "speak.template.analysis_help_message": "Press Right Arrow Key for next move. Press Left Arrow Key for previous move. Press Up Arrow Key for the first move. Press E for explanation. Press B to get the best move. Press C to get the current move. Or press tab key to select function from buttons.",

        # ====== Rule-based chatbot canned responses (moved from enum_helper.response) ======
        "chat.response.greetings": "Hi! I am here to help you with any questions. You can ask me about how to use this software.",
        "chat.response.howareyou": "I'm doing well, thank you for asking!",
        "chat.response.help": "You can navigate different options by pressing Tab key or Arrows. When entered in a chess game, there are 3 input mode. Press Ctrl F for the default keyboard base interface. <> Ctrl J for Arrow mode that allow you to navagate through the board and move pieces by choosing target and destination grid using space bar. <> Ctrl S to activate voice input and press Ctrl S again to finish your input. <> You can ask for arrow mode and voice input for more information. There are also some shortcuts availble. You can ask me about the shortcuts if you are interested.",
        "chat.response.arrow_mode": "Press Ctrl J while conducting a chess game to enter arrow mode. <> You can navigate the chessboard using arrow key and move chess piece by pressing spacebar to select source and destination grid.",
        "chat.response.voice_input": "Press Ctrl S to activate Voice Input. Press Ctrl S again to finish Voice Input. You can select game mode by saying the game mode keyword you want to play. <> Computer for Computer Mode, Online for Online Player Mode, Puzzle for Puzzle Mode. <> You can also perform chess move by saying the UCI notation, which means the source grid and destination grid in order. For example, a sentence like 'move e2 to e4' indicates move the chess piece on e2 to e4. <> You can also resign by saying resign or surrender.",
        "chat.response.shortcut": "Press Ctrl Q to activate chat bot. \n<> Ctrl O for avalible options. <> For game mode selection, Press Ctrl 1 for computer mode. <> Ctrl 2 for online player mode. <> Ctrl 3 for puzzle mode. <> For Game Review Mode, Press A to enter game review mode. Press B for best move. Left arrow for next chess move. Right arrow for previous chess move.",

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
        "ui.play.computer.category_hint": "按 Tab 選擇選項，按 Enter 或空白鍵確認選項。",

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
        "ui.current_game_analysis.button": "目前局面分析",
        "ui.current_game_analysis.desc": "分析目前棋局狀況",
        "ui.macro_view.button": "宏觀視圖",
        "ui.common.play": "開始",
        "ui.common.back_to_category": "返回類別",
        "ui.common.back_to_previous_page": "回上一頁",
        "ui.common.ok": "確定",

        # ====== Chatbot window ======
        "chat.voice_button.tooltip": "語音輸入（Ctrl+S）",
        "chat.voice_button.desc": "按下開始語音輸入，再按一次結束語音輸入。",
        "chat.message_input.desc": "你可以在此輸入訊息。",
        "chat.send_button.text": "送出",
        "chat.send_button.desc": "按下送出訊息",
        "chat.welcome": "哈囉！我可以怎麼幫你？",
        "chat.user_label": "你",
        "chat.bot_label": "聊天機器人",
        "chat.macro.none_under_attack": "宏觀視圖：目前沒有棋子被攻擊。",
        "chat.macro.under_attack_count": "宏觀視圖：有 {count} 枚棋子正被攻擊。",
        "chat.you_prefix": "你：{message}",
        "chat.bot_prefix": "聊天機器人：",
        "chat.bot_line": "聊天機器人：{message}",

        # ====== System / info dialogs ======
        "dialog.information.title": "資訊",
        "dialog.information.text": "這是一則資訊訊息。",
        "dialog.confirm.title": "確認對話框",
        "dialog.confirm.prefix": "確認 {message}",
        "dialog.confirm.resign_message": "按 Enter 確認從目前對局認輸，或按 Delete 取消",
        "startup.audio_reminder.title": "音訊提醒",
        "startup.audio_reminder.message": "本軟體為視障使用者設計，請確認系統音訊已開啟，以便接收語音引導與協助。",
        "startup.audio_reminder.confirm": "{message} 按 Enter 以確認。",

        # ====== Speak texts ======
        "speak.login.success": "登入成功！使用者名稱：{username}",
        "speak.login.failed": "使用者名稱或密碼不正確，請再試一次",
        "speak.login.invalid_input": "輸入無效",
        "speak.login.trying": "正在嘗試登入",
        "speak.logout.logging_out": "正在登出",
        "speak.logout.success": "登出成功",
        "speak.flow.activate_login": "已進入登入流程",
        "speak.flow.activate_login_input": "已進入登入流程，請輸入你的使用者名稱與密碼",
        "speak.common.confirm_or_cancel": "按 Enter 確認，或按 Delete 取消。",
        "speak.common.cancel": "取消",
        "speak.common.press_tab_next_option": "按 Tab 以選擇下一個選項。",
        "speak.settings.engine_on": "已開啟語音引擎",
        "speak.settings.engine_off": "已關閉語音引擎",
        "speak.settings.saved": "使用者偏好已儲存",
        "speak.settings.opened_hint": "設定已開啟，請使用 Tab 選擇選項，按 Enter 確認。",
        "speak.game.bot_started": "電腦對局已開始",
        "speak.game.select_bot_then_start": "請先選擇你要對戰的機器人，然後按 Enter 或空白鍵開始",
        "speak.game.bot_selected": "已選擇 {name}",
        "speak.game.existing_game_found": "已找到未完成對局。",
        "speak.game.opponent_last_move": "對手上一步：{src} 到 {dest}",
        "speak.game.select_category_time_control": "請選擇 {category} 的時間控制",
        "speak.game.time_control_selected": "已選擇 {name}，按確定開始對局。",
        "speak.game.macro_under_attack_count": "宏觀視圖：有 {count} 枚棋子正被攻擊。",
        "speak.game.and_more_count": "另外還有 {count} 枚。",
        "speak.game.no_timer_computer_mode": "電腦模式沒有計時器",
        "speak.game.wait_opponent_move": "請等待對手走棋",
        "speak.game.not_started_wait_matchmaking": "對局尚未開始，請等待配對完成。",
        "speak.game.select_time_control_category": "請選擇時間控制類別",
        "speak.game.restart_computer_game": "重新開始電腦對局",
        "speak.game.starting_new_game": "正在開始新對局",
        "speak.game.returned_home": "你已返回首頁",
        "speak.game.no_active_macro_unavailable": "目前沒有進行中的對局，暫時無法使用宏觀視圖。",
        "speak.game.color_not_assigned": "尚未分配顏色，請先開始對局。",
        "speak.game.no_pieces_under_attack": "目前沒有棋子被攻擊",
        "speak.game.no_active_start_or_resume": "目前沒有進行中的對局，請先開始或恢復對局。",
        "speak.game.macro_view_failed": "宏觀視圖執行失敗。",
        "speak.mode.command_mode_hint": "指令模式。你可以在這裡輸入走法。",
        "speak.mode.arrow_mode": "方向鍵模式",
        "speak.analysis.analyzing_current_game": "正在分析目前局面",
        "speak.analysis.unable_to_analyze": "無法分析目前局面",
        "speak.analysis.free_review_used": "你今天的免費棋局複盤次數已用完。",
        "speak.analysis.login_required": "請先登入才能使用棋局複盤功能",
        "speak.analysis.this_is_beginning": "這是開局位置",
        "speak.analysis.this_is_last_move": "這是最後一步",
        "speak.analysis.current_is_best": "目前這一步就是最佳步",
        "speak.audio.processing_wait": "語音正在處理中，請稍候。",
        "speak.audio.sr_server_unreachable": "語音辨識伺服器目前無法連線。",
        "speak.puzzle.limit_reached": "你的帳號已達到今日解題上限，將返回首頁。",
        "speak.puzzle.correct_next_action": "正確，請選擇下一步操作。",
        "speak.puzzle.incorrect_ended": "錯誤，解題已結束，請選擇下一步操作。",
        "speak.chat.user_input": "使用者輸入：{message}",
        "speak.chat.delegate_to_ai_wait": "我先把這個問題交給 AI，請稍候。",
        "speak.flow.select_bot_category": "請選擇電腦類別",
        "speak.flow.select_bot_category": "請選擇電腦類別",
        "speak.flow.select_time_controls": "請選擇時間控制",

        "speak.game.still_initializing": "仍在初始化：{sentence}",
        "speak.game.resign_before_new": "開始新對局前請先認輸",
        "speak.game.computer_mode_selected": "電腦引擎模式 <>{sentence}",
        "speak.game.online_mode_selected": "線上對戰模式 <>{sentence}",
        "speak.game.match_not_started": "對局尚未開始，請重新選擇一次時間控制。",
        "speak.game.online_page_not_ready": "頁面尚未載入完成，請稍候。",
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
        "settings.font_size.label": "字體大小：",
        "settings.font_size.desc": "使用左右方向鍵調整文字大小。",
        "settings.rate.label": "語速：",
        "settings.rate.desc": "使用左右方向鍵調整語速。",
        "settings.volume.label": "音量：",
        "settings.volume.desc": "使用左右方向鍵調整音量。",
        "settings.voice_trigger.label": "語音觸發方式：",
        "settings.voice_trigger.desc": "選擇 Ctrl+S 的錄音啟動方式。",
        "settings.voice_trigger.toggle": "按一次開始/再按一次結束",
        "settings.voice_trigger.hold": "按住錄音、放開結束",
        "settings.ok": "確定",
        "settings.ok.desc": "按下以儲存設定",
        "settings.language.desc": "使用上下方向鍵變更語言。",
        "settings.voice_button.desc.toggle": "按下開始語音輸入，再按一次結束語音輸入。",
        "settings.voice_button.desc.hold": "按住開始語音輸入，放開結束語音輸入。",
        "settings.voice_button.tooltip.toggle": "語音輸入（Ctrl+S：按一次開始/再按一次結束）",
        "settings.voice_button.tooltip.hold": "語音輸入（Ctrl+S：按住錄音、放開結束）",

        # ====== Speak template texts (moved from enum_helper.Speak_template) ======
        "speak.template.welcome_sentence": "歡迎使用西洋棋機器人！",
        "speak.template.game_intro_sentence": "按 Tab 鍵瀏覽選項。<> 按空白鍵或 Enter 確認選擇。<> 按 Ctrl+R 重複上一句。<> 按 Ctrl+O 尋找可用選項。<> 按 Ctrl+Q 叫出聊天機器人回答問題。",
        "speak.template.setting_state_help_message": "按 Ctrl+1 與電腦對戰。按 Ctrl+2 與線上玩家對戰。或使用 Tab 在按鈕間選擇。你也可以按 Ctrl+S 開始語音輸入，再按一次 Ctrl+S 結束。每次語音輸入只能執行一個動作。語音指令可按 Ctrl+Q 列出目前狀態可用選項。",
        "speak.template.setting_state_vinput_help_message": "說 Computer 或 bot 進入電腦模式；說 Online 或 Player 進入線上對戰模式。",
        "speak.template.initialize_game_sentence": "正在為你初始化對局",
        "speak.template.init_state_help_message": "請稍候，正在初始化",
        "speak.template.select_computer_help_message": "按 Tab 選擇機器人類別，並選擇你想對戰的機器人。",
        "speak.template.select_online_help_message": "按 Tab 選擇線上對局的時間控制。",
        "speak.template.select_computer_vinput_help_message": "先說出機器人類別以選擇類別，再說出機器人名稱以選擇機器人。",
        "speak.template.select_online_vinput_help_message": "用「分鐘加增量」的格式說出時間控制。例如說「ten plus zero」選擇 10 分鐘加 0 秒；說「fifteen plus ten」選擇 15 分鐘加 10 秒。",
        "speak.template.game_state_help_message": "你可以按 Ctrl+F 進入指令模式，或按 Ctrl+J 進入方向鍵模式。",
        "speak.template.command_panel_help_message": "按 Tab 尋找其他功能 <> 或按 Ctrl+J 切換到方向鍵模式",
        "speak.template.command_panel_vinput_help_message": "移動棋子時，請用「起點到終點」格式說出走法，例如 E2 到 E4。",
        "speak.template.arrow_mode_help_message": "使用方向鍵在棋盤上移動 <> 按空白鍵選擇要移動的棋子 <> 再按空白鍵選擇目的地 <>",
        "speak.template.opponent_move_sentence": "{color}{piece} 移動到 {square}",
        "speak.template.ask_for_promote_type": "請用第一個字母指定升變棋子類型",
        "speak.template.confirm_move": "確認走法：{source} 到 {destination}",
        "speak.template.user_resign": "已認輸",
        "speak.template.check_time_sentence": "你剩下 {user}，對手剩下 {opponent}",
        "speak.template.user_black_side_sentence": "你執黑。",
        "speak.template.user_white_side_sentence": "你執白。",
        "speak.template.analysis_help_message": "按右方向鍵到下一步。按左方向鍵到上一步。按上方向鍵到第一步。按 E 取得解釋。按 B 取得最佳步。按 C 取得目前步。或按 Tab 在按鈕間選擇功能。",

        # ====== Rule-based chatbot canned responses (moved from enum_helper.response) ======
        "chat.response.greetings": "嗨！我可以協助回答你的問題。你可以問我如何使用這個軟體。",
        "chat.response.howareyou": "我很好，謝謝你的關心！",
        "chat.response.help": "你可以按 Tab 或方向鍵瀏覽選項。進入對局後有三種輸入方式：按 Ctrl+F 使用預設的鍵盤指令介面；<> 按 Ctrl+J 進入方向鍵模式，用方向鍵移動並用空白鍵選擇起點與終點來走子；<> 按 Ctrl+S 開始語音輸入，再按一次 Ctrl+S 結束。你也可以問我方向鍵模式與語音輸入的更多資訊。還有一些快捷鍵可用；如果你想了解也可以問我。",
        "chat.response.arrow_mode": "在對局中按 Ctrl+J 進入方向鍵模式。<> 你可以用方向鍵瀏覽棋盤，並按空白鍵選擇起點與終點來移動棋子。",
        "chat.response.voice_input": "按 Ctrl+S 開始語音輸入，再按一次 Ctrl+S 結束。你可以說出想玩的模式關鍵字：<> Computer 代表電腦模式，Online 代表線上玩家模式，Puzzle 代表解題模式。<> 你也可以用 UCI 走法（起點格與終點格依序）來走子，例如說「move e2 to e4」。<> 你也可以說 resign 或 surrender 來認輸。",
        "chat.response.shortcut": "按 Ctrl+Q 啟用聊天機器人。\\n<> Ctrl+O 取得可用選項。<> 選擇遊戲模式：Ctrl+1 電腦模式、Ctrl+2 線上玩家模式、Ctrl+3 解題模式。<> 棋局複盤：按 A 進入複盤模式；按 B 取得最佳步；左方向鍵下一手、右方向鍵上一手。",
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
        "ui.play.computer.category_hint": "按 Tab 选择选项，按 Enter 或空格键确认选项。",

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
        "ui.current_game_analysis.button": "当前局面分析",
        "ui.current_game_analysis.desc": "分析当前棋局情况",
        "ui.macro_view.button": "宏观视图",
        "ui.common.play": "开始",
        "ui.common.back_to_category": "返回类别",
        "ui.common.back_to_previous_page": "回上一页",
        "ui.common.ok": "确定",

        # ====== Chatbot window ======
        "chat.voice_button.tooltip": "语音输入（Ctrl+S）",
        "chat.voice_button.desc": "按下开始语音输入，再按一次结束语音输入。",
        "chat.message_input.desc": "你可以在此输入消息。",
        "chat.send_button.text": "发送",
        "chat.send_button.desc": "按下发送消息",
        "chat.welcome": "你好！我可以怎么帮你？",
        "chat.user_label": "你",
        "chat.bot_label": "聊天机器人",
        "chat.macro.none_under_attack": "宏观视图：当前没有棋子被攻击。",
        "chat.macro.under_attack_count": "宏观视图：有 {count} 枚棋子正被攻击。",
        "chat.you_prefix": "你：{message}",
        "chat.bot_prefix": "聊天机器人：",
        "chat.bot_line": "聊天机器人：{message}",

        # ====== System / info dialogs ======
        "dialog.information.title": "信息",
        "dialog.information.text": "这是一则信息消息。",
        "dialog.confirm.title": "确认对话框",
        "dialog.confirm.prefix": "确认 {message}",
        "dialog.confirm.resign_message": "按 Enter 确认从当前对局认输，或按 Delete 取消",
        "startup.audio_reminder.title": "音频提醒",
        "startup.audio_reminder.message": "本软件为视障用户设计，请确认系统音频已开启，以便接收语音引导与协助。",
        "startup.audio_reminder.confirm": "{message} 按 Enter 以确认。",

        # ====== Speak texts ======
        "speak.login.success": "登录成功！用户名：{username}",
        "speak.login.failed": "用户名或密码不正确，请再试一次",
        "speak.login.invalid_input": "输入无效",
        "speak.login.trying": "正在尝试登录",
        "speak.logout.logging_out": "正在登出",
        "speak.logout.success": "登出成功",
        "speak.flow.activate_login": "已进入登录流程",
        "speak.flow.activate_login_input": "已进入登录流程，请输入你的用户名和密码",
        "speak.common.confirm_or_cancel": "按 Enter 确认，或按 Delete 取消。",
        "speak.common.cancel": "取消",
        "speak.common.press_tab_next_option": "按 Tab 选择下一个选项。",
        "speak.settings.engine_on": "已开启语音引擎",
        "speak.settings.engine_off": "已关闭语音引擎",
        "speak.settings.saved": "用户偏好已保存",
        "speak.settings.opened_hint": "设置已打开，请使用 Tab 选择选项，按 Enter 确认。",
        "speak.game.bot_started": "电脑对局已开始",
        "speak.game.select_bot_then_start": "请先选择你要对战的机器人，然后按 Enter 或空格键开始",
        "speak.game.bot_selected": "已选择 {name}",
        "speak.game.existing_game_found": "已找到未完成对局。",
        "speak.game.opponent_last_move": "对手上一步：{src} 到 {dest}",
        "speak.game.select_category_time_control": "请选择 {category} 的时间控制",
        "speak.game.time_control_selected": "已选择 {name}，按确定开始对局。",
        "speak.game.macro_under_attack_count": "宏观视图：有 {count} 枚棋子正被攻击。",
        "speak.game.and_more_count": "另外还有 {count} 枚。",
        "speak.game.no_timer_computer_mode": "电脑模式没有计时器",
        "speak.game.wait_opponent_move": "请等待对手走棋",
        "speak.game.not_started_wait_matchmaking": "对局尚未开始，请等待匹配完成。",
        "speak.game.select_time_control_category": "请选择时间控制类别",
        "speak.game.restart_computer_game": "重新开始电脑对局",
        "speak.game.starting_new_game": "正在开始新对局",
        "speak.game.returned_home": "你已返回首页",
        "speak.game.no_active_macro_unavailable": "当前没有进行中的对局，暂时无法使用宏观视图。",
        "speak.game.color_not_assigned": "尚未分配颜色，请先开始对局。",
        "speak.game.no_pieces_under_attack": "当前没有棋子被攻击",
        "speak.game.no_active_start_or_resume": "当前没有进行中的对局，请先开始或恢复对局。",
        "speak.game.macro_view_failed": "宏观视图执行失败。",
        "speak.mode.command_mode_hint": "指令模式。你可以在这里输入走法。",
        "speak.mode.arrow_mode": "方向键模式",
        "speak.analysis.analyzing_current_game": "正在分析当前局面",
        "speak.analysis.unable_to_analyze": "无法分析当前局面",
        "speak.analysis.free_review_used": "你今天的免费棋局复盘次数已用完。",
        "speak.analysis.login_required": "请先登录才能使用棋局复盘功能",
        "speak.analysis.this_is_beginning": "这是开局位置",
        "speak.analysis.this_is_last_move": "这是最后一步",
        "speak.analysis.current_is_best": "当前这一步就是最佳步",
        "speak.audio.processing_wait": "语音正在处理中，请稍候。",
        "speak.audio.sr_server_unreachable": "语音识别服务器当前无法连接。",
        "speak.puzzle.limit_reached": "你的账号已达到今日解题上限，将返回首页。",
        "speak.puzzle.correct_next_action": "正确，请选择下一步操作。",
        "speak.puzzle.incorrect_ended": "错误，解题已结束，请选择下一步操作。",
        "speak.chat.user_input": "用户输入：{message}",
        "speak.chat.delegate_to_ai_wait": "我先把这个问题交给 AI，请稍候。",
        "speak.flow.select_bot_category": "请选择电脑类别",
        "speak.flow.select_bot_category": "请选择电脑类别",
        "speak.flow.select_time_controls": "请选择时间控制",

        "speak.game.still_initializing": "仍在初始化：{sentence}",
        "speak.game.resign_before_new": "开始新对局前请先认输",
        "speak.game.computer_mode_selected": "电脑引擎模式 <>{sentence}",
        "speak.game.online_mode_selected": "在线对战模式 <>{sentence}",
        "speak.game.match_not_started": "对局尚未开始，请重新选择一次时间控制。",
        "speak.game.online_page_not_ready": "页面尚未加载完成，请稍候。",
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
        "settings.language.desc": "使用上下方向键切换语言。",
        "settings.language.en": "English",
        "settings.language.zh_tw": "繁體中文",
        "settings.language.zh_cn": "简体中文",
        "settings.engine.checkbox": "启用内建语音引擎",
        "settings.engine.checkbox.desc": "勾选使用内建语音引擎；取消勾选则仅播报重要信息。",
        "settings.font_size.label": "字体大小：",
        "settings.font_size.desc": "使用左右方向键调整字体大小。",
        "settings.rate.label": "语速：",
        "settings.rate.desc": "使用左右方向键调整语速。",
        "settings.volume.label": "音量：",
        "settings.volume.desc": "使用左右方向键调整音量。",
        "settings.voice_trigger.label": "语音触发方式：",
        "settings.voice_trigger.desc": "选择 Ctrl+S 的录音启动方式。",
        "settings.voice_trigger.toggle": "按一次开始/再按一次结束",
        "settings.voice_trigger.hold": "按住录音、松开结束",
        "settings.ok": "确定",
        "settings.ok.desc": "按下以保存设置",
        "settings.voice_button.desc.toggle": "按下开始语音输入，再按一次结束语音输入。",
        "settings.voice_button.desc.hold": "按住开始语音输入，松开结束语音输入。",
        "settings.voice_button.tooltip.toggle": "语音输入（Ctrl+S：按一次开始/再按一次结束）",
        "settings.voice_button.tooltip.hold": "语音输入（Ctrl+S：按住录音、松开结束）",

        # ====== Speak template texts (moved from enum_helper.Speak_template) ======
        "speak.template.welcome_sentence": "欢迎使用国际象棋机器人！",
        "speak.template.game_intro_sentence": "按 Tab 键浏览选项。<> 按空格键或 Enter 确认选择。<> 按 Ctrl+R 重复上一句。<> 按 Ctrl+O 查找可用选项。<> 按 Ctrl+Q 召唤聊天机器人回答问题。",
        "speak.template.setting_state_help_message": "按 Ctrl+1 与电脑对战。按 Ctrl+2 与在线玩家对战。或使用 Tab 在按钮间选择。你也可以按 Ctrl+S 开始语音输入，再按一次 Ctrl+S 结束。每次语音输入只能执行一个动作。语音指令可按 Ctrl+Q 列出当前状态可用选项。",
        "speak.template.setting_state_vinput_help_message": "说 Computer 或 bot 进入电脑模式；说 Online 或 Player 进入在线对战模式。",
        "speak.template.initialize_game_sentence": "正在为你初始化对局",
        "speak.template.init_state_help_message": "请稍候，正在初始化",
        "speak.template.select_computer_help_message": "按 Tab 选择机器人类别，并选择你想对战的机器人。",
        "speak.template.select_online_help_message": "按 Tab 选择在线对局的时间控制。",
        "speak.template.select_computer_vinput_help_message": "先说出机器人类别以选择类别，再说出机器人名称以选择机器人。",
        "speak.template.select_online_vinput_help_message": "用“分钟加增量”的格式说出时间控制。例如说“ten plus zero”选择 10 分钟加 0 秒；说“fifteen plus ten”选择 15 分钟加 10 秒。",
        "speak.template.game_state_help_message": "你可以按 Ctrl+F 进入指令模式，或按 Ctrl+J 进入方向键模式。",
        "speak.template.command_panel_help_message": "按 Tab 查找其他功能 <> 或按 Ctrl+J 切换到方向键模式",
        "speak.template.command_panel_vinput_help_message": "移动棋子时，请用“起点到终点”格式说出走法，例如 E2 到 E4。",
        "speak.template.arrow_mode_help_message": "使用方向键在棋盘上移动 <> 按空格键选择要移动的棋子 <> 再按空格键选择目的地 <>",
        "speak.template.opponent_move_sentence": "{color}{piece} 移动到 {square}",
        "speak.template.ask_for_promote_type": "请用第一个字母指定升变棋子类型",
        "speak.template.confirm_move": "确认走法：{source} 到 {destination}",
        "speak.template.user_resign": "已认输",
        "speak.template.check_time_sentence": "你剩下 {user}，对手剩下 {opponent}",
        "speak.template.user_black_side_sentence": "你执黑。",
        "speak.template.user_white_side_sentence": "你执白。",
        "speak.template.analysis_help_message": "按右方向键到下一步。按左方向键到上一步。按上方向键到第一步。按 E 获取解释。按 B 获取最佳步。按 C 获取当前步。或按 Tab 在按钮间选择功能。",

        # ====== Rule-based chatbot canned responses (moved from enum_helper.response) ======
        "chat.response.greetings": "嗨！我可以协助回答你的问题。你可以问我如何使用这个软件。",
        "chat.response.howareyou": "我很好，谢谢你的关心！",
        "chat.response.help": "你可以按 Tab 或方向键浏览选项。进入对局后有三种输入方式：按 Ctrl+F 使用默认的键盘指令界面；<> 按 Ctrl+J 进入方向键模式，用方向键移动并用空格键选择起点与终点来走子；<> 按 Ctrl+S 开始语音输入，再按一次 Ctrl+S 结束。你也可以问我方向键模式与语音输入的更多信息。还有一些快捷键可用；如果你想了解也可以问我。",
        "chat.response.arrow_mode": "在对局中按 Ctrl+J 进入方向键模式。<> 你可以用方向键浏览棋盘，并按空格键选择起点与终点来移动棋子。",
        "chat.response.voice_input": "按 Ctrl+S 开始语音输入，再按一次 Ctrl+S 结束。你可以说出想玩的模式关键字：<> Computer 代表电脑模式，Online 代表在线玩家模式，Puzzle 代表解题模式。<> 你也可以用 UCI 走法（起点格与终点格依序）来走子，例如说“move e2 to e4”。<> 你也可以说 resign 或 surrender 来认输。",
        "chat.response.shortcut": "按 Ctrl+Q 启用聊天机器人。\\n<> Ctrl+O 获取可用选项。<> 选择游戏模式：Ctrl+1 电脑模式、Ctrl+2 在线玩家模式、Ctrl+3 解题模式。<> 棋局复盘：按 A 进入复盘模式；按 B 获取最佳步；左方向键下一手、右方向键上一手。",
    }
}

_external_cache: Dict[str, Dict[str, str]] = {}


def set_language(lang: str) -> None:

    global _current_lang
    _current_lang = _normalize_lang_code(lang)


def get_language() -> str:
    return _current_lang


def _get_lang_table(lang: str) -> Dict[str, str]:

    if lang not in _external_cache:
        _external_cache[lang] = _load_external_translations(lang)

    table = dict(TRANSLATIONS.get(lang, {}))
    table.update(_external_cache.get(lang, {}))
    return table


def t(key: str, **params: Any) -> str:

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

            pass
    return text


