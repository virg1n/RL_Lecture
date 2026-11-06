import json
import uuid

# Pretty pictures for the snake games. You do not need to read this file:
# it records a game and shows it as an animation with a play button, or lets you play in the browser.
#
#   python snake_viz.py                       replay random games of the simple snake in the browser
#   python snake_viz.py competitive           the same for the competitive snake
#   python snake_viz.py --play                play the simple snake: w = straight, a = left, d = right (one key = one move)
#   python snake_viz.py competitive --play    play the competitive snake


def record_episode(game, choose_action, max_steps=300):
    """Play one game with choose_action(game) -> 0/1/2 and return the list of frames."""
    frames = [game.frame()]
    for _ in range(max_steps):
        ate, died = game.step(choose_action(game))
        frame = game.frame()
        if died:
            frame["dead"] = True            # the last frame gets a crash mark
            frames.append(frame)
            break
        frames.append(frame)
    return frames


_PLAYER_JS = """
(function () {
  const root = document.getElementById("__ID__");
  const episodes = __DATA__;
  const CELL = __CELL__;
  const LIVE = __LIVE__;                                  // live: a Python server plays the game, one key = one move
  let fps = __FPS__, t = 0, timer = null, busy = false;
  const longest = Math.max(...episodes.map(e => e.frames.length));
  const canvases = [], infos = [];

  episodes.forEach((e, i) => {
    const box = document.createElement("div");
    box.style.cssText = "text-align:center;";
    const title = document.createElement("div");
    title.style.cssText = "font-weight:600;margin-bottom:4px;";
    title.textContent = e.title;
    const size = e.frames[0].size;
    const cv = document.createElement("canvas");
    cv.width = cv.height = size * CELL;
    cv.style.cssText = "border-radius:8px;box-shadow:0 1px 4px rgba(0,0,0,.35);";
    const info = document.createElement("div");
    info.style.cssText = "margin-top:4px;font-size:13px;";
    box.append(title, cv, info);
    root.querySelector(".sv-boards").appendChild(box);
    canvases.push(cv); infos.push(info);
  });

  function cellBox(ctx, x, y, pad, color, radius) {
    ctx.fillStyle = color;
    ctx.beginPath();
    if (ctx.roundRect) ctx.roundRect(x * CELL + pad, y * CELL + pad, CELL - 2 * pad, CELL - 2 * pad, radius);
    else ctx.rect(x * CELL + pad, y * CELL + pad, CELL - 2 * pad, CELL - 2 * pad);
    ctx.fill();
  }

  function drawSnake(ctx, cells, bodyColor, headColor) {
    for (let k = cells.length - 1; k >= 0; k--) {
      cellBox(ctx, cells[k][0], cells[k][1], 1.5, k === 0 ? headColor : bodyColor, 5);
    }
    if (cells.length > 1) {                               // eyes
      const h = cells[0], n = cells[1];
      const dx = h[0] - n[0], dy = h[1] - n[1];
      const cx = (h[0] + 0.5) * CELL + dx * CELL * 0.15, cy = (h[1] + 0.5) * CELL + dy * CELL * 0.15;
      ctx.fillStyle = "#fff";
      const eyes = (dx !== 0) ? [[cx, cy - CELL * 0.2], [cx, cy + CELL * 0.2]] : [[cx - CELL * 0.2, cy], [cx + CELL * 0.2, cy]];
      eyes.forEach(p => { ctx.beginPath(); ctx.arc(p[0], p[1], CELL * 0.1, 0, 7); ctx.fill(); });
    }
  }

  function draw(i, f, last) {
    const ctx = canvases[i].getContext("2d");
    const size = f.size;
    for (let x = 0; x < size; x++) for (let y = 0; y < size; y++) {
      ctx.fillStyle = (x + y) % 2 ? "#cfe8b0" : "#c2de9f";
      ctx.fillRect(x * CELL, y * CELL, CELL, CELL);
    }
    f.apples.forEach(a => {
      ctx.fillStyle = "#e53935";
      ctx.beginPath(); ctx.arc((a[0] + 0.5) * CELL, (a[1] + 0.5) * CELL, CELL * 0.36, 0, 7); ctx.fill();
      ctx.fillStyle = "#43a047";
      ctx.fillRect((a[0] + 0.5) * CELL - 1, a[1] * CELL + 2, 2, CELL * 0.2);
    });
    if (f.rival.length) drawSnake(ctx, f.rival, "#ff9800", "#e65100");
    drawSnake(ctx, f.snake, "#42a5f5", "#1565c0");
    if (last && f.dead) {
      ctx.fillStyle = "rgba(229,57,53,0.30)"; ctx.fillRect(0, 0, size * CELL, size * CELL);
      ctx.fillStyle = "#b71c1c"; ctx.font = "bold " + (CELL * 1.2) + "px sans-serif"; ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillText("CRASH", size * CELL / 2, size * CELL / 2);
    }
    infos[i].textContent = "apples: " + f.score + "   step: " + Math.min(t, e_len(i) - 1) + (last ? (f.dead ? "   (crashed)" : "   (time is up)") : "");
    if (LIVE && last) infos[i].textContent += "   press r to restart";
  }
  function e_len(i) { return episodes[i].frames.length; }

  function render() {
    episodes.forEach((e, i) => {
      const idx = Math.min(t, e.frames.length - 1);
      const f = e.frames[idx];
      draw(i, f, LIVE ? Boolean(f.dead || f.over) : t >= e.frames.length - 1);
    });
  }
  function play() {
    if (timer) return;
    if (t >= longest - 1) t = 0;
    timer = setInterval(() => {
      if (t < longest - 1) { t++; render(); } else { pause(); }
    }, 1000 / fps);
    btn.textContent = "pause";
  }
  function pause() { clearInterval(timer); timer = null; btn.textContent = "play"; }

  const btn = root.querySelector(".sv-play");
  if (LIVE) {
    // w / arrow up = straight, a / arrow left = left, d / arrow right = right, r = new game
    const KEYS = {w: 0, ArrowUp: 0, a: 1, ArrowLeft: 1, d: 2, ArrowRight: 2};
    const frames = episodes[0].frames;
    document.addEventListener("keydown", async ev => {
      const action = KEYS[ev.key];
      const last = frames[frames.length - 1];
      if (busy || (action === undefined && ev.key !== "r")) return;
      if (ev.key === "r") {
        busy = true;
        const first = await (await fetch("/reset")).json();
        frames.length = 0; frames.push(first); t = 0;
      } else {
        if (last.dead || last.over) return;
        busy = true;
        frames.push(await (await fetch("/step?a=" + action)).json());
        t = frames.length - 1;
      }
      busy = false;
      render();
    });
  } else {
    btn.onclick = () => timer ? pause() : play();
    root.querySelector(".sv-restart").onclick = () => { pause(); t = 0; render(); play(); };
    root.querySelector(".sv-speed").oninput = ev => {
      fps = +ev.target.value;
      if (timer) { pause(); play(); }
    };
  }
  render();
  if (__AUTOPLAY__) play();
})();
"""


