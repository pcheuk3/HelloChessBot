getColor = """
    function getColor(){
        const anchor = document.querySelector('[x="10"][y="99"]');
        if(anchor && (anchor.textContent || '').toLowerCase() == 'a'){
            return "WHITE";
        }

        // fallback: 若棋盤座標尚未渲染，先回傳 null 讓 Python 端重試
        const boardExists = document.querySelector('.board') || document.querySelector('[data-cy="board"]');
        if(!anchor && boardExists){
            return null;
        }

        return "BLACK";
    }
    getColor();
"""
    
white_GetOpponentMove = """
    function getOpponentMove() {
        let player_color = "WHITE";
        let moveList = document.querySelectorAll(".main-line-row");
        let opponent_move;
        let black_icon = "";
        if(moveList.length === 0) {
            return null;
        }
        let lastMove = moveList[moveList.length-1];
        let info = lastMove?.textContent.trim().split("   ");
        if(document?.querySelector('[data-move-list-el]')){
            info.splice(info.length-1, 1);
        }
        if(info.length!=3){
            opponent_move = null;
        }
        else{
            let chessIcon = lastMove.querySelectorAll(".icon-font-chess");
            if(chessIcon.length>0){
                if(chessIcon.length==1){
                    if(chessIcon[0].getAttribute("class").includes("black")){
                        black_icon = chessIcon[0].getAttribute("data-figurine");
                    }
                }
                else{
                    black_icon = chessIcon[1].getAttribute("data-figurine");
                }
            }
            opponent_move = black_icon + info[2].trim();
        }
        return opponent_move;
    }
    getOpponentMove();
    """

black_GetOpponentMove = """
    function getOpponentMove() {
        let player_color = "BLACK";
        let moveList = document.querySelectorAll(".main-line-row");
        let opponent_move;
        let white_icon = "";
        if(moveList.length === 0) {
            return null;
        }
        let lastMove = moveList[moveList.length-1];
        let info = lastMove?.textContent.trim().split("   ");
        if(document?.querySelector('[data-move-list-el]')){
            info.splice(info.length-1, 1);
        }
        if(info.length==3){
            opponent_move = null;    
        }
        else{
            let chessIcon = lastMove.querySelectorAll(".icon-font-chess")
            if(chessIcon.length>0){
                if(chessIcon.length==1){
                    if(chessIcon[0].getAttribute("class").includes("white")){
                        white_icon = chessIcon[0].getAttribute("data-figurine");
                    }
                }
                else{
                    white_icon = chessIcon[0].getAttribute("data-figurine");
                }
            }
        opponent_move = white_icon + info[1].trim();
        }
        return opponent_move;  
    }
    getOpponentMove();
    """

checkGameEnd = """
    function checkGameEnd(mode){
        let moveList = document.querySelectorAll(".main-line-row");
        if(moveList.length > 0 && moveList[moveList.length-1].outerHTML.includes("result")){
            if(mode == 'computer'){
                return document.querySelector('.modal-game-over-header-component').textContent.trim();
            }
            else{
                return document.querySelector('.game-over-header-header').textContent.trim();
            }
        }
        return false;
    }
"""

getFEN = """
    function getFEN(){
        let FEN = document?.getElementById("share-fen")?.value;
        if(FEN == null){
            return false;
        }
        document.querySelector('[aria-label="Close"]').click();
        return FEN;
    }
    getFEN();
"""

checkExistGame = """
    function checkExistGame() {
        let moveList = document.querySelectorAll(".main-line-row");
        if(moveList.length>0){
            let move = [];
            for(let i = 0; i<moveList.length; i++){
                let white_icon = "";
                let black_icon = "";
                let info = moveList[i].textContent.trim().split("   ");
                if(document?.querySelector('[data-move-list-el]')){
                    info.splice(info.length-1, 1);
                }
                let chessIcon = moveList[i].querySelectorAll(".icon-font-chess");
                if(info.length==2){
                    if(chessIcon.length>0){
                        white_icon = chessIcon[0].getAttribute("data-figurine");
                    }
                    move.push(white_icon + info[1].trim());
                }
                else{
                    if(chessIcon.length>0){
                        if(chessIcon.length==1){
                            if(chessIcon[0].getAttribute("class").includes("white")){
                                white_icon = chessIcon[0].getAttribute("data-figurine");
                            }
                            else{
                                black_icon = chessIcon[0].getAttribute("data-figurine");
                            }
                        }
                        else{
                            white_icon = chessIcon[0].getAttribute("data-figurine");
                            black_icon = chessIcon[1].getAttribute("data-figurine");
                        }                 
                    }
                    move.push(white_icon + info[1].trim());
                    move.push(black_icon + info[2].trim());
                }
            }
            return move;
        }
        return false;
    }
    checkExistGame();
    """
