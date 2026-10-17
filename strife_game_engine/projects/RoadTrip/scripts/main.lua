Page.Open("GameBD")
UI.Load("GameBD")

local bombBox = UI.Get("BombBox")
if not bombBox then
  error('Could not find "BombBox"; open the matching GameBD layout.')
end

local duration = 40
local elapsed = 0
local timer = duration
local launchX, launchY = 100, 259 -- Fixed at the center of the builder's launcher.
local targetPlane = 786
local graphScale = 50 -- One graph unit is 50 screen pixels on either axis.
local shotSpeed = 300 -- Horizontal screen pixels per second.
local projectileRadius = 4
local shot = {active = false, x = launchX, y = launchY, fn = nil}
local trail = {}
local lastTrailX, lastTrailY = launchX, launchY
local touched = {}
local touchedCount = 0
local won = false
local expired = false
local functionInput

-- The builder layout copy supplied with this script adds these IDs to only the
-- four colored targets and their glow frames. Their existing sizes/styles stay.
local colors = {"red", "yellow", "blue", "green"}
local targets, glows = {}, {}
for _, color in ipairs(colors) do
  targets[color] = UI.Get("Target" .. color:gsub("^%l", string.upper))
  glows[color] = UI.Get("Glow" .. color:gsub("^%l", string.upper))
  if not targets[color] or not glows[color] then
    error("Missing target/glow IDs in GameBD.json for color: " .. color)
  end
end

local title = UI.Text("Timer: " .. timer, 60, 13, 36)
title.color, title.z = "#ffffff", 4
local redTitle = UI.Text(title.text, 60, 13, 36)
redTitle.color, redTitle.alpha, redTitle.z = "#ff0000", 0, 5
local status = UI.Text("Enter a function through (0, 0), then fire.", 330, 20, 16)
status.color, status.z = "#d1d5db", 4

-- Cache the Strife API function once; repeated UI.Frame lookups from Lua can
-- otherwise resolve to a Widget proxy instead of the constructor.
local createFrame = UI.Frame
local createImage = UI.Image
local function frame(x, y, w, h, color, z)
  local widget = createFrame(x, y, w, h)
  widget.bg, widget.z, widget.rounding = color, z, 0
  return widget
end

local function gridText(value, x, y)
  local widget = UI.Text(value, x, y, 11)
  widget.color, widget.z = "#8b98a9", -2
  return widget
end

-- Grid and axes stay inside BombBox and draw behind every builder widget.
local boxRight = bombBox.x + bombBox.w
local boxBottom = bombBox.y + bombBox.h
for n = math.ceil((bombBox.x - launchX) / 25), math.floor((boxRight - 1 - launchX) / 25) do
  local x = launchX + n * 25
  local major = n % 2 == 0
  frame(x, bombBox.y, 1, bombBox.h, major and "#414d5e" or "#2b3441", -3)
end
for n = math.ceil((launchY - boxBottom) / 25), math.floor((launchY - bombBox.y) / 25) do
  local y = launchY - n * 25
  local major = n % 2 == 0
  frame(bombBox.x, y, bombBox.w, 1, major and "#414d5e" or "#2b3441", -3)
end
frame(launchX, bombBox.y, 2, bombBox.h, "#a4afbe", -2.5)
frame(bombBox.x, launchY, bombBox.w, 2, "#a4afbe", -2.5)
for n = 1, math.floor((targetPlane - launchX) / graphScale) do
  gridText(tostring(n), launchX + n * graphScale - 3, boxBottom - 15)
end
for n = math.ceil((launchY - boxBottom) / graphScale),
         math.floor((launchY - bombBox.y) / graphScale) do
  if n ~= 0 then
    gridText(tostring(n), launchX + 5, launchY - n * graphScale + 3)
  end
end
gridText("x", boxRight - 14, boxBottom - 15)
gridText("y", launchX + 5, bombBox.y + 3)

