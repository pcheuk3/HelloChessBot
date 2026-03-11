from enum import Enum

class Game_play_mode(Enum):
    computer_mode = "COMPUTER_MODE"
    online_mode = "ONLINE_MODE"
    puzzle_mode = "PUZZLE_MODE"
    analysis_mode = "ANALYSIS_MODE"

class Input_mode(Enum):
    command_mode = "COMMAND_MODE"
    arrow_mode = "ARROW_MDOE"


class Bot_flow_status(Enum):
    login_status = "LOGIN_STATUS"
    setting_status = "SETTING_STATUS"
    select_status = "SELECT_STATUS"
    board_init_status = "BOARD_INIT_STATUS"
    game_play_status = "GAME_PLAY_STATUS"
    game_end_status = "GAME_END_STATUS"
    puzzle_end_status = "PUZZLE_END_STATUS"


class Game_flow_status(Enum):
    # sub-routine of game play status
    not_start = "NOT_START"
    user_turn = "USER_TURN"
    opponent_turn = "OPPONENT_TURN"
    game_end = "GAME_END"


class Speak_template(Enum):
    ###setting
    welcome_sentense = "Welcome to chess bot!! "
    game_intro_sentense = "press TAB key to navigate options. <> press spacebar or enter key to confirm your selection. <> press control R to repeat last sentence. <> press control O to find availble options. <> press control Q to summon Chatbot to answer your questions."
    setting_state_help_message = (
        "Press Control + 1 to play with computer. Press Control + 2 to play with other online player. Or press tab key to select from buttons. You can also press Control + S to start record voice input, and press Control + S again to stop. Each voice input can only perform one action. For voice input command, press Control Q to list the available options in current state."
    )
    setting_state_vinput_help_message = "Say Computer or bot for Computer Mode. Say Online or Player for Online Player Mode."

    ###initialization
    initialize_game_sentense = "Initializing game for you"
    init_state_help_message = "please wait the initializing process"

    #Select State
    select_computer_help_message = "Press Tab key to select the bot category and choose the bot you want to play with."
    select_online_help_message = "Press Tab key to select the Time Control for Online Game."
    select_computer_vinput_help_message = "Say the Bot Category to select the Category. Then Say the bot name to select the bot."
    select_online_vinput_help_message = "Say the time control with format <minute plus increment> to select. For example, say ten plus zero to select 10 minute with 0 second time increment, say fifteen plus ten to select 15 minute with 10 seconds time increment."

    ###game play
    game_state_help_message = (
        "You can press control F for command mode or press control J for arrow mode"
    )
    command_panel_help_message = (
        "Press tab key to find other functions <> or press control J for arrow mode"
    )
    command_panel_vinput_help_message = (
        "For moving pieces, say the chess move with format <source to destination>. For example, E2 to E4."
    )

    arrow_mode_help_message = "use arrow key to travel the chess board <> use space bar to select the piece to move <> and the square to place <>"

    opponent_move_sentense = "{0} {1} moved to {2} "

    ask_for_promote_type = "please indicate promote type by first letter"
    confirm_move = "Confirm move {0} to {1} "
    user_resign = "Resigned"
    check_time_sentense = "you remain {0}, opponent remain {1}"

    user_black_side_sentense = (
        "You are playing as black."
    )
    user_white_side_sentense = "You are playing as white."

    #analysis
    analysis_help_message = "Press Right Arrow Key for next move. Press Left Arrow Key for previous move. Press Up Arrow Key for the first move. Press E for explanation. Press B to get the best move. Press C to get the current move. Or press tab key to select function from buttons."


class english_chess_pieces_name(Enum):
    King = "king"
    Queen = "queen"
    Bishop = "bishop"
    Rook = "rook"
    Knight = "knight"
    Pawn = "pawn"