puzzle_mode_constructBoard = """
    function puzzle_mode_constructBoard(){
        notation_transform_dictionary = {
            "bq":"q",
            "bk":"k",
            "bn":"n",
            "bb":"b",
            "br":"r",
            "bp":"p",
            "wq":"Q",
            "wk":"K",
            "wn":"N",
            "wb":"B",
            "wr":"R",
            "wp":"P",
        }
        let pieces = document.querySelectorAll(".piece");
        let board_element = Array.from(Array(8), _ => Array(8).fill(0));
        for(let i=0; i<pieces.length; i++){
            let info = pieces[i].getAttribute("class");
            let location = info.match(/\d+/)[0];
            info = info.split(" ")
            let piece_type = notation_transform_dictionary[info[1]];
            if(piece_type==null){
                piece_type = notation_transform_dictionary[info[2]];
            }
            board_element[location[1]-1][location[0]-1] = piece_type;
        }
        return board_element;
    }
    puzzle_mode_constructBoard();
    """


puzzle_mode_GetTitle = """
    function puzzle_mode_GetTitle(){
        document?.querySelector('[aria-label="Close"]')?.click();
        document?.querySelector(".modal-first-time-button")?.getElementsByTagName('button')[0].click();
        let title = document?.querySelector(".section-heading-title")?.textContent?.split(' ')[0];
        if(title == null){
            title = document.querySelector(".cc-text-speech-bold").textContent.split(' ')[0]
        }
        return title;
    }
    puzzle_mode_GetTitle();
"""

puzzle_mode_GetOpponentMove = """
    function puzzle_mode_GetOpponentMove(){
        let position_transform_dictionary = {
            "1":"A",
            "2":"B",
            "3":"C",
            "4":"D",
            "5":"E",
            "6":"F",
            "7":"G",
            "8":"H",
        }
        let pos1 = document.querySelectorAll(".highlight")[0].getAttribute("class").split(' ')[1].match(/\d+/)[0];
        let pos2 = document.querySelectorAll(".highlight")[1].getAttribute("class").split(' ')[1].match(/\d+/)[0];
        pos1 = position_transform_dictionary[[pos1[0]]] + pos1[1];
        pos2 = position_transform_dictionary[pos2[0]] + pos2[1];
        return pos1 + pos2;
    }
    puzzle_mode_GetOpponentMove();
"""

clickNextPuzzle = """
    function clickNextPuzzle(){
        let target = document.querySelector('[aria-label="Next Puzzle"]');
        target.click();
    }
    clickNextPuzzle();
    """

clickTimeControlButton = """
    function clickTimeControlButton(timeControl, login){
        const safeClick = (el) => {
            if (el && typeof el.click === 'function') {
                el.click();
                return true;
            }
            return false;
        };

        const openSelector = () => {
            return safeClick(document.querySelector('.selector-button-button'))
                || safeClick(document.querySelector('[data-cy="time-control-selector"]'))
                || safeClick(document.querySelector('[class*="time-control"] button'));
        };

        const clickTimeButton = () => {
            let buttons = Array.from(document.querySelectorAll('button'));
            for (const button of buttons){
                if ((button?.textContent || '').trim().toLowerCase() === timeControl){
                    return safeClick(button);
                }
            }
            return false;
        };

        const clickPrimary = () => {
            return safeClick(document?.querySelector('.create-game-next-component .cc-button-primary'))
                || safeClick(document?.querySelector('.create-game-component .cc-button-primary'))
                || safeClick(document?.querySelector('[data-cy="create-game-next"]'));
        };

        openSelector();

        setTimeout(() => {
            clickTimeButton();

            setTimeout(() => {
                clickPrimary();

                if(!login){
                    setTimeout(() => {
                        safeClick(document.getElementById('guest-button'))
                        || safeClick(document.querySelector('[data-cy="guest-button"]'));
                    }, 1500);
                }
                else{
                    setTimeout(() => {
                        safeClick(document.querySelector('.fair-play-button'))
                        || safeClick(document.querySelector('[data-cy="fair-play-accept"]'));
                    }, 1000);
                }
            }, 1500)
        }, 500);
    }
"""