def html_player(*episodes, titles=None, cell=24, fps=8, autoplay=False, live=False):
    """HTML (with JavaScript) that shows recorded games side by side with play / pause / speed controls.

    live=True: a single board driven by the keys w / a / d (see play_in_browser)."""
    titles = titles or ["game %d" % (i + 1) for i in range(len(episodes))]
    data = [{"title": t, "frames": frames} for t, frames in zip(titles, episodes)]
    uid = "sv" + uuid.uuid4().hex[:8]
    script = (_PLAYER_JS.replace("__ID__", uid).replace("__DATA__", json.dumps(data))
              .replace("__CELL__", str(cell)).replace("__FPS__", str(fps))
              .replace("__AUTOPLAY__", "true" if autoplay else "false")
              .replace("__LIVE__", "true" if live else "false"))
    controls = """
      <div style="margin-top:10px;display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
        <button class="sv-play" style="padding:4px 12px;cursor:pointer;">play</button>
        <button class="sv-restart" style="padding:4px 12px;cursor:pointer;">restart</button>
        <span>speed</span><input class="sv-speed" type="range" min="1" max="40" value="%d">
      </div>""" % fps
    if live:
        controls = """
      <div style="margin-top:10px;"><button class="sv-play" style="display:none;"></button>
        w = straight, a = left, d = right (arrow keys work too). One key = one move. r = new game.</div>"""
    return """
    <div id="%s" style="font-family:sans-serif;">
      <div class="sv-boards" style="display:flex;flex-wrap:wrap;gap:16px;"></div>%s
    </div>
    <script>%s</script>
    """ % (uid, controls, script)


def play(*episodes, **options):
    """In a notebook: show recorded games. Same arguments as html_player."""
    from IPython.display import HTML, display
    display(HTML(html_player(*episodes, **options)))


def save_html(path, *episodes, **options):
    """Outside a notebook: write a web page with the animation."""
    with open(path, "w") as f:
        f.write("<!doctype html><meta charset='utf-8'><body>" + html_player(*episodes, **options))


def play_in_browser(new_game, cell=32):
    """Play in the browser: you press w / a / d and each key makes exactly one move.

    The game itself runs here in Python; the page only draws it and sends your keys to this program."""
    import http.server
    import webbrowser

    state = {"game": new_game()}

    def current_frame(game, died=False):
        frame = game.frame()
        frame["dead"] = died
        frame["over"] = hasattr(game, "max_steps") and game.steps >= game.max_steps
        return frame

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            path, _, query = self.path.partition("?")
            if path == "/":
                state["game"] = new_game()
                body = ("<!doctype html><meta charset='utf-8'><title>snake</title><body>"
                        + html_player([current_frame(state["game"])], titles=["you"], cell=cell, live=True))
                kind = "text/html"
            elif path == "/reset":
                state["game"] = new_game()
                body, kind = json.dumps(current_frame(state["game"])), "application/json"
            elif path == "/step" and query in ("a=0", "a=1", "a=2"):
                ate, died = state["game"].step(int(query[-1]))
                body, kind = json.dumps(current_frame(state["game"], died)), "application/json"
            else:
                self.send_error(404)
                return
            data = body.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", kind + "; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *args):         # keep the terminal quiet
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)      # only this computer can connect
    url = "http://127.0.0.1:%d/" % server.server_port
    print("play at", url, "  (Ctrl+C to stop)")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    import argparse
    import os
    import random
    import webbrowser

    parser = argparse.ArgumentParser(description="Show or play the snake games in the browser.")
    parser.add_argument("game", nargs="?", choices=["simple", "competitive"], default="simple")
    parser.add_argument("--play", action="store_true", help="play yourself with w / a / d, one key = one move")
    args = parser.parse_args()

    if args.game == "simple":
        from snake_game import SnakeGame as Game
    else:
        from competitive_snake import CompetitiveSnake as Game

    if args.play:
        play_in_browser(Game, cell=32 if args.game == "simple" else 28)
    else:
        games = [record_episode(Game(seed=s), lambda g: random.randint(0, 2)) for s in (1, 2, 3)]
        out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "snake.html")
        save_html(out, *games, titles=["random #1", "random #2", "random #3"], autoplay=True)
        print("wrote", out)
        webbrowser.open("file://" + out)