class bot_List(Enum):

    backToSchool_ChadThaddeusBradley = {"name": "Chad Thaddeus Bradley", "rating": "575", "category": "Back To School"} #tick
    backToSchool_StanleyFunk = {"name": "Stanley Funk", "rating": "1065", "category": "Back To School"} #tick
    backToSchool_BaileyHoops = {"name": "Bailey Hoops", "rating": "1450", "category": "Back To School"} #tick
    backToSchool_ProfessorPassant = {"name": "Professor Passant", "rating": "2025", "category": "Back To School"} #tick
    backToSchool_Eugene = {"name": "Eugene", "rating": "?", "category": "Back To School"} #tick

class coach(Enum):
    #5
    coach_CoachDanny = {"name": "Coach Danny", "rating": "400", "category": "Coach"} #tick
    coach_CoachMay = {"name": "Coach May", "rating": "800", "category": "Coach"} #tick
    coach_CoachDan = {"name": "Coach Dan", "rating": "1200", "category": "Coach"}
    coach_CoachMonica = {"name": "Coach Monica", "rating": "1600", "category": "Coach"} 
    coach_CoachDave = {"name": "Coach Dave", "rating": "2000", "category": "Coach"}

class adaptive(Enum):
    #5
    adaptive_Jimmy = {"name": "Jimmy", "rating": "600", "category": "Adaptive"}  #tick
    adaptive_Nisha = {"name": "Nisha", "rating": "900", "category": "Adaptive"}
    adaptive_Tomas = {"name": "Tomas", "rating": "1200", "category": "Adaptive"}
    adaptive_Devon = {"name": "Devon", "rating": "1600", "category": "Adaptive"}
    adaptive_Natasha = {"name": "Natasha", "rating": "2000", "category": "Adaptive"}

class beginner(Enum):
    #15
    beginner_Martin = {"name": "Martin", "rating": "250", "category": "Beginner"} #tick
    beginner_Wayne = {"name": "Wayne", "rating": "250", "category": "Beginner"}
    beginner_Fabian = {"name": "Fabian", "rating": "250", "category": "Beginner"}
    beginner_Juan = {"name": "Juan", "rating": "400", "category": "Beginner"}
    beginner_Filip = {"name": "Filip", "rating": "400", "category": "Beginner"}
    beginner_Elani = {"name": "Elani", "rating": "400", "category": "Beginner"} #tick
    beginner_Noel = {"name": "Noel", "rating": "550", "category": "Beginner"}
    beginner_Oliver = {"name": "Oliver", "rating": "550", "category": "Beginner"}
    beginner_Milica = {"name": "Milica", "rating": "550", "category": "Beginner"}
    beginner_Aron = {"name": "Aron", "rating": "700", "category": "Beginner"}
    beginner_Janjay = {"name": "Janjay", "rating": "700", "category": "Beginner"} #tick
    beginner_Mina = {"name": "Mina", "rating": "700", "category": "Beginner"}
    beginner_Zara = {"name": "Zara", "rating": "850", "category": "Beginner"}
    beginner_Santiago = {"name": "Santiago", "rating": "850", "category": "Beginner"}
    beginner_Karim = {"name": "Karim", "rating": "850", "category": "Beginner"}