onlineGameReady = """
    function onlineGameReady(){
        const clocks = document.querySelectorAll('.clock-time-monospace');
        const hasBoard = document.querySelector('.board') != null;
        const hasMoveList = document.querySelector('[data-cy="move-list"]') != null || document.querySelector('.move-list-component') != null;
        const hasTurnClock = document.querySelector('.clock-player-turn') != null;
        return (clocks.length >= 2) && hasBoard && hasMoveList && hasTurnClock;
    }
    onlineGameReady();
"""

clickShare = """
    function clickShare(){
        document.querySelector('[aria-label="Share"]').click();
        return false;
    }
    clickShare();
"""

clickPGN = """
    function clickPGN(){
        if(document?.querySelector('.share-menu-tab-selector-tab') == null){
            return false;
        }
        document.querySelector('.share-menu-tab-selector-tab').click();
        return true;
    }
    clickPGN();
"""

checkMoveSuccess = """
    function checkMoveSuccess(targetSrc){
        pieces = document.querySelectorAll(".piece")
        for(piece of pieces){
            if(piece.getAttribute("class").includes("square-"+ targetSrc)){
                return false;
            }
        }
        return true;
    }
"""

clickGameReview = """
    function clickGameReview(){
        for(let i of document?.querySelectorAll('button')){
            console.log(i.textContent.trim().toLowerCase())
            if(i.textContent.trim().toLowerCase() == "game review"){
                i.click();
                return true;
            }
        }
        return false;
    }
    clickGameReview();
"""

getGameId = """
    function getGameId(){
        return document.URL.match(/\d+/)[0] //game id
    }
    getGameId();
"""

clickStartReview = """
    function clickStartReview(){
        if(document.querySelector('.cc-button-primary') == null){
            return null;
        }
        let overview = document.querySelector(".bot-speech-content-content-container").textContent;
        document.querySelector('.cc-button-primary').click();
        setTimeout(() => {
            document.querySelector('[aria-label="First Move"]').click();            
        }, 300);
        return overview;
    }
    clickStartReview();
"""

checkReviewLimited = """
    function checkReviewLimited(){
        if(document.querySelector('.modal-upgrade-game-review-limit')){
            return true;
        }
        return false;
    }
    checkReviewLimited();
"""

getReviewComment = """
    function getReviewComment(){
        let selected = document.querySelector(".selected");
        if(selected != null){
            let icon = selected?.querySelector('.icon-font-chess')?.getAttribute('data-figurine');
            if(icon == null){
                icon = "";
            }
            let feedback = document.querySelector(".move-feedback-box-move").textContent.trim();
            if(!/\d/.test(feedback)){
                feedback = icon + selected.textContent.trim() + " is " + feedback;
            }
            else if(feedback.includes("=")){
                let index = feedback.indexOf("is");
                let lastSeq = feedback.substring(index, feedback.length);
                feedback = selected.textContent + lastSeq; 
            }
            else{
                feedback = icon + feedback;
            }
            let explain = document.querySelector('.move-feedback-box-row')?.textContent;
            let bestExist = false;
            if(document.querySelector('[data-glyph="tool-magnifier-star"]')){
                bestExist = true;
            }
            return [feedback, explain, bestExist];
        }
        return document.querySelector(".bot-speech-content-content-container").textContent.trim();
    }
    getReviewComment();
"""

analysis_GetBestMove = """
    function analysis_GetBestMove(){
        let buttons = document.querySelector('.flow-buttons-component').querySelectorAll('button');
        for(let i = 0; i < buttons.length; i++){
            if(buttons[i].textContent.trim().toLowerCase() == 'best'){
                buttons[i].click();
                break;
            }
        }
    }
    analysis_GetBestMove();
"""

