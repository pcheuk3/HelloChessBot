dismissOverlays = """
    (function dismissOverlays(){
        try {
            const closeSelectors = [
                '[aria-label="Close"]',
                'button[aria-label*="close" i]',
                'button[data-cy*="close" i]',
                '.modal-close',
                '.popup-close',
                '.overlay-close'
            ];

            for (const sel of closeSelectors) {
                const btn = document.querySelector(sel);
                if (btn && typeof btn.click === 'function') {
                    btn.click();
                }
            }

            const blockerSelectors = [
                '.modal-trial-modal',
                '.modal-upgrade-game-review-limit',
                '.cc-modal-component',
                '.modal-backdrop',
                '.overlay',
                '.popup'
            ];

            for (const sel of blockerSelectors) {
                document.querySelectorAll(sel).forEach((el) => {
                    if (el && el.parentNode) {
                        el.parentNode.removeChild(el);
                    }
                });
            }

            if (document.body) {
                document.body.style.overflow = 'auto';
            }
            if (document.documentElement) {
                document.documentElement.style.overflow = 'auto';
            }
        } catch (e) {
            // ignore overlay close errors
        }
        return true;
    })();
"""

getColor = """
    function getColor(){
        const anchor = document.querySelector('[x="10"][y="99"]');
        if(anchor && (anchor.textContent || '').toLowerCase() == 'a'){
            return "WHITE";
        }

        
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
        let moveList = document.querySelectorAll(".main-line-row");
        let opponent_move;
        let black_icon = "";
        if(moveList.length === 0) {
            return [null, ""];
        }
        let lastMove = moveList[moveList.length-1];
        let row_sig = (lastMove?.textContent || "").trim();
        let info = row_sig.split(/\s{2,}/).filter(Boolean);
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
        return [opponent_move, row_sig];
    }
    getOpponentMove();
    """

black_GetOpponentMove = """
    function getOpponentMove() {
        let moveList = document.querySelectorAll(".main-line-row");
        let opponent_move;
        let white_icon = "";
        if(moveList.length === 0) {
            return [null, ""];
        }
        let lastMove = moveList[moveList.length-1];
        let row_sig = (lastMove?.textContent || "").trim();
        let info = row_sig.split(/\s{2,}/).filter(Boolean);
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
        return [opponent_move, row_sig];  
    }
    getOpponentMove();
    """

checkGameEnd = """
    function checkGameEnd(mode){
        const textOf = (selectors) => {
            for (const s of selectors) {
                const el = document.querySelector(s);
                const txt = el && el.textContent ? el.textContent.trim() : "";
                if (txt) return txt;
            }
            return "";
        };

       
        const endText = textOf([
            '.modal-game-over-header-component',
            '.game-over-header-header',
            '[data-cy="game-over-header"]',
            '.game-over-modal-title',
            '[data-cy="game-over-modal"] [class*="header"]',
            '[data-cy="game-over-modal"] [class*="title"]'
        ]);
        if (endText) return endText;

       
        const gameOverContainer = document.querySelector('[data-cy="game-over-modal"], .game-over-modal-component, .modal-game-over-component');
        if (gameOverContainer) {
            const txt = (gameOverContainer.textContent || '').trim();
            if (txt) return txt;
            return true;
        }

       
        let moveList = document.querySelectorAll('.main-line-row');
        if(moveList.length > 0 && moveList[moveList.length-1].outerHTML.includes('result')){
            if(mode == 'computer'){
                return textOf(['.modal-game-over-header-component']) || true;
            }
            else{
                return textOf(['.game-over-header-header']) || true;
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
        let highlights = document.querySelectorAll(".highlight");
        if(!highlights || highlights.length < 2){
            return null;
        }

        function parse_square(el){
            if(!el){
                return null;
            }
            let class_text = el.getAttribute("class") || "";
            let tokens = class_text.split(/\s+/);
            let square_token = null;
            for(let i = 0; i < tokens.length; i++){
                if(/\d{2}/.test(tokens[i])){
                    square_token = tokens[i];
                    break;
                }
            }
            if(!square_token){
                return null;
            }
            let match = square_token.match(/\d+/);
            if(!match || !match[0] || match[0].length < 2){
                return null;
            }
            let raw = match[0];
            let file = position_transform_dictionary[raw[0]];
            let rank = raw[1];
            if(!file || !rank){
                return null;
            }
            return file + rank;
        }

        let pos1 = parse_square(highlights[0]);
        let pos2 = parse_square(highlights[1]);
        if(!pos1 || !pos2){
            return null;
        }
        return pos1 + pos2;
    }
    puzzle_mode_GetOpponentMove();
"""