class intermediate(Enum):
    #15
    intermediate_Maria = {"name": "Maria", "rating": "1000", "category": "Intermediate"} #tick
    intermediate_Maxim = {"name": "Maxim", "rating": "1000", "category": "Intermediate"}
    intermediate_Hans = {"name": "Hans", "rating": "1000", "category": "Intermediate"}
    intermediate_Azeez = {"name": "Azeez", "rating": "1100", "category": "Intermediate"}
    intermediate_Laura = {"name": "Laura", "rating": "1100", "category": "Intermediate"}
    intermediate_Sven = {"name": "Sven", "rating": "1100", "category": "Intermediate"} #tick
    intermediate_Emir = {"name": "Emir", "rating": "1200", "category": "Intermediate"}
    intermediate_Elena = {"name": "Elena", "rating": "1200", "category": "Intermediate"}
    intermediate_Wilson = {"name": "Wilson", "rating": "1200", "category": "Intermediate"}
    intermediate_Vinh = {"name": "Vinh", "rating": "1300", "category": "Intermediate"}
    intermediate_Nelson = {"name": "Nelson", "rating": "1300", "category": "Intermediate"} #tick
    intermediate_Jade = {"name": "Jade", "rating": "1300", "category": "Intermediate"}
    intermediate_David = {"name": "David", "rating": "1400", "category": "Intermediate"}
    intermediate_Ali = {"name": "Ali", "rating": "1400", "category": "Intermediate"}
    intermediate_Mateo = {"name": "Mateo", "rating": "1400", "category": "Intermediate"}

class advanced(Enum):
    #20
    advanced_Wendy = {"name": "Wendy", "rating": "1500", "category": "Advanced"} #tick
    advanced_Antonio = {"name": "Antonio", "rating": "1500", "category": "Advanced"}
    advanced_Pierre = {"name": "Pierre", "rating": "1500", "category": "Advanced"}
    advanced_Pablo = {"name": "Pablo", "rating": "1600", "category": "Advanced"}
    advanced_Joel = {"name": "Joel", "rating": "1600", "category": "Advanced"}
    advanced_Isabel = {"name": "Isabel", "rating": "1600", "category": "Advanced"} #tick
    advanced_Arthur = {"name": "Arthur", "rating": "1700", "category": "Advanced"}
    advanced_Jonas = {"name": "Jonas", "rating": "1700", "category": "Advanced"}
    advanced_Isla = {"name": "Isla", "rating": "1700", "category": "Advanced"}
    advanced_Lorenzo = {"name": "Lorenzo", "rating": "1800", "category": "Advanced"}
    advanced_Wally = {"name": "Wally", "rating": "1800", "category": "Advanced"} #tick
    advanced_Julia = {"name": "Julia", "rating": "1800", "category": "Advanced"}
    advanced_Miguel = {"name": "Miguel", "rating": "1900", "category": "Advanced"}
    advanced_Xavier = {"name": "Xavier", "rating": "1900", "category": "Advanced"}
    advanced_Olga = {"name": "Olga", "rating": "1900", "category": "Advanced"}
    advanced_Li = {"name": "Li", "rating": "2000", "category": "Advanced"} #tick
    advanced_Charles = {"name": "Charles", "rating": "2000", "category": "Advanced"}
    advanced_Fatima = {"name": "Fatima", "rating": "2000", "category": "Advanced"}
    advanced_Manuel = {"name": "Manuel", "rating": "2100", "category": "Advanced"}
    advanced_Oscar = {"name": "Oscar", "rating": "2100", "category": "Advanced"}

class master(Enum):
    #10
    master_Nora = {"name": "Nora", "rating": "2200", "category": "Master"} #tick
    master_Noam = {"name": "Noam", "rating": "2200", "category": "Master"}
    master_Ahmed = {"name": "Ahmed", "rating": "2200", "category": "Master"}
    master_Sakura = {"name": "Sakura", "rating": "2200", "category": "Master"}
    master_Arjun = {"name": "Arjun", "rating": "2300", "category": "Master"}
    master_Francis = {"name": "Francis", "rating": "2300", "category": "Master"} #tick
    master_Sofia = {"name": "Sofia", "rating": "2300", "category": "Master"}
    master_Alexander = {"name": "Alexander", "rating": "2450", "category": "Master"}
    master_Luke = {"name": "Luke", "rating": "2450", "category": "Master"}
    master_Wei = {"name": "Wei", "rating": "2450", "category": "Master"}