analysis_GetMoveLength = """
    function analysis_GetMoveLength(){
        return document.querySelectorAll('.main-line-ply').length;
    }
    analysis_GetMoveLength();
"""

userLogin = """
    function userLogin(username, password){
        let usernameField = document.getElementById('login-username');
        usernameField.value = username;
        usernameField.dispatchEvent(new Event('input', { bubbles: true }));
        usernameField.dispatchEvent(new Event('change', { bubbles: true }));
        
        let passwordField = document.getElementById('login-password');
        passwordField.value = password;
        passwordField.dispatchEvent(new Event('input', { bubbles: true }));
        passwordField.dispatchEvent(new Event('change', { bubbles: true }));
        
        if(!document.getElementById('_remember_me').checked){
            document.getElementById('_remember_me').click();
        }
        setTimeout(document.querySelector('[name="login"]').click(), 500);
    }
"""

loginSuccess = """
    function loginSuccess(){
        // 更严格地判断是否登录成功：
        // 1. 页面上出现仅登录后才存在的用户信息/用户菜单元素
        // 2. 同时登录按钮不再出现
        const loginButton = document.querySelector('[name="login"]');

        const loggedInSelectors = [
            '.home-user-info',
            '[data-testid="user-menu"]',
            '.user-info',
            '[class*="UserMenu"]',
            '[class*="user-menu"]'
        ];

        let hasUserInfo = false;
        for (const sel of loggedInSelectors) {
            const el = document.querySelector(sel);
            if (el && (el.innerText || el.textContent)) {
                const text = (el.innerText || el.textContent).trim();
                if (text.length > 0) {
                    hasUserInfo = true;
                    break;
                }
            }
        }

        if (hasUserInfo && loginButton == null) {
            return true;
        }
        return false;
    }
    loginSuccess();
"""

userLogout = """
    function userLogout(){
        // 查找并点击登出按钮
        // Chess.com 的登出按钮通常在用户菜单中
        let logoutFound = false;
        
        // 方法1: 先尝试查找用户菜单按钮（头像或用户名）
        let userMenuTriggers = [
            document.querySelector('[data-testid="user-menu"]'),
            document.querySelector('.user-menu'),
            document.querySelector('[aria-label*="user"]'),
            document.querySelector('[aria-label*="account"]'),
            document.querySelector('.user-avatar'),
            document.querySelector('.user-info'),
            document.querySelector('[class*="user-menu"]'),
            document.querySelector('[class*="user-avatar"]'),
            document.querySelector('[class*="UserMenu"]')
        ].filter(el => el !== null);
        
        if(userMenuTriggers.length > 0){
            // 点击用户菜单打开下拉菜单
            userMenuTriggers[0].click();
            // 等待菜单打开后查找登出按钮
            setTimeout(() => {
                // 查找登出按钮
                let logoutButtons = Array.from(document.querySelectorAll('button, a, [role="menuitem"], [role="button"]')).filter(btn => {
                    let text = (btn.textContent || btn.innerText || '').trim().toLowerCase();
                    let href = btn.getAttribute('href') || '';
                    return text.includes('sign out') || text.includes('log out') || text.includes('logout') || 
                           text.includes('登出') || href.includes('/logout');
                });
                
                if(logoutButtons.length > 0){
                    logoutButtons[0].click();
                } else {
                    // 如果没找到，尝试直接访问登出 URL
                    window.location.href = 'https://www.chess.com/logout';
                }
            }, 800);
            logoutFound = true;
        } else {
            // 方法2: 如果找不到用户菜单，直接查找页面上的登出按钮
            let logoutButtons = Array.from(document.querySelectorAll('button, a')).filter(btn => {
                let text = (btn.textContent || btn.innerText || '').trim().toLowerCase();
                let href = btn.getAttribute('href') || '';
                return text.includes('sign out') || text.includes('log out') || text.includes('logout') || 
                       text.includes('登出') || href.includes('/logout');
            });
            
            if(logoutButtons.length > 0){
                logoutButtons[0].click();
                logoutFound = true;
            } else {
                // 方法3: 直接访问登出 URL
                window.location.href = 'https://www.chess.com/logout';
                logoutFound = true;
            }
        }
        
        return logoutFound;
    }
    userLogout();
"""

