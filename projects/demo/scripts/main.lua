-- Demo: two pages, a tween, a button, and a tiny game hook.
-- Edit and save this file while the engine is running to see it hot reload.

-- Game page
Page.Open("Game")
local player = UI.Frame(100, 400, 40, 40)
player.bg = "blue"
local back = UI.Button("Back", 20, 20, 120, 40)
back.on_click = function() Page.Open("Menu") end
UI.Text("Arrow keys to move", 20, 80, 20)

-- Menu page
Page.Open("Menu")
local title = UI.Text("Strife!", 400, -60, 48)
local play = UI.Button("Play", 360, 300, 240, 60)
play.on_click = function() Page.Open("Game") end
Tween(title, "y", 100, 0.6)

local speed = 300
function on_update(dt)
  if Input.key_down("right") then player.x = player.x + speed * dt end
  if Input.key_down("left")  then player.x = player.x - speed * dt end
  if Input.key_down("up")    then player.y = player.y - speed * dt end
  if Input.key_down("down")  then player.y = player.y + speed * dt end
end