class athletes(Enum):
    #11
    athletes_JustinReid = {"name": "Justin Reid", "rating": "1300", "category": "Athletes"}
    athletes_JoeyVotto = {"name": "Joey Votto", "rating": "1575", "category": "Athletes"}
    athletes_LarryFitzgeraldJr = {"name": "Larry Fitzgerald Jr.", "rating": "1250", "category": "Athletes"} #tick
    athletes_JaylenBrown = {"name": "Jaylen Brown", "rating": "1500", "category": "Athletes"} #tick
    athletes_DrueTranquill = {"name": "Drue Tranquill", "rating": "1300", "category": "Athletes"}
    athletes_GordonHayward = {"name": "Gordon Hayward", "rating": "1350", "category": "Athletes"} #tick
    athletes_ChidobeAwuzie = {"name": "Chidobe Awuzie", "rating": "1400", "category": "Athletes"} #tick
    athletes_ChristianPulisic = {"name": "Christian Pulisic", "rating": "1500", "category": "Athletes"} #tick
    athletes_JamieJaquezJr = {"name": "Jamie Jaquez Jr.", "rating": "1500", "category": "Athletes"}
    athletes_DarylMorey = {"name": "Daryl Morey", "rating": "1550", "category": "Athletes"} #tick
    athletes_LukAI = {"name": "Luk.AI", "rating": "2500", "category": "Athletes"} #tick

class musicians(Enum):
    #2
    musicians_ThomasMars = {"name": "Thomas Mars", "rating": "1500", "category": "Musicians"} #tick
    musicians_Logic = {"name": "Logic", "rating": "1500", "category": "Musicians"}
    musicians_Wallows = {"name": "Wallows", "rating": "1200", "category": "Musicians"} #tick

class creators(Enum):
    #32
    creators_xQc = {"name": "xQc", "rating": "1200", "category": "Creators"} #tick
    creators_MarkRober = {"name": "Mark Rober", "rating": "1200", "category": "Creators"} #tick
    creators_MrBeast = {"name": "MrBeast", "rating": "1100", "category": "Creators"} #tick
    creators_Pokimane = {"name": "Pokimane", "rating": "1000", "category": "Creators"} #tick
    creators_LudWig = {"name": "LudWig", "rating": "1200", "category": "Creators"} #tick
    creators_QTCinderella = {"name": "QTCinderella", "rating": "900", "category": "Creators"} #tick
    creators_boxbox = {"name": "boxbox", "rating": "1400", "category": "Creators"} #tick
    creators_HarryMack = {"name": "HarryMack", "rating": "600", "category": "Creators"} #tick
    creators_Tectone = {"name": "Tectone", "rating": "700", "category": "Creators"} #tick
    creators_Sapnap = {"name": "Sapnap", "rating": "1000", "category": "Creators"} #tick
    creators_Wirtual = {"name": "Wirtual", "rating": "1100", "category": "Creators"} #tick
    creators_IamCristinini = {"name": "IamCristinini", "rating": "800", "category": "Creators"} #tick
    creators_Neeko = {"name": "Neeko", "rating": "800", "category": "Creators"} #tick
    creators_GothamChess = {"name": "GothamChess", "rating": "2500", "category": "Creators"}
    creators_Andrea = {"name": "Andrea", "rating": "1801", "category": "Creators"}
    creators_Alexandra = {"name": "Alexandra", "rating": "2100", "category": "Creators"}
    creators_Eric = {"name": "Eric", "rating": "2600", "category": "Creators"} #tick
    creators_Aman = {"name": "Aman", "rating": "2550", "category": "Creators"}
    creators_Anna = {"name": "Anna", "rating": "2400", "category": "Creators"}
    creators_Nemo = {"name": "Nemo", "rating": "2300", "category": "Creators"}
    creators_AnnaCramling = {"name": "Anna Cramling", "rating": "2100", "category": "Creators"}
    creators_Samay = {"name": "Samay", "rating": "1800", "category": "Creators"} #tick
    creators_Naycir = {"name": "Naycir", "rating": "1300", "category": "Creators"}
    creators_Canty = {"name": "Pokimane", "rating": "2300", "category": "Creators"}
    creators_ElDeplorable = {"name": "El Deplorable", "rating": "2200", "category": "Creators"} #tick
    creators_Bartosz = {"name": "Bartosz", "rating": "2000", "category": "Creators"}
    creators_CDawgVA = {"name": "CDawgVA", "rating": "900", "category": "Creators"} #tick
    creators_Hafu = {"name": "Hafu", "rating": "1500", "category": "Creators"} #tick
    creators_Sardoche = {"name": "Sardoche", "rating": "1550", "category": "Creators"} #tick
    creators_Fundy = {"name": "Fundy", "rating": "1500", "category": "Creators"} #tick
    creators_Sabo = {"name": "Sabo", "rating": "1927", "category": "Creators"} #tick
    creators_SonicFox = {"name": "SonicFox", "rating": "1750", "category": "Creators"} #tick
    creators_ReyEnigma = {"name": "Rey Enigma", "rating": "2500", "category": "Creators"} #tick