analysis_NextMove = """
    function analysis_NextMove(){
        document.querySelector('[aria-label="Next Move"]').click()
    }
    analysis_NextMove();
"""

analysis_PreviousMove = """
    function analysis_PreviousMove(){
        document.querySelector('[aria-label="Previous Move"]').click()
    }
    analysis_PreviousMove();
"""

analysis_FirstMove = """
    function analysis_FirstMove(){
        document.querySelector('[aria-label="First Move"]').click()
    }
    analysis_FirstMove();
"""    

analysis_LastMove = """
    function analysis_LastMove(){
        document.querySelector('[aria-label="Last Move"]').click()
    }
    analysis_LastMove();
"""

getBoard = """
    function getBoard(){
        let bottom_number = document.querySelector('[x="0.75"][y="90.75"]').getBoundingClientRect();
        let left_alphabet = document.querySelector('[x="10"][y="99"]').getBoundingClientRect();
        let right_alphabet = document.querySelector('[x="22.5"][y="99"]').getBoundingClientRect();
        let distance = right_alphabet['x'] - left_alphabet['x'];
        let mid_x = (bottom_number['x'] + left_alphabet['x']) *0.5;
        let mid_y = (bottom_number['y'] + left_alphabet['y']) *0.5;
        return [mid_x, mid_y, distance];
    }
    getBoard();
"""

checkLogin = """
    function checkLogin(){
        return document.querySelector(".login");
    }
    checkLogin();
"""

getPiecesLocation = """
    function getPiecesLocation(){
        let num_to_alphabet = {
            "1": "a",
            "2": "b",
            "3": "c",
            "4": "d",
            "5": "e",
            "6": "f",
            "7": "g",
            "8": "h",  
        }
        let pieces = document.querySelectorAll(".piece");
        let white = "";
        let white_k = "";
        let white_q = "";
        let white_r = "";
        let white_b = "";
        let white_n = "";
        let white_p = "";
        let black = "";
        let black_k = "";
        let black_q = "";
        let black_r = "";
        let black_b = "";
        let black_n = "";
        let black_p = "";
        for(let i=0; i<pieces.length; i++){
            let info = pieces[i].getAttribute("class");
            let location = info.match(/\d+/)[0];
            let col = num_to_alphabet[location[0]];
            let row = location[1];
            info = info.split(" ");
            let piece_type = info[1];
            if(/\d+/.test(piece_type)){
                piece_type = info[2];
            }
            console.log(piece_type)
            switch(piece_type){
                case "bp":
                    if(black_p == ""){
                        black_p = "pawn: " + col + row + ", ";
                    }
                    else{
                        black_p += col + row + ", ";
                    }
                    break;

                case "wp":
                    if(white_p == ""){
                        white_p = "pawn: " + col + row + ", ";
                    }
                    else{
                        white_p += col + row + ", ";
                    }
                    break;
                    
                case "bk":
                    black_k = "king: " + col + row + ", ";
                    break;

                case "bq":
                    black_q = "queen: " + col + row + ", ";
                    break;

                case "bn":
                    if(black_n == ""){
                        black_n = "knight: " + col + row + ", ";
                    }
                    else{
                        black_n += col + row + ", ";
                    }
                    break;
                    
                case "bb":
                    if(black_b == ""){
                        black_b = "bishop: " + col + row + ", ";
                    }
                    else{
                        black_b += col + row + ", ";
                    }
                    break;
                    
                case "br":
                    if(black_r == ""){
                        black_r = "rook: " + col + row + ", ";
                    }
                    else{
                        black_r += col + row + ", ";
                    }
                    break;

                case "wk":
                    white_k = "king: " + col + row + ", ";
                    break;

                case "wq":
                    white_q = "queen: " + col + row + ", ";
                    break;

                case "wn":
                    if(white_n == ""){
                        white_n = "knight: " + col + row + ", ";
                    }
                    else{
                        white_n += col + row + ", ";
                    }
                    break;

                case "wb":
                    if(white_b == ""){
                        white_b = "bishop: " + col + row + ", ";
                    }
                    else{
                        white_b += col + row + ", ";
                    }
                    break;
                    
                case "wr":
                    if(white_r == ""){
                        white_r = "rook: " + col + row + ", ";
                    }
                    else{
                        white_r += col + row + ", ";
                    }
                    break;
            }
        }
            white = white_k + white_q + white_r + white_b + white_n + white_p;
            black = black_k + black_q + black_r + black_b + black_n + black_p;
            return [white, black];
    }
    getPiecesLocation();
"""