-- Bombs replace the old square obstacle field. They remain regular widgets,
-- so the existing projectile collision and random-row logic still apply.
local topRowObstacles, midRowObstacles, bottomRowObstacles = {}, {}, {}
local allObstacles = {topRowObstacles, midRowObstacles, bottomRowObstacles}
local bbWidth = bombBox.w - 140
local bombHitboxInset = 10
local explosionFrameCount = 24
local explosionFrameSeconds = 0.045
local function makeRow(row, y)
  for i = 1, math.floor(bbWidth / 130) do
    local obstacle = createImage("bomb.png", 50 + math.floor(bbWidth / 4) * i, y, 0.14)
    obstacle.z = -1
    table.insert(row, obstacle)
  end
end
makeRow(topRowObstacles, 110)
makeRow(midRowObstacles, 220)
makeRow(bottomRowObstacles, 330)

-- The launcher is the graph origin, so place the wirecutter directly there.
local wirecutter = createImage("Wirecutter.png", launchX - 25, launchY - 29, 0.20)
wirecutter.z = 2.5

-- A small, safe expression parser: no Lua code is executed from the input.
-- Supported: x, pi, e; + - * / % ^; parentheses and implicit multiplication;
-- sin, cos, tan, asin, acos, atan, atan2, sqrt, abs, exp, ln, log, log10,
-- floor, ceil, min, and max.
local function compileFunction(source)
  source = source:match("^%s*(.-)%s*$")
  source = source:gsub("^[yY]%s*=%s*", "")
  source = source:gsub("^[fF]%s*%(%s*[xX]%s*%)%s*=%s*", "")

  local tokens, pos = {}, 1
  while pos <= #source do
    local rest = source:sub(pos)
    if rest:match("^%s") then
      pos = pos + 1
    else
      local number = rest:match("^%d+%.?%d*") or rest:match("^%.%d+")
      if number then
        local exponent = rest:sub(#number + 1):match("^[eE][%+%-]?%d+")
        if exponent then number = number .. exponent end
        local value = tonumber(number)
        if not value then error("Invalid number: " .. number) end
        table.insert(tokens, value)
        pos = pos + #number
      else
        local name = rest:match("^[%a_][%w_]*")
        if name then
          table.insert(tokens, name:lower())
          pos = pos + #name
        else
          local symbol = rest:sub(1, 1)
          if not symbol:match("[%+%-%*/%^%%%(%)%,]") then
            error("Unexpected character: " .. symbol)
          end
          table.insert(tokens, symbol)
          pos = pos + 1
        end
      end
    end
  end

  if #tokens == 0 then error("Type a function first.") end
  local index = 1
  local function peek() return tokens[index] end
  local function take(expected)
    local token = peek()
    if expected and token ~= expected then
      error("Expected '" .. expected .. "'.")
    end
    index = index + 1
    return token
  end
  local parseSum, parseProduct, parseUnary, parsePower, parsePrimary

  local functions = {
    sin = {math.sin, 1, 1}, cos = {math.cos, 1, 1},
    tan = {math.tan, 1, 1}, asin = {math.asin, 1, 1},
    acos = {math.acos, 1, 1}, atan = {math.atan, 1, 1},
    atan2 = {function(y, x) return math.atan(y, x) end, 2, 2},
    sqrt = {math.sqrt, 1, 1}, abs = {math.abs, 1, 1},
    exp = {math.exp, 1, 1}, ln = {math.log, 1, 1},
    log = {math.log, 1, 1},
    log10 = {function(x) return math.log(x) / math.log(10) end, 1, 1},
    floor = {math.floor, 1, 1}, ceil = {math.ceil, 1, 1},
    min = {math.min, 1, math.huge}, max = {math.max, 1, math.huge},
  }

  parsePrimary = function()
    local token = peek()
    if type(token) == "number" then
      take()
      return function() return token end
    end
    if token == "(" then
      take("(")
      local value = parseSum()
      take(")")
      return value
    end
    if type(token) == "string" then
      local name = take()
      if name == "x" then return function(x) return x end end
      if name == "pi" then return function() return math.pi end end
      if name == "e" then return function() return math.exp(1) end end
      local spec = functions[name]
      if not spec then error("Unknown variable or function: " .. name) end
      take("(")
      local args = {parseSum()}
      while peek() == "," do
        take(",")
        table.insert(args, parseSum())
      end
      take(")")
      if #args < spec[2] or #args > spec[3] then
        error("Wrong number of arguments for " .. name .. ".")
      end
      return function(x)
        local values = {}
        for i, arg in ipairs(args) do values[i] = arg(x) end
        return spec[1](table.unpack(values))
      end
    end
    error("Expected a number, x, function, or parenthesized expression.")
  end

  parsePower = function()
    local base = parsePrimary()
    if peek() == "^" then
      take("^")
      local exponent = parseUnary()
      return function(x) return base(x) ^ exponent(x) end
    end
    return base
  end
  parseUnary = function()
    if peek() == "+" then take("+"); return parseUnary() end
    if peek() == "-" then
      take("-")
      local value = parseUnary()
      return function(x) return -value(x) end
    end
    return parsePower()
  end
  parseProduct = function()
    local left = parseUnary()
    while true do
      local token = peek()
      if token == "*" or token == "/" or token == "%" then
        take()
        local right = parseUnary()
        local op = token
        local previous = left
        if op == "*" then
          left = function(x) return previous(x) * right(x) end
        elseif op == "/" then
          left = function(x) return previous(x) / right(x) end
        else
          left = function(x) return previous(x) % right(x) end
        end
      elseif type(token) == "number" or token == "("
          or (type(token) == "string" and token:match("^[%a_]")) then
        local right = parseUnary()
        local previous = left
        left = function(x) return previous(x) * right(x) end
      else
        break
      end
    end
    return left
  end
  parseSum = function()
    local left = parseProduct()
    while peek() == "+" or peek() == "-" do
      local op = take()
      local right = parseProduct()
      local previous = left
      if op == "+" then
        left = function(x) return previous(x) + right(x) end
      else
        left = function(x) return previous(x) - right(x) end
      end
    end
    return left
  end

  local result = parseSum()
  if peek() ~= nil then error("Unexpected token: " .. tostring(peek())) end
  return result
end

local function finiteNumber(value)
  return type(value) == "number" and value == value
      and value ~= math.huge and value ~= -math.huge
end

local function clearTrail()
  for _, dot in ipairs(trail) do UI.Destroy(dot) end
  trail = {}
  lastTrailX, lastTrailY = launchX, launchY
end

local function stopShot()
  shot.active = false
  shot.fn = nil
end

local projectile = frame(launchX - projectileRadius, launchY - projectileRadius,
                         projectileRadius * 2, projectileRadius * 2, "#ffe066", 2)
projectile.rounding = 1
projectile.visible = false

local function touchedSummary()
  local names = {}
  for _, color in ipairs(colors) do
    if touched[color] then table.insert(names, color) end
  end
  return #names > 0 and table.concat(names, ", ") or "none"
end

local function updateProgress()
  status.text = "Buttons " .. touchedCount .. "/4: " .. touchedSummary()
end

local glowOffsetY = {red = -2, yellow = -2, blue = -3, green = -2}
local function shuffleTargets()
  local slots = {118, 196, 276, 355}
  for i = #slots, 2, -1 do
    local j = math.random(i)
    slots[i], slots[j] = slots[j], slots[i]
  end
  for i, color in ipairs(colors) do
    targets[color].y = slots[i]
    glows[color].y = slots[i] + glowOffsetY[color]
  end
end

local function resetTargets()
  touched, touchedCount, won = {}, 0, false
  for _, color in ipairs(colors) do
    targets[color].alpha = 1
    glows[color].alpha = 0.45
  end
  shuffleTargets()
  updateProgress()
end

-- Add your own bomb-specific rules here. The hit itself and all-four win
-- condition are handled by this script; you can extend the callbacks freely.
function on_bomb_button_touched(color, xValue, yValue, progress)
  -- TODO: optional sound, clue, or state change after a colored button is hit.
end

function on_bomb_obstacle_hit(xValue, yValue)
  -- TODO: optional feedback. The five-second penalty is already applied.
end

function on_bomb_timer_expired()
  -- TODO: optional failure screen or restart rule.
end

local function expireTimer()
  if expired or won then return end
  expired = true
  timer = 0
  title.text = "Timer: 0"
  redTitle.text = title.text
  redTitle.alpha = 0
  stopShot()
  projectile.visible = false
  status.text = "Time is up."
  on_bomb_timer_expired()
end

local function setTimerFromElapsed()
  timer = math.max(0, duration - math.floor(elapsed))
  title.text = "Timer: " .. timer
  redTitle.text = title.text
  if timer == 0 then expireTimer() end
end

local function fire()
  if won then
    status.text = "All four buttons are touched."
    return
  end
  if timer <= 0 then
    status.text = "Time is up."
    return
  end
  if shot.active then
    status.text = "Wait for this shot to finish."
    return
  end

  local ok, compiled = pcall(compileFunction, functionInput.text)
  if not ok then
    status.text = "Function error: " .. tostring(compiled)
    return
  end
  local okStart, startY = pcall(compiled, 0)
  if not okStart or not finiteNumber(startY) or math.abs(startY) > 0.000001 then
    status.text = "Use a function through the launcher: f(0) must equal 0."
    return
  end

  clearTrail()
  shot.fn, shot.active, shot.x, shot.y = compiled, true, launchX, launchY
  projectile.x, projectile.y, projectile.visible = launchX - projectileRadius,
                                                    launchY - projectileRadius, true
  status.text = "Firing: " .. functionInput.text
end

local function targetAt(x, y)
  for _, color in ipairs(colors) do
    local target = targets[color]
    if x + projectileRadius >= target.x and x - projectileRadius <= target.x + target.w
        and y + projectileRadius >= target.y and y - projectileRadius <= target.y + target.h then
      return color
    end
  end
  return nil
end

local function obstacleAt(x, y)
  for _, row in ipairs(allObstacles) do
    for _, obstacle in ipairs(row) do
      if obstacle.visible and obstacle.alpha > 0.5
          and x + projectileRadius > obstacle.x + bombHitboxInset
          and x - projectileRadius < obstacle.x + obstacle.w - bombHitboxInset
          and y + projectileRadius > obstacle.y + bombHitboxInset
          and y - projectileRadius < obstacle.y + obstacle.h - bombHitboxInset then
        return obstacle
      end
    end
  end
  return nil
end

local function explodeBomb(bomb)
  -- A bomb disappears as the explosion sprite takes its place. Restart brings
  -- all randomized bombs back for the next round.
  bomb.visible = false
  local frames = {}
  for i = 0, explosionFrameCount - 1 do
    local name = string.format("explosion_frame_%02d.png", i)
    local frame = createImage(name, bomb.x + 3, bomb.y - 6, 0.35)
    frame.z, frame.visible = 3, i == 0
    table.insert(frames, frame)
  end

  local current = 1
  local function showNextFrame()
    frames[current].visible = false
    current = current + 1
    if current <= #frames then
      frames[current].visible = true
      After(explosionFrameSeconds, showNextFrame)
    else
      for _, frame in ipairs(frames) do UI.Destroy(frame) end
    end
  end
  After(explosionFrameSeconds, showNextFrame)
end

local function addTrailPoint(x, y)
  local dx, dy = x - lastTrailX, y - lastTrailY
  if dx * dx + dy * dy < 16 or #trail >= 350 then return end
  local point = frame(x - 2, y - 2, 5, 5, "#4ade80", -0.5)
  table.insert(trail, point)
  lastTrailX, lastTrailY = x, y
end

local function registerTarget(color, x, y)
  stopShot()
  projectile.visible = false
  if not touched[color] then
    touched[color] = true
    touchedCount = touchedCount + 1
    targets[color].alpha = 0.45
    glows[color].alpha = 0.12
  end
  on_bomb_button_touched(color, (x - launchX) / graphScale,
                         (launchY - y) / graphScale, touchedCount)
  if touchedCount == 4 then
    won = true
    updateProgress()
    status.text = "All four buttons touched — defused!"
    return
  end
  shuffleTargets() -- Move the colored targets to a newly randomized row order.
  updateProgress()
end

local function moveProjectile(dt)
  local remaining = shotSpeed * dt
  while remaining > 0 and shot.active do
    local step = math.min(1, remaining, targetPlane - shot.x)
    if step <= 0 then
      stopShot()
      projectile.visible = false
      return
    end
    remaining = remaining - step
    local x = shot.x + step
    local xValue = (x - launchX) / graphScale
    local ok, yValue = pcall(shot.fn, xValue)
    if not ok or not finiteNumber(yValue) or math.abs(yValue) > 100 then
      stopShot()
      projectile.visible = false
      status.text = "Function is undefined or out of range here."
      return
    end
    local y = launchY - yValue * graphScale
    if y - projectileRadius < bombBox.y or y + projectileRadius > boxBottom then
      stopShot()
      projectile.visible = false
      status.text = "The function left the arena."
      return
    end
    local bomb = obstacleAt(x, y)
    if bomb then
      stopShot()
      projectile.visible = false
      explodeBomb(bomb)
      elapsed = math.min(duration, elapsed + 5)
      setTimerFromElapsed()
      if timer > 0 then status.text = "Obstacle hit: 5 seconds lost. Try another function." end
      on_bomb_obstacle_hit(xValue, yValue)
      return
    end
    local color = targetAt(x, y)
    shot.x, shot.y = x, y
    projectile.x, projectile.y = x - projectileRadius, y - projectileRadius
    addTrailPoint(x, y)
    if color then
      registerTarget(color, x, y)
      return
    end
    if x >= targetPlane then
      stopShot()
      projectile.visible = false
      status.text = "Missed the targets. Try another function."
    end
  end
end

local function shuffleObstacles()
  for _, row in ipairs(allObstacles) do
    for _, obstacle in ipairs(row) do
      obstacle.visible, obstacle.alpha = true, 0
      After(0.5, function()
        if math.random(1, 3) == 3 then obstacle.alpha = 1 end
      end)
    end
  end
end
shuffleTargets()
shuffleObstacles()

local function blink()
  if Page.Current() == "GameBD" and timer > 0 then
    local nextAlpha = redTitle.alpha < 0.5 and 1 or 0
    Tween(redTitle, "alpha", nextAlpha, 0.25, "inout")
  else
    redTitle.alpha = 0
  end
  After(1, blink)
end
After(1, blink)

local function restartRound()
  clearTrail()
  stopShot()
  projectile.visible = false
  elapsed, timer, expired, won = 0, duration, false, false
  title.text, redTitle.text = "Timer: " .. duration, "Timer: " .. duration
  redTitle.alpha = 0
  resetTargets()
  shuffleObstacles()
  status.text = "Enter a function through (0, 0), then fire."
end

local function clearShot()
  clearTrail()
  stopShot()
  projectile.visible = false
  status.text = won and "All four buttons are touched." or "Trail cleared."
end

local function backToModes()
  clearTrail()
  stopShot()
  Page.Open("Menu")
end

local function markButton(button, background)
  button.z, button.bg, button.color = 6, background, "#ffffff"
end

local function makeButton(label, x, w, callback, background)
  local button = UI.Button(label, x, 464, w, 38)
  markButton(button, background or "#495057")
  button.on_click = callback
  return button
end

local yLabel = UI.Text("f(x) =", 14, 470, 20)
yLabel.color, yLabel.z = "#ffffff", 6
functionInput = UI.Input("e.g. x^2/25, sin(x), or 0.5*x", 76, 464, 350, 38)
functionInput.z = 6
local fireButton = makeButton("Fire", 438, 82, fire, "#2f9e44")
local clearButton = makeButton("Clear", 530, 82, clearShot, "#868e96")
local restartButton = makeButton("Restart", 622, 90, restartRound, "#1971c2")
local backButton = makeButton("Back", 820, 110, backToModes, "#495057")
functionInput.on_submit = function() fire() end

function on_update(dt)
  if Page.Current() ~= "GameBD" then return end
  if not won and timer > 0 then
    elapsed = math.min(duration, elapsed + dt)
    setTimerFromElapsed()
  end
  if shot.active and timer > 0 then moveProjectile(dt) end
end

Page.Open("Menu")