class top_players(Enum):
    #22
    topPlayers_Hikaru = {"name": "Hikaru", "rating": "2820", "category": "Top Players"} #tick
    topPlayers_AnnaMuzychuk = {"name": "Anna Muzychuk", "rating": "2606", "category": "Top Players"}
    topPlayers_Vishy = {"name": "Vishy", "rating": "2820", "category": "Top Players"}
    topPlayers_DingLiren = {"name": "Ding Liren", "rating": "2788", "category": "Top Players"}
    topPlayers_Fabiano = {"name": "Fabiano", "rating": "2840", "category": "Top Players"}
    topPlayers_Kosteniuk = {"name": "Kosteniuk", "rating": "2561", "category": "Top Players"}
    topPlayers_Danya = {"name": "Danya", "rating": "2650", "category": "Top Players"} #tick
    topPlayers_Ian = {"name": "Ian", "rating": "2795", "category": "Top Players"}
    topPlayers_Aronian = {"name": "Aronian", "rating": "2830", "category": "Top Players"}
    topPlayers_PaulMorphy = {"name": "Paul Morphy", "rating": "2600", "category": "Top Players"}
    topPlayers_JuditPolgar = {"name": "Judit Polgar", "rating": "2735", "category": "Top Players"} #tick
    topPlayers_Vidit = {"name": "Vidit", "rating": "2730", "category": "Top Players"}
    topPlayers_IrinaKrush = {"name": "Irina Krush", "rating": "2502", "category": "Top Players"}
    topPlayers_Giri = {"name": "Giri", "rating": "2800", "category": "Top Players"}
    topPlayers_Abdusattorov = {"name": "Abdusattorov", "rating": "2660", "category": "Top Players"}
    topPlayers_Lasker = {"name": "Lasker", "rating": "2640", "category": "Top Players"}
    topPlayers_HouYifan = {"name": "Hou Yifan", "rating": "2686", "category": "Top Players"}
    topPlayers_Bok = {"name": "Bok", "rating": "2650", "category": "Top Players"}
    topPlayers_WesleySo = {"name": "Wesley So", "rating": "2820", "category": "Top Players"}
    topPlayers_Tal = {"name": "Tal", "rating": "2705", "category": "Top Players"}
    topPlayers_Capablanca = {"name": "Capablanca", "rating": "2725", "category": "Top Players"}
    topPlayers_Magnus = {"name": "Magnus", "rating": "2882", "category": "Top Players"} #tick