retryPuzzle = """
    function retryPuzzle(){
        document.querySelector('[aria-label="Retry"]').click();
    }
    retryPuzzle();
"""

open_bot_menu = """
    function open_bot_menu(){
        document?.querySelector('[aria-label="Close"]')?.click();
        let bot_list = document.querySelectorAll('.bot-group-accordion-component');
        for(bot of bot_list){
            bot.querySelector('.bot-group-accordion-toggleClickArea').click();
        }
    }
    open_bot_menu();
"""

select_bot = """
    function select_bot(bot_name){
        if(document?.querySelector('[aria-label="Close"]')){
            document?.querySelector('[aria-label="Close"]')?.click();
        }
        let search = '[data-bot-selection-name="' + bot_name + '"]';
        let bot = document?.querySelector(search)
        if(bot){
            bot.click();
            setTimeout(document.querySelector('.bot-selection-cta-button-button').click(), 300);
        }
        else{
            let bot_list = document.querySelectorAll('.bot-group-accordion-component');
            for(bot of bot_list){
                bot.querySelector('.bot-group-accordion-toggleClickArea').click();
            }
            setTimeout(() => {
                document?.querySelector(search).click();
                document.querySelector('.bot-selection-cta-button-button').click();
            }, 500);
        }
    }
"""

select_engine_level = """
    function select_engine_level(level){
        let slider = document?.querySelector('[aria-label="Slider"]');
        if(!slider){
            let bot_list = document.querySelectorAll('.bot-group-accordion-component');
            for(bot of bot_list){
                bot.querySelector('.bot-group-accordion-toggleClickArea').click();
            }
            setTimeout(() => {
                slider = document?.querySelector('[aria-label="Slider');
                slider.value = level;
                slider.dispatchEvent(new Event('input', { bubbles: true }));
                setTimeout(document.querySelector('.bot-selection-cta-button-button').click(), 500);
            }, 300);
        }
        else{
            slider.value = level;
            slider.dispatchEvent(new Event('input', { bubbles: true }));
            setTimeout(document.querySelector('.bot-selection-cta-button-button').click(), 500);
        }
    }
"""

check_bot_locked = """
    function check_bot_locked(){
        if(document?.querySelector(".modal-trial-modal")){
            return true;
        }
        return false;
    }
    check_bot_locked();
"""

bot_new_game = """
    function bot_new_game(){
        let buttons = Array.from(document?.querySelectorAll("button") || []);
        const targets = ["rematch", "new game", "play again", "再来一局", "再來一局", "新对局", "新對局"];

        for (const item of buttons){
            const txt = (item.textContent || "").trim().toLowerCase();
            if (targets.includes(txt)){
                item.click();
                return true;
            }
        }

        // fallback: 模糊匹配，避免文案微调导致失败
        for (const item of buttons){
            const txt = (item.textContent || "").trim().toLowerCase();
            if (txt.includes("rematch") || txt.includes("new game") || txt.includes("play again")){
                item.click();
                return true;
            }
        }
        return false;
    }
    bot_new_game();
"""

bot_request_takeback = """
    function bot_request_takeback(){
        // 嘗試尋找電腦對戰下方的悔棋 / takeback 按鈕
        let buttons = Array.from(document.querySelectorAll('button'));
        let candidates = buttons.filter(b => {
            let txt = (b.textContent || '').trim().toLowerCase();
            return txt.includes('takeback') || txt.includes('undo') || txt.includes('悔棋');
        });
        if (candidates.length > 0){
            candidates[0].click();
            return true;
        }
        return false;
    }
    bot_request_takeback();
"""

analysis_retry = """
    function analysis_retry(){
        buttons = document.querySelectorAll('button');
        for(i of buttons){
            if(i.textContent.trim() == "Retry"){
                i.click();
            }
        }
    }
    analysis_retry();
"""