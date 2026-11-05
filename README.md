# PyAlphaBeta — շախմատային շարժիչ Python-ով

Պարզ, բայց իրական շախմատային շարժիչ՝ UCI արձանագրությամբ, որը կարելի է միացնել GUI-ների և Lichess-ին։

## Ինչ կա ներսում
- **Գնահատում** (`evaluate.py`)՝ նյութ + piece-square աղյուսակներ + փղերի զույգ + թագավորի փուլային աղյուսակ
- **Որոնում** (`search.py`)՝ negamax + alpha-beta, iterative deepening, quiescence search, transposition table, null-move pruning, check extension, killer/history + MVV-LVA քայլերի դասավորում
- **UCI** (`uci.py`)՝ `position`, `go` (wtime/btime/movetime/depth/infinite), `stop`
- **Խաղ տերմինալում** (`play.py`)
- Քայլերի գեներացիան և տախտակը տրամադրում է `python-chess` գրադարանը

## Տեղադրում
```bash
pip install -r requirements.txt
python -m unittest discover tests     # թեստեր
python play.py 3                      # խաղալ շարժիչի դեմ (3 վրկ քայլի համար)
```

## Օգտագործում GUI-ում (Arena, Cute Chess, Banksia)
Որպես շարժիչ ընտրիր `run_engine.sh` (Linux/macOS) կամ `python uci.py` (Windows)։

## Lichess բոտ
1. Ստեղծիր նոր Lichess հաշիվ, որով դեռ խաղ չես խաղացել։
2. Ստեղծիր API token՝ **Read incoming challenges**, **Play games with the bot API** իրավունքներով։
3. Փոխարկիր հաշիվը բոտի՝ `curl -d '' https://lichess.org/api/bot/account/upgrade -H "Authorization: Bearer <TOKEN>"`
4. Clone արա [lichess-bot](https://github.com/lichess-bot-devs/lichess-bot), պատճենիր `config.yml.default` → `config.yml` և լրացրու `lichess_config_snippet.yml`-ի արժեքներով (token, engine dir)։
5. `pip install -r requirements.txt` և `python3 lichess-bot.py`

## Հաջորդ քայլերը
- Perft թեստեր և սեփական քայլերի գեներատոր
- Late move reduction, aspiration windows, opening book
- Շարժիչի Elo-ի չափում Cute Chess-ով Stockfish-ի թույլ մակարդակների դեմ
- Վերագրում Rust-ով՝ 1000+ Elo ավելի ուժ