class personalities(Enum):
    #13
    personalities_Danny = {"name": "Danny", "rating": "2500", "category": "Personalities"} #tick
    personalities_Agadmator = {"name": "Agadmator", "rating": "2000", "category": "Personalities"}
    personalities_Robert = {"name": "Robert", "rating": "2600", "category": "Personalities"}
    personalities_Maurice = {"name": "Maurice", "rating": "2550", "category": "Personalities"}
    personalities_Kevin = {"name": "Kevin", "rating": "2300", "category": "Personalities"}
    personalities_BenFinegold = {"name": "Ben Finegold", "rating": "2563", "category": "Personalities"} #tick
    personalities_Luison = {"name": "Luison", "rating": "2250", "category": "Personalities"}
    personalities_Krikor = {"name": "Krikor", "rating": "2550", "category": "Personalities"}
    personalities_FunMasterMike = {"name": "FunMasterMike", "rating": "2300", "category": "Personalities"}
    personalities_Pandolfini = {"name": "Pandolfini", "rating": "2250", "category": "Personalities"}
    personalities_PiaCramling = {"name": "Pia Cramling", "rating": "2250", "category": "Personalities"}
    personalities_Phiona = {"name": "Phiona", "rating": "1700", "category": "Personalities"}
    personalities_Dawid = {"name": "Dawid", "rating": "2400", "category": "Personalities"}

class engine(Enum):
    engine_level1_Rating250 = {"name": "Level 1", "rating": "250", "category": "Engine", "level": 1}
    engine_level2_Rating400 = {"name": "Level 2", "rating": "400", "category": "Engine", "level": 2}
    engine_level3_Rating550 = {"name": "Level 3", "rating": "550", "category": "Engine", "level": 3}
    engine_level4_Rating700 = {"name": "Level 4", "rating": "700", "category": "Engine", "level": 4}
    engine_level5_Rating850 = {"name": "Level 5", "rating": "850", "category": "Engine", "level": 5}
    engine_level6_Rating1000 = {"name": "Level 6", "rating":"1000","category": "Engine", "level": 6}
    engine_level7_Rating1100 = {"name": "Level 7", "rating":"1100","category": "Engine", "level": 7}
    engine_level8_Rating1200 = {"name": "Level 8", "rating": "1200", "category": "Engine", "level": 8}
    engine_level9_Rating1300 = {"name": "Level 9", "rating": "1300", "category": "Engine", "level": 9}
    engine_level10_Rating1400 = {"name": "Level 10", "rating": "1400", "category": "Engine", "level": 10}
    engine_level11_Rating1500 = {"name": "Level 11", "rating": "1500", "category": "Engine", "level": 11}
    engine_level12_Rating1600 = {"name": "Level 12", "rating": "1600", "category": "Engine", "level": 12}
    engine_level13_Rating1700 = {"name": "Level 13", "rating": "1700", "category": "Engine", "level": 13}
    engine_level14_Rating1800 = {"name": "Level 14", "rating": "1800", "category": "Engine", "level": 14}
    engine_level15_Rating1900 = {"name": "Level 15", "rating": "1900", "category": "Engine", "level": 15}
    engine_level16_Rating2000 = {"name": "Level 16", "rating": "2000", "category": "Engine", "level": 16}
    engine_level17_Rating2100 = {"name": "Level 17", "rating": "2100", "category": "Engine", "level": 17}
    engine_level18_Rating2200 = {"name": "Level 18", "rating": "2200", "category": "Engine", "level": 18}
    engine_level19_Rating2300 = {"name": "Level 19", "rating": "2300", "category": "Engine", "level": 19}
    engine_level20_Rating2400 = {"name": "Level 20", "rating": "2400", "category": "Engine", "level": 20}
    engine_level21_Rating2500 = {"name": "Level 21", "rating": "2500", "category": "Engine", "level": 21}
    engine_level22_Rating2600 = {"name": "Level 22", "rating": "2600", "category": "Engine", "level": 22}
    engine_level23_Rating2700 = {"name": "Level 23", "rating": "2700", "category": "Engine", "level": 23}
    engine_level24_Rating2900 = {"name": "Level 24", "rating": "2900", "category": "Engine", "level": 24}
    engine_level25_Rating3200 = {"name": "Level 25", "rating": "3200", "category": "Engine", "level": 25}