clickNextPuzzle = """
    function clickNextPuzzle(){
        let target = document.querySelector('[aria-label="Next Puzzle"]');
        if(target && typeof target.click === "function"){
            target.click();
            return true;
        }
        return false;
    }
    clickNextPuzzle();
    """

clickTimeControlButton = """
    function clickTimeControlButton(timeControl, login, preferredSelector, startSelector){
        const MAX_TRIES = 10;
        const RETRY_MS = 500;

        const normalize = (s) => (s || '').replace(/\s+/g, ' ').trim().toLowerCase();

        const waitForSelector = (selectors, tries, onFound, onFailed) => {
            const list = Array.isArray(selectors) ? selectors : [selectors];
            for (const sel of list){
                const el = document.querySelector(sel);
                if (el) {
                    onFound(el);
                    return;
                }
            }
            if (tries <= 0){
                onFailed();
                return;
            }
            setTimeout(() => waitForSelector(list, tries - 1, onFound, onFailed), RETRY_MS);
        };

        const safeClick = (el) => {
            if (!el) return false;
            try {
                if (typeof el.scrollIntoView === 'function') {
                    el.scrollIntoView({ block: 'center', inline: 'center' });
                }
                el.dispatchEvent(new MouseEvent('mouseover', { bubbles: true }));
                el.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
                el.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
                if (typeof el.click === 'function') el.click();
                return true;
            } catch (_e) {
                return false;
            }
        };

        const openSelector = (done) => {
            const prefer = (preferredSelector && typeof preferredSelector === 'string') ? preferredSelector : '';
            const hasPreferred = (() => {
                try {
                    const m = prefer.match(/document\.querySelector\((.*)\)/);
                    if (m && m[1]) {
                        const css = Function('return ' + m[1])();
                        return !!document.querySelector(css);
                    }
                } catch (_e) {}
                return false;
            })();

            if (hasPreferred) {
                done();
                return;
            }

            if (findTimeButton()) {
                done();
                return;
            }

            waitForSelector(
                [
                    '.selector-button-button',
                    '[data-cy="time-control-selector"]',
                    '[data-cy="time-control-picker"]',
                    '.time-selector-field-component button',
                    '.time-selector-component button',
                    '[class*="time-control"] button'
                ],
                MAX_TRIES,
                (el) => {
                    safeClick(el);
                    setTimeout(done, 900);
                },
                done
            );
        };

        const findTimeButton = () => {
            if (preferredSelector && typeof preferredSelector === 'string') {
                try {
                    const m = preferredSelector.match(/document\.querySelector\((.*)\)/);
                    if (m && m[1]) {
                        const css = Function('return ' + m[1])();
                        const preferred = document.querySelector(css);
                        if (preferred) return preferred;
                    }
                } catch (_e) {}
            }

            const target = normalize(timeControl).replace('|', '+');
            const buttons = Array.from(document.querySelectorAll('button'));
            return buttons.find((button) => {
                const text = normalize(button?.textContent || '');
                return text === target
                    || text.includes(target)
                    || text === normalize(timeControl)
                    || text.includes(normalize(timeControl));
            }) || null;
        };

        const clickTimeWithRetry = (tries, done) => {
            const btn = findTimeButton();
            if (btn && safeClick(btn)) {
                setTimeout(() => {
                    const isSelected = btn.getAttribute('aria-pressed') === 'true'
                        || btn.classList.contains('selected')
                        || btn.getAttribute('data-selected') === 'true';
                    if (isSelected || findTimeButton() === btn) {
                        done(true);
                    } else if (tries > 0) {
                        setTimeout(() => clickTimeWithRetry(tries - 1, done), RETRY_MS);
                    } else {
                        done(false);
                    }
                }, 700);
                return;
            }

            if (tries <= 0){
                done(false);
                return;
            }
            setTimeout(() => clickTimeWithRetry(tries - 1, done), RETRY_MS);
        };

        const waitStartEnabledAndClick = (tries, done) => {
            const directStart = (startSelector && typeof startSelector === 'string')
                ? document.querySelector(startSelector)
                : null;

            const candidates = [
                directStart,
                document.querySelector('#board-layout-sidebar > div.sidebar-content > div.new-game-component > div.new-game-primary > button'),
                document.querySelector('.create-game-next-component .cc-button-primary'),
                document.querySelector('.create-game-component .cc-button-primary'),
                document.querySelector('[data-cy="create-game-next"]'),
                document.querySelector('[data-cy="new-game-index-play"]'),
                document.querySelector('[data-cy="challenge-button"]'),
                document.querySelector('button[data-cy*="play"]'),
            ].filter(Boolean);

            let startBtn = candidates.find((el) => !el.disabled) || null;

            if (!startBtn && directStart) {
                startBtn = directStart;
            }

            if (!startBtn) {
                const byText = Array.from(document.querySelectorAll('button')).find((btn) => {
                    const txt = normalize(btn?.textContent || '');
                    return !btn.disabled
                        && (txt.includes('play') || txt.includes('start') || txt.includes('create game') || txt.includes('對戰') || txt.includes('开始'));
                });
                if (byText) startBtn = byText;
            }

            if (startBtn) {
                try { startBtn.removeAttribute('disabled'); } catch (_e) {}
                const clicked = safeClick(startBtn);
                setTimeout(() => {
                    try { safeClick(startBtn); } catch (_e) {}
                }, 250);

                if (clicked) {
                    done(true);
                    return;
                }
            }

            if (tries <= 0){
                done(false);
                return;
            }
            setTimeout(() => waitStartEnabledAndClick(tries - 1, done), RETRY_MS);
        };

        const handlePostStart = () => {
            if(!login){
                waitForSelector(
                    ['#guest-button', '[data-cy="guest-button"]'],
                    MAX_TRIES,
                    (el) => safeClick(el),
                    () => null
                );
            } else {
                waitForSelector(
                    ['.fair-play-button', '[data-cy="fair-play-accept"]'],
                    MAX_TRIES,
                    (el) => safeClick(el),
                    () => null
                );
            }
        };

        openSelector(() => {
            clickTimeWithRetry(MAX_TRIES, (timePicked) => {
                if (!timePicked) {
                    window.__neoOnlineSetupStatus = 'time_not_selected';
                    return;
                }

                waitStartEnabledAndClick(MAX_TRIES, (started) => {
                    if (!started) {
                        window.__neoOnlineSetupStatus = 'start_not_ready';
                        return;
                    }
                    window.__neoOnlineSetupStatus = 'start_clicked';
                    setTimeout(handlePostStart, 900);
                });
            });
        });

        return true;
    }
"""