class timeControl(Enum):
    timeControl_1_0 = "1 min"
    timeControl_1_1 = "1 | 1"
    timeControl_2_1 = "2 | 1"
    timeControl_3_0 = "3 min"
    timeControl_3_2 = "3 | 2"
    timeControl_5_0 = "5 min"
    timeControl_10_0 = "10 min"
    timeControl_15_10 = "15 | 10"
    timeControl_30_0 = "30 min"
    timeControl_Custom = "custom"

class determinant(Enum):
    options_words = ["option", "options"]

    computer_mode_words = ["computer", "computers", "pvc", "bot", "bots"]

    online_mode_words = ["online", "player", "players", "pvp", "rank", "ranking"]

    puzzle_mode_words = ["puzzle", "puzzles"]

    resign_words = ["resign", "give up", "forfeit", "surrender"]

    quit_application_words = ["quit", "exit", "leave", "close", "shutdown"]

class timeControlDeterminant_Type(Enum):
    timeControl_1_0_words = dict.fromkeys(["1+0", "1 + 0", "1|0", "1 | 0", "1 min", "1min", "one minute", "1 minute", "1minute", "1 plus 0"], timeControl.timeControl_1_0.value)
    timeControl_1_1_words = dict.fromkeys(["1+1", "1 + 1", "1|1", "1 | 1", "one plus one", "1 plus 1", "one + one"], timeControl.timeControl_1_1.value)
    timeControl_2_1_words = dict.fromkeys(["2+1", "2 + 1", "2|1", "2 | 1", "two plus one", "2 plus 1", "two + one"], timeControl.timeControl_2_1.value)
    timeControl_3_0_words = dict.fromkeys(["3+0", "3 + 0", "3|0", "3 | 0", "3 min", "3min", "three minute", "3 minute", "3minute", "3 plus 0"], timeControl.timeControl_3_0.value)
    timeControl_3_2_words = dict.fromkeys(["3+2", "3 + 2", "3|2", "3 | 2", "three plus two", "3 plus 2", "three + two"], timeControl.timeControl_3_2.value)
    timeControl_5_0_words = dict.fromkeys(["5+0", "5 + 0", "5|0", "5 | 0", "5 min", "5min", "five minute", "5 minute", "5minute", "5 plus 0"], timeControl.timeControl_5_0.value)
    timeControl_10_0_words = dict.fromkeys(["10+0", "10 + 0", "10|0", "10 | 0", "10 min", "10min", "ten minute", "10 minute", "10minute", "10 plus 0"], timeControl.timeControl_10_0.value)
    timeControl_15_10_words = dict.fromkeys(["15+10", "15 + 10", "15|10", "15 | 10", "fifteen plus ten", "15 plus 10", "fifteen + ten"], timeControl.timeControl_15_10.value)
    timeControl_30_0_words = dict.fromkeys(["30+0", "30 + 0", "30|0", "30 | 0", "30 min", "30min", "thirty minute", "30 minute", "30minute", "30 plus 0", "default"], timeControl.timeControl_30_0.value)

class timeControlDeterminant_Speak(Enum):
    timeControl_1_0_words = dict.fromkeys(["1 + 0", "one minute", "1 minute", "1 plus 0"], timeControl.timeControl_1_0.value)
    timeControl_1_1_words = dict.fromkeys(["1 + 1", "one plus one", "1 plus 1"], timeControl.timeControl_1_1.value)
    timeControl_2_1_words = dict.fromkeys(["2 + 1", "two plus one", "2 plus 1"], timeControl.timeControl_2_1.value)
    timeControl_3_0_words = dict.fromkeys(["3 + 0", "three minutes", "3 minutes", "3 minute", "3 plus 0"], timeControl.timeControl_3_0.value)
    timeControl_3_2_words = dict.fromkeys(["3 + 2", "three plus two", "3 plus 2"], timeControl.timeControl_3_2.value)
    timeControl_5_0_words = dict.fromkeys(["5 + 0", "five minutes", "5 minutes", "5 minute", "5 plus 0"], timeControl.timeControl_5_0.value)
    timeControl_10_0_words = dict.fromkeys(["10 + 0", "ten minutes", "10 minutes", "10 plus 0", "10 minute"], timeControl.timeControl_10_0.value)
    timeControl_15_10_words = dict.fromkeys(["15 + 10", "fifteen plus ten", "15 plus 10"], timeControl.timeControl_15_10.value)
    timeControl_30_0_words = dict.fromkeys(["30 + 0", "thirty minutes", "30 minutes", "30 minute", "30 plus 0", "default"], timeControl.timeControl_30_0.value)

class response(Enum):
    greetings = "Hi! I am here to help you with any questions. You can ask me about how to use this software."
    howareyou = "I'm doing well, thank you for asking!"
    help = "You can navigate different options by pressing Tab key or Arrows. When entered in a chess game, there are 3 input mode. Press Ctrl F for the default keyboard base interface. <> " \
    "Ctrl J for Arrow mode that allow you to navagate through the board and move pieces by choosing target and destination grid using space bar." \
    "<> Ctrl S to activate voice input and press Ctrl S again to finish your input. <> You can ask for arrow mode and voice input for more information." \
    "There are also some shortcuts availble. You can ask me about the shortcuts if you are interested."
    arrow_mode = "Press Ctrl J while conducting a chess game to enter arrow mode. <> You can navigate the chessboard using arrow key and move chess piece by pressing spacebar to select source and destination grid."
    voice_input = "Press Ctrl S to activate Voice Input. Press Ctrl S again to finish Voice Input. You can select game mode by saying the game mode keyword you want to play. <> Computer for Computer Mode, Online for Online Player Mode, Puzzle for Puzzle Mode. <> You can also perform chess move by saying the UCI notation, which means the source grid and destination grid in order. For example, a sentence like 'move e2 to e4' indicates move the chess piece on e2 to e4. <> You can also resign by saying resign or surrender."
    shortcut = "Press Ctrl Q to activate chat bot. \n<> Ctrl O for avalible options. <> For game mode selection, Press Ctrl 1 for computer mode. <> Ctrl 2 for online player mode. <> Ctrl 3 for puzzle mode. <> For Game Review Mode, Press A to enter game review mode. Press B for best move. Left arrow for next chess move. Right arrow for previous chess move."

class chatbot_response(Enum):
    greetings = dict.fromkeys(["hi","hello", "nice to meet you"], response.greetings.value)
    howareyou = dict.fromkeys(["how are you", "I'm doing well, thank you for asking!"], response.howareyou.value)
    help = dict.fromkeys(["how to use", "tutorial", "tutor", "help"], response.help.value)
    arrow_mode = dict.fromkeys(["arrow", "arrows"], response.arrow_mode.value)
    voice_input = dict.fromkeys(["voice", "voices"], response.voice_input.value)
    shortcut = dict.fromkeys(["shortcut", "shortcuts"], response.shortcut.value)
    login = dict.fromkeys(["login", "log in", "sign in"], "Logging in now! Please enter your username now and press tab key to enter password.")
    start_computer_game = dict.fromkeys(["computer", "computers", "play with computer", "bot", "bots"], "Starting a computer game now!")
    start_player_game = dict.fromkeys(["online", "player", "players", "play with player"], "Starting an online player game now!")
    start = dict.fromkeys(["start", "new game","play"], "Which game mode would you like to play? Play with computer or player?")
    home = dict.fromkeys(["home", "main menu", "main"], "Returning to main menu now!")
    puzzle = dict.fromkeys(["puzzle", "puzzles"], "Starting a puzzle game now!")