onlineGameReady = """
    function onlineGameReady(){
        const clocks = document.querySelectorAll('.clock-time-monospace, .clock-time');
        const hasBoard = document.querySelector('.board, wc-chess-board, [data-cy="game-board"]') != null;
        const hasMoveList = document.querySelector('[data-cy="move-list"]') != null
            || document.querySelector('.move-list-component') != null
            || document.querySelector('[data-cy="move-list-item"]') != null;
        const hasTurnClock = document.querySelector('.clock-player-turn, [data-cy="clock-player-turn"]') != null;
        return (clocks.length >= 2) && hasBoard && hasMoveList && hasTurnClock;
    }
    onlineGameReady();
"""

clickShare = """
    function clickShare(){
        const safeClick = (el) => {
            if (el && typeof el.click === 'function') {
                el.click();
                return true;
            }
            return false;
        };

        return (
            safeClick(document.querySelector('[aria-label="Share"]'))
            || safeClick(document.querySelector('[data-cy="share-button"]'))
            || safeClick(document.querySelector('button[aria-haspopup="dialog"]'))
            || false
        );
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

        let logoutFound = false;
        
 
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
  
            userMenuTriggers[0].click();
      
            setTimeout(() => {
      
                let logoutButtons = Array.from(document.querySelectorAll('button, a, [role="menuitem"], [role="button"]')).filter(btn => {
                    let text = (btn.textContent || btn.innerText || '').trim().toLowerCase();
                    let href = btn.getAttribute('href') || '';
                    return text.includes('sign out') || text.includes('log out') || text.includes('logout') || 
                           text.includes('登出') || href.includes('/logout');
                });
                
                if(logoutButtons.length > 0){
                    logoutButtons[0].click();
                } else {
           
                    window.location.href = 'https://www.chess.com/logout';
                }
            }, 800);
            logoutFound = true;
        } else {
      
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
        // Use the provided board selector first
        const boardSelectors = [
                '#board > div',
                '.board',
                '[data-cy="board"]',
                '.board-layout-board',
                '.board-view',
                '.board-replay-component',
            ];

        let board = null;
        for (const sel of boardSelectors) {
            board = document.querySelector(sel);
            if (board) break;
        }

        if (!board) {
            // fallback: try to find element that contains pieces
            const piece = document.querySelector('.piece');
            if (piece) {
                board = piece.parentElement;
            }
        }

        if (!board) {
            return null;
        }

        const rect = board.getBoundingClientRect();
        // compute square size as average of width/height divided by 8
        const squareW = rect.width / 8.0;
        const squareH = rect.height / 8.0;
        const square = Math.min(squareW, squareH);

        // return left (x), top (y), square size, plus full rect for debug if needed
        return [rect.left, rect.top, square, rect.width, rect.height, rect.right, rect.bottom];
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
        let target = document.querySelector('[aria-label="Retry"]');
        if(target && typeof target.click === "function"){
            target.click();
            return true;
        }
        return false;
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
            setTimeout(() => {
                document?.querySelector('.bot-selection-cta-button-button')?.click();
            }, 300);
        }
        else{
            let bot_list = document.querySelectorAll('.bot-group-accordion-component');
            for(bot of bot_list){
                bot.querySelector('.bot-group-accordion-toggleClickArea')?.click();
            }
            setTimeout(() => {
                document?.querySelector(search)?.click();
                document?.querySelector('.bot-selection-cta-button-button')?.click();
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
                bot.querySelector('.bot-group-accordion-toggleClickArea')?.click();
            }
            setTimeout(() => {
                slider = document?.querySelector('[aria-label="Slider"]');
                if(!slider){
                    return false;
                }
                slider.value = level;
                slider.dispatchEvent(new Event('input', { bubbles: true }));
                setTimeout(() => {
                    document?.querySelector('.bot-selection-cta-button-button')?.click();
                }, 500);
            }, 300);
        }
        else{
            slider.value = level;
            slider.dispatchEvent(new Event('input', { bubbles: true }));
            setTimeout(() => {
                document?.querySelector('.bot-selection-cta-button-button')?.click();
            }, 500);
        }
    }
"""

check_bot_locked = """
    function check_bot_locked(){
        const modal = document?.querySelector('.modal-trial-modal, .cc-modal-component, [role="dialog"]');
        if(!modal){
            return { locked: false, type: "none", message: "" };
        }

        const rawText = (modal.textContent || "").trim().toLowerCase();
        let type = "vip";
        if (
            rawText.includes("login") || rawText.includes("log in") || rawText.includes("sign in") ||
            rawText.includes("登入") || rawText.includes("登录")
        ){
            type = "login";
        }
        else if (
            rawText.includes("premium") || rawText.includes("membership") || rawText.includes("upgrade") ||
            rawText.includes("會員") || rawText.includes("会员") || rawText.includes("升級") || rawText.includes("升级")
        ){
            type = "vip";
        }

        const closeBtn =
            modal.querySelector('[aria-label="Close"]') ||
            modal.querySelector('button[aria-label*="close" i]') ||
            modal.querySelector('.modal-close, .popup-close, .overlay-close');

        if(closeBtn && typeof closeBtn.click === 'function'){
            closeBtn.click();
        }

        return {
            locked: true,
            type: type,
            message: rawText.slice(0, 180)
        };
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
